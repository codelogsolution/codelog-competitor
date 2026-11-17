import logging


from fastapi import APIRouter, HTTPException

from app.schemas.research import ResearchRequest, ResearchResponse
from app.services.research_service import ResearchService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/run", response_model=ResearchResponse)
async def run_competitor_research(payload: ResearchRequest):
    try:
        return await ResearchService.research_competitors(
            competitors=payload.competitors,
            max_competitors=payload.max_competitors,
            max_results_per_competitor=payload.max_results_per_competitor,
        )
    except Exception as exc:
        logger.exception("Competitor research endpoint failed")
        raise HTTPException(
            status_code=500,
            detail="Competitor research failed. Check application logs for details.",
        ) from exc
