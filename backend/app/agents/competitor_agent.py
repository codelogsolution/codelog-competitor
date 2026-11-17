from collections.abc import Callable

from sqlalchemy.orm import Session

from app.workflows.competitor_workflow import build_competitor_workflow


class CompetitorAgent:

    def __init__(self):
        self.workflow = build_competitor_workflow()

    async def run(
        self,
        records: list[dict],
        db: Session,
        run_id: str | None = None,
        progress_callback: Callable[[dict], None] | None = None,
    ) -> dict:

        initial_state = {
            "records": records,
            "db": db,
            "run_id": run_id,
            "scoring_results": [],
            "research_results": [],
            "evidence_results": [],
            "battlecard_results": [],
            "errors": [],
            "status": "started",
            "progress_callback": progress_callback,
        }

        return await self.workflow.ainvoke(initial_state)
