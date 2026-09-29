import json
from typing import Any

from openai import AsyncOpenAI

from app.config import settings
from app.models import HistoricalExperience, RiskAssessment


class LLMConfigurationError(RuntimeError):
    pass


def _client() -> AsyncOpenAI:
    if not settings.llm_api_key:
        raise LLMConfigurationError("Set OPENAI_API_KEY (or LLM_API_KEY for another OpenAI-compatible provider) in backend/.env to enable assessments.")
    options = {"api_key": settings.llm_api_key}
    if settings.llm_base_url:
        options["base_url"] = settings.llm_base_url
    return AsyncOpenAI(**options)


SYSTEM_PROMPT = """You are ReleaseMind, a cautious software-change reviewer. Assess a proposed change before release. You do not predict production incidents and must not imply causal certainty from public reports. Distinguish historical report facts from your inference. Recommend specific safeguards that fit this change. Risk score is a 0-100 ordinal judgment, not a probability. Return valid JSON with: risk_level (LOW|MEDIUM|HIGH|CRITICAL), risk_score (integer), summary, key_risks (string array), recommended_safeguards (string array), evidence_citations (array of IDs), model_reasoning, confidence_notes. Never invent historical facts, events, organizations, metrics, causes, or remediations. In the baseline condition, evidence_citations must be empty. In the memory condition, cite only supplied evidence IDs and cite only when the item substantively supports the point. If no evidence is relevant, say so and use general engineering reasoning without citations."""


def _evidence_block(experiences: list[HistoricalExperience]) -> str:
    if not experiences:
        return "No historical incident evidence was retrieved. Do not invent or imply any." 
    blocks = []
    for item in experiences:
        blocks.append("\n".join([
            f"Evidence ID: {item.id}",
            f"Title: {item.title}",
            f"Source: {item.source} ({item.source_url})",
            f"Date: {item.date or 'not available'}; severity: {item.severity or 'not available'}",
            f"Affected components: {', '.join(item.services_affected) or 'not specified'}",
            f"Report text: {item.description}",
            f"Reported triggering change: {item.triggering_change or 'not stated in the imported record'}",
            f"Reported cause: {item.root_cause or 'not stated in the imported record'}",
            f"Reported remediation: {item.remediation or 'not stated in the imported record'}",
        ]))
    return "\n\n---\n\n".join(blocks)


async def _assess(
    change_description: str,
    context: str | None,
    evidence: list[HistoricalExperience] | None,
) -> RiskAssessment:
    client = _client()
    user_parts = [f"Proposed software change:\n{change_description}"]
    if context:
        user_parts.append(f"Additional change context:\n{context}")
    if evidence is not None:
        user_parts.append(f"Retrieved historical incident evidence (treat as reports, not proof of causation for this proposed change):\n{_evidence_block(evidence)}")
    else:
        user_parts.append("Condition: baseline LLM-only. No memory or incident evidence is provided.")
    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "\n\n".join(user_parts)},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("The model returned an empty assessment.")
        payload: dict[str, Any] = json.loads(content)
    except Exception as exc:
        raise RuntimeError(f"LLM assessment failed: {exc.__class__.__name__}. Check the configured provider key, endpoint, model access, and network connectivity.") from exc

    allowed_ids = {item.id for item in evidence or []}
    payload["evidence_citations"] = [
        str(item) for item in payload.get("evidence_citations", []) if str(item) in allowed_ids
    ] if evidence is not None else []
    try:
        result = RiskAssessment.model_validate(payload)
    except Exception as exc:
        raise RuntimeError("The model response did not match the required assessment schema.") from exc
    return result


async def assess_conditions(
    change_description: str,
    context: str | None,
    experiences: list[HistoricalExperience],
) -> tuple[RiskAssessment, RiskAssessment]:
    import asyncio

    baseline, augmented = await asyncio.gather(
        _assess(change_description, context, None),
        _assess(change_description, context, experiences),
    )
    return baseline, augmented
