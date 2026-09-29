from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class ChangeRequest(BaseModel):
    change_description: str = Field(min_length=8, max_length=12000)
    context: str | None = Field(default=None, max_length=4000)


class HistoricalExperience(BaseModel):
    id: str
    title: str
    description: str
    category: str = "incident"
    source: str
    source_url: str
    triggering_change: str | None = None
    root_cause: str | None = None
    remediation: str | None = None
    severity: str | None = None
    date: str | None = None
    services_affected: list[str] = Field(default_factory=list)
    retrieval_score: float | None = None
    is_synthetic: bool = False


class RiskAssessment(BaseModel):
    risk_level: str
    risk_score: int
    summary: str
    key_risks: list[str]
    recommended_safeguards: list[str]
    evidence_citations: list[str] = Field(default_factory=list)
    model_reasoning: str
    confidence_notes: str


class AssessmentResponse(BaseModel):
    baseline_assessment: RiskAssessment
    memory_assessment: RiskAssessment
    retrieved_experiences: list[HistoricalExperience]
    metadata: dict[str, Any]


class IngestResponse(BaseModel):
    imported: int
    skipped: int
    memory_provider: str
    message: str
