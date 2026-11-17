from typing import TypedDict, Any, Callable
from sqlalchemy.orm import Session


class CompetitorAgentState(TypedDict, total=False):
    records: list[dict[str, Any]]
    db: Session
    run_id: str | None
    scoring_results: list[dict[str, Any]]
    research_results: list[dict[str, Any]]
    evidence_results: list[dict[str, Any]]
    battlecard_results: list[dict[str, Any]]
    errors: list[str]
    status: str
    progress_callback: Callable[[dict[str, Any]], None] | None
