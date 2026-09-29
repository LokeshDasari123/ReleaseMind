import csv
import hashlib
import io
import json
import re
from typing import Any
from urllib.parse import urlparse

from app.models import HistoricalExperience


def _pick(record: dict[str, Any], *keys: str) -> Any:
    normalized = {re.sub(r"[^a-z0-9]", "", str(key).lower()): value for key, value in record.items()}
    for key in keys:
        value = normalized.get(re.sub(r"[^a-z0-9]", "", key.lower()))
        if value not in (None, "", [], {}):
            return value
    return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        parts = [_text(item) for item in value]
        return "; ".join(part for part in parts if part) or None
    if isinstance(value, dict):
        return _text(value.get("text") or value.get("value") or value.get("name"))
    return None


def _truth(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "synthetic"}
    return value is True or value == 1


def _records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("incidents", "records", "data", "reports", "items", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return [payload]


def parse_dataset(filename: str, raw: bytes) -> tuple[list[HistoricalExperience], int]:
    name = filename.lower()
    if name.endswith(".json"):
        payload = json.loads(raw.decode("utf-8-sig"))
        rows = _records(payload)
    elif name.endswith(".csv"):
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    else:
        raise ValueError("Upload a JSON or CSV export of incident records.")

    experiences: list[HistoricalExperience] = []
    skipped = 0
    for index, row in enumerate(rows, start=1):
        nested = row.get("incident") if isinstance(row.get("incident"), dict) else {}
        record = {**nested, **row}
        title = _text(_pick(record, "title", "incident_title", "name", "headline"))
        description = _text(_pick(record, "description", "narrative", "report", "summary", "content", "text", "body"))
        source_url = _text(_pick(record, "source_url", "url", "link", "report_url", "uri"))
        if not title or not description or not source_url:
            skipped += 1
            continue
        parsed_url = urlparse(source_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            skipped += 1
            continue
        source = _text(_pick(record, "source", "organization", "company", "publisher", "vendor")) or parsed_url.netloc
        raw_id = _text(_pick(record, "id", "incident_id", "uuid", "slug"))
        record_id = raw_id or hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:16]
        services = _pick(record, "services_affected", "affected_services", "services", "components", "component")
        if isinstance(services, str):
            services = [part.strip() for part in re.split(r"[,;|]", services) if part.strip()]
        elif not isinstance(services, list):
            services = [str(services)] if services else []
        try:
            experiences.append(HistoricalExperience(
                id=str(record_id),
                title=title,
                description=description,
                category=_text(_pick(record, "category", "type", "incident_type")) or "incident",
                source=source,
                source_url=source_url,
                triggering_change=_text(_pick(record, "triggering_change", "change_trigger", "reported_change")),
                root_cause=_text(_pick(record, "root_cause", "cause")),
                remediation=_text(_pick(record, "remediation", "mitigation", "resolution", "fix", "corrective_actions", "actions_taken")),
                severity=_text(_pick(record, "severity", "impact_level")),
                date=_text(_pick(record, "date", "incident_date", "started_at", "published_at", "timestamp")),
                services_affected=[str(item) for item in services],
                is_synthetic=_truth(_pick(record, "is_synthetic", "synthetic")),
            ))
        except Exception:
            skipped += 1
    return experiences, skipped
