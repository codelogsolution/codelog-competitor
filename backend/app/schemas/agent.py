from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    records: list[dict] = Field(min_length=1)


class AgentRunResponse(BaseModel):
    status: str
    scoring_results: list[dict]
    research_results: list[dict]
    evidence_results: list[dict]
    battlecard_results: list[dict]
    errors: list[str] = Field(default_factory=list)