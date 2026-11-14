from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.competitor_agent import CompetitorAgent
from app.database.session import get_db
from app.schemas.agent import AgentRunRequest, AgentRunResponse

router = APIRouter()


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    payload: AgentRunRequest,
    db: Session = Depends(get_db),
):
    try:
        result = await CompetitorAgent().run(
            records=payload.records,
            db=db,
        )

        return {
            "status": result.get("status", "completed"),
            "scoring_results": result.get("scoring_results", []),
            "research_results": result.get("research_results", []),
            "evidence_results": result.get("evidence_results", []),
            "battlecard_results": result.get("battlecard_results", []),
            "errors": result.get("errors", []),
        }

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Competitor workflow execution failed.",
        ) from exc