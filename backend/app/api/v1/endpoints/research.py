
from fastapi import APIRouter, HTTPException

from app.schemas.research import ResearchRequest, ResearchResponse
from app.services.research_service import ResearchService

router = APIRouter()


@router.post("/run", response_model=ResearchResponse)
async def run_competitor_research(payload: ResearchRequest):
    try:
        return await ResearchService.research_competitors(
            competitors=payload.competitors,
            max_competitors=payload.max_competitors,
            max_results_per_competitor=payload.max_results_per_competitor,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Competitor research failed: {str(exc)}",
        ) from exc
