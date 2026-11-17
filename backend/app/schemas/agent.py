from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    records: list[dict] = Field(min_length=1, max_length=10000)
    import_id: str | None = None
    source_name: str = ""


class AgentRunResponse(BaseModel):
    run_id: str | None = None
    status: str
    scoring_results: list[dict]
    research_results: list[dict]
    evidence_results: list[dict]
    battlecard_results: list[dict]
    errors: list[str] = Field(default_factory=list)


class AgentRunHistoryResponse(BaseModel):
    run_id: str
    import_id: str | None = None
    source_name: str = ""
    status: str
    uploaded_count: int
    valid_count: int
    warning_count: int
    invalid_count: int
    scoring_results: list[dict]
    research_targets: list[dict]
    research_results: list[dict]
    source_urls: list[str]
    battlecard_ids: list[int]
    errors: list[str]
    created_at: str
    completed_at: str | None = None
