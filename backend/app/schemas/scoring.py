
from pydantic import BaseModel, Field
from typing import Any


class ScoreRequest(BaseModel):
    records: list[dict[str, Any]] = Field(
        ..., min_length=1, description="Normalized competitor evidence records"
    )


class ScoreBreakdown(BaseModel):
    review_pain: int
    seo_gap: int
    product_overlap: int
    recency: int


class CompetitorScore(BaseModel):
    competitor_name: str
    domain: str
    preliminary_score: int
    max_score: int = 95
    priority: str
    breakdown: ScoreBreakdown
    reasons: list[str]
    missing_data: list[str]
    evidence_count: int


class ScoreResponse(BaseModel):
    success: bool
    total_competitors: int
    results: list[CompetitorScore]
