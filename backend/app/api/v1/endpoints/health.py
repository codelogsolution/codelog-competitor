from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {
        "success": True,
        "application": "KOMP Competitor Intelligence Agent",
        "status": "healthy",
        "message": "Backend is running successfully",
    }