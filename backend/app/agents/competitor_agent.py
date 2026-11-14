from sqlalchemy.orm import Session

from app.workflows.competitor_workflow import build_competitor_workflow


class CompetitorAgent:

    def __init__(self):
        self.workflow = build_competitor_workflow()

    async def run(
        self,
        records: list[dict],
        db: Session,
    ) -> dict:

        initial_state = {
            "records": records,
            "db": db,
            "scoring_results": [],
            "research_results": [],
            "evidence_results": [],
            "battlecard_results": [],
            "errors": [],
            "status": "started",
        }

        return await self.workflow.ainvoke(initial_state)