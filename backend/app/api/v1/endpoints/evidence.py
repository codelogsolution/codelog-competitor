from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.evidence import (
    EvidenceIngestRequest,
    EvidenceIngestResponse,
    EvidenceResponse,
    EvidenceSummary,
)
from app.services.evidence_service import EvidenceService

router = APIRouter()


@router.post("/ingest", response_model=EvidenceIngestResponse)
def ingest_evidence(
    payload: EvidenceIngestRequest,
    db: Session = Depends(get_db),
):
    try:
        return EvidenceService.ingest(db, payload.records)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Evidence ingestion failed: {str(exc)}",
        ) from exc


@router.get("/", response_model=list[EvidenceResponse])
def list_evidence(
    domain: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return EvidenceService.list_evidence(db, domain, limit)


@router.get("/summary/{domain}", response_model=EvidenceSummary)
def get_evidence_summary(
    domain: str,
    db: Session = Depends(get_db),
):
    result = EvidenceService.summary(db, domain)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No evidence found for this competitor.",
        )

    return result