from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceCreate(BaseModel):
    competitor_name: str = Field(min_length=1, max_length=255)
    domain: str = Field(min_length=1, max_length=255)
    source_type: str = Field(min_length=1, max_length=100)
    source_url: str = ""
    category: str = Field(min_length=1, max_length=150)
    signal_type: str = Field(min_length=1, max_length=100)
    signal_text: str = Field(min_length=1)
    signal_date: str
    sentiment: str = "unknown"
    frequency: int = Field(default=0, ge=0)
    keyword_gap: str = ""
    keyword_volume: float | None = Field(default=None, ge=0)
    ranking_gap: float | None = Field(default=None, ge=0)
    product_area: str = ""
    status: str = "valid"


class EvidenceResponse(EvidenceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class EvidenceIngestRequest(BaseModel):
    records: list[EvidenceCreate] = Field(min_length=1, max_length=1000)


class EvidenceIngestResponse(BaseModel):
    success: bool
    received_count: int
    inserted_count: int
    duplicate_count: int
    results: list[EvidenceResponse]


class EvidenceSummary(BaseModel):
    competitor_name: str
    domain: str
    total_evidence: int
    evidence_by_type: dict[str, int]
    evidence_by_category: dict[str, int]
    sources: list[str]


class EvidenceResolutionRequest(BaseModel):
    decision: Literal["confirm_valid", "mark_invalid"]
    actor: str = Field(default="workspace_reviewer", min_length=1, max_length=255)
    comment: str = Field(default="", max_length=2000)
    source_url: str | None = Field(default=None, max_length=2000)
