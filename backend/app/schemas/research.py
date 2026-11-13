
from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    competitors: list[dict] = Field(
        ..., min_length=1,
        description="Competitor scoring results from Module 3"
    )
    max_competitors: int = Field(default=5, ge=1, le=5)
    max_results_per_competitor: int = Field(default=5, ge=1, le=5)


class ResearchSource(BaseModel):
    title: str
    url: str
    content: str = ""
    published_date: str | None = None
    score: float | None = None


class CompetitorResearch(BaseModel):
    competitor_name: str
    domain: str
    preliminary_score: int
    status: str
    query: str
    sources: list[ResearchSource] = Field(default_factory=list)
    message: str = ""


class ResearchResponse(BaseModel):
    success: bool
    researched_count: int
    skipped_count: int
    results: list[CompetitorResearch]
