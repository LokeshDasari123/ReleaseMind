import json
import math
import re
import sqlite3
from abc import ABC, abstractmethod
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from app.config import settings
from app.models import HistoricalExperience

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_+.#-]*", re.IGNORECASE)
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "into",
    "is", "it", "of", "on", "or", "that", "the", "this", "to", "with", "was", "were",
}


def tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text) if token.lower() not in STOP_WORDS]


class MemoryProvider(ABC):
    name: str

    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> list[HistoricalExperience]: ...

    @abstractmethod
    async def ingest(self, experiences: list[HistoricalExperience]) -> tuple[int, int]: ...

    @abstractmethod
    def stats(self) -> dict[str, Any]: ...


class HindsightUnavailable(RuntimeError):
    """Raised only when a configured Hindsight endpoint cannot be reached or is unhealthy."""


class SQLiteMemoryProvider(MemoryProvider):
    """Persistent local incident memory with BM25-style lexical ranking."""

    name = "local-bm25-sqlite"

    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    searchable_text TEXT NOT NULL,
                    token_count INTEGER NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path, timeout=15)
        conn.row_factory = sqlite3.Row
        return conn

    def get(self, experience_id: str) -> HistoricalExperience | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM incidents WHERE id = ?", (experience_id,)).fetchone()
        if row is None:
            return None
        return HistoricalExperience.model_validate_json(row["payload"])

    async def ingest(self, experiences: list[HistoricalExperience]) -> tuple[int, int]:
        imported = 0
        skipped = 0
        with self._connect() as conn:
            for experience in experiences:
                if experience.is_synthetic:
                    skipped += 1
                    continue
                searchable_text = " ".join(
                    value for value in [
                        experience.title, experience.description, experience.category,
                        experience.triggering_change or "", experience.root_cause or "", experience.remediation or "",
                        " ".join(experience.services_affected),
                    ] if value
                )
                payload = experience.model_copy(update={"retrieval_score": None}).model_dump_json()
                conn.execute(
                    """INSERT INTO incidents(id, payload, searchable_text, token_count, updated_at)
                       VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                       ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,
                           searchable_text=excluded.searchable_text, token_count=excluded.token_count,
                           updated_at=CURRENT_TIMESTAMP""",
                    (experience.id, payload, searchable_text, len(tokens(searchable_text))),
                )
                imported += 1
        return imported, skipped

    async def search(self, query: str, top_k: int = 5) -> list[HistoricalExperience]:
        query_terms = tokens(query)
        if not query_terms:
            return []
        with self._connect() as conn:
            rows = conn.execute("SELECT id, payload, searchable_text, token_count FROM incidents").fetchall()
        if not rows:
            return []

        documents = [(row, Counter(tokens(row["searchable_text"]))) for row in rows]
        doc_count = len(documents)
        average_length = sum(row["token_count"] for row, _ in documents) / max(doc_count, 1)
        document_frequency = Counter(term for term in set(query_terms) for _, counts in documents if counts[term])
        query_counts = Counter(query_terms)
        ranked: list[tuple[float, sqlite3.Row]] = []
        k1, b = 1.5, 0.75
        for row, counts in documents:
            length = row["token_count"]
            score = 0.0
            for term, query_frequency in query_counts.items():
                frequency = counts[term]
                if not frequency:
                    continue
                inverse_document_frequency = math.log(1 + (doc_count - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
                denominator = frequency + k1 * (1 - b + b * length / max(average_length, 1))
                term_score = inverse_document_frequency * frequency * (k1 + 1) / denominator
                score += term_score * min(query_frequency, 2)
            if score > 0:
                ranked.append((score, row))
        ranked.sort(key=lambda item: item[0], reverse=True)
        results = []
        for score, row in ranked[:top_k]:
            experience = HistoricalExperience.model_validate_json(row["payload"])
            results.append(experience.model_copy(update={"retrieval_score": round(score, 4)}))
        return results

    def stats(self) -> dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM incidents").fetchall()
        categories: Counter[str] = Counter()
        sources: Counter[str] = Counter()
        for row in rows:
            incident = json.loads(row["payload"])
            categories[incident.get("category") or "incident"] += 1
            sources[incident.get("source") or "Unknown source"] += 1
        return {
            "total_experiences": len(rows),
            "categories": dict(categories),
            "sources": dict(sources),
            "provider": self.name,
            "persistence": "SQLite",
        }


class HindsightMemoryProvider(MemoryProvider):
    """Hindsight recall backed by SQLite source records for auditable citations."""

    name = "hindsight"

    def __init__(self, local_store: SQLiteMemoryProvider):
        self.local_store = local_store
        self.base_url = settings.hindsight_base_url.rstrip("/")
        self.bank_id = settings.hindsight_bank_id
        self.headers = {"Authorization": f"Bearer {settings.hindsight_api_key}"} if settings.hindsight_api_key else {}

    async def ingest(self, experiences: list[HistoricalExperience]) -> tuple[int, int]:
        imported, skipped = await self.local_store.ingest(experiences)
        records = [item for item in experiences if not item.is_synthetic]
        if not records:
            return imported, skipped
        url = f"{self.base_url}/v1/default/banks/{quote(self.bank_id, safe='')}/memories"
        async with httpx.AsyncClient(timeout=45) as client:
            for offset in range(0, len(records), 20):
                batch = records[offset:offset + 20]
                items = []
                for item in batch:
                    content = "\n".join([
                        f"Historical incident: {item.title}", item.description,
                        f"Reported triggering change: {item.triggering_change or 'Not stated in source'}",
                        f"Reported root cause: {item.root_cause or 'Not stated in source'}",
                        f"Reported remediation: {item.remediation or 'Not stated in source'}",
                    ])
                    items.append({
                        "content": content,
                        "context": "public incident report",
                        "document_id": item.id,
                        "metadata": {
                            "experience_id": item.id,
                            "title": item.title,
                            "source_url": item.source_url,
                            "source": item.source,
                        },
                    })
                try:
                    response = await client.post(url, headers=self.headers, json={"items": items, "async": True})
                except httpx.TransportError as exc:
                    raise HindsightUnavailable("Hindsight is unreachable; records were saved locally.") from exc
                if response.status_code >= 500:
                    raise HindsightUnavailable("Hindsight is unhealthy; records were saved locally.")
                if response.is_error:
                    raise RuntimeError(f"Hindsight retain failed ({response.status_code}); check Hindsight URL, key, and bank configuration.")
        return imported, skipped

    async def search(self, query: str, top_k: int = 5) -> list[HistoricalExperience]:
        url = f"{self.base_url}/v1/default/banks/{quote(self.bank_id, safe='')}/memories/recall"
        try:
            async with httpx.AsyncClient(timeout=25) as client:
                response = await client.post(
                    url, headers=self.headers,
                    json={"query": query, "max_tokens": 3000, "budget": "mid", "types": ["experience", "world"]},
                )
        except httpx.TransportError as exc:
            raise HindsightUnavailable("Hindsight is unreachable.") from exc
        if response.status_code >= 500:
            raise HindsightUnavailable("Hindsight is unhealthy.")
        if response.is_error:
            raise RuntimeError(f"Hindsight recall failed ({response.status_code}); check service availability and API configuration.")
        payload = response.json()
        recalls = payload.get("results", [])
        experiences: list[HistoricalExperience] = []
        seen: set[str] = set()
        for recall in recalls:
            metadata = recall.get("metadata") or {}
            experience_id = metadata.get("experience_id") or recall.get("document_id") or recall.get("documentId")
            if not experience_id or experience_id in seen:
                continue
            experience = self.local_store.get(str(experience_id))
            if experience is None:
                continue
            seen.add(str(experience_id))
            # Hindsight supplies ranking; do not fabricate a numerical similarity score.
            experiences.append(experience)
            if len(experiences) >= top_k:
                break
        return experiences

    def stats(self) -> dict[str, Any]:
        stats = self.local_store.stats()
        stats["provider"] = self.name
        stats["persistence"] = "Hindsight + local SQLite source records"
        stats["bank_id"] = self.bank_id
        return stats


local_store = SQLiteMemoryProvider(settings.database_path)
if settings.retrieval_provider == "hindsight" and settings.hindsight_enabled:
    memory_provider: MemoryProvider = HindsightMemoryProvider(local_store)
else:
    memory_provider = local_store


def get_memory_provider() -> MemoryProvider:
    return memory_provider
