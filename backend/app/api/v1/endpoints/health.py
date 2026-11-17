from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="KOMP API is running but the database is unavailable.",
        ) from exc

    return {
        "success": True,
        "application": "KOMP Competitor Intelligence Agent",
        "status": "healthy",
        "message": "Backend and database are ready.",
    }
