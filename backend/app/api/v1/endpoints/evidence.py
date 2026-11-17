import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.evidence import (
    EvidenceIngestRequest,
    EvidenceIngestResponse,
    EvidenceResponse,
    EvidenceSummary,
    EvidenceResolutionRequest,
    EvidenceCreate,
)
from app.repositories.evidence_repository import EvidenceRepository
from app.services.evidence_service import EvidenceService
from app.services.validation_service import ValidationService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ingest", response_model=EvidenceIngestResponse)
def ingest_evidence(
    payload: EvidenceIngestRequest,
    db: Session = Depends(get_db),
):
    try:
        validation = ValidationService.validate_records(
            [record.model_dump(mode="json") for record in payload.records]
        )
        eligible_records = [
            EvidenceCreate.model_validate({
                **record,
                "source_url": record.get("source_url") or "",
                "signal_date": record.get("signal_date") or "unknown",
                "sentiment": record.get("sentiment") or "unknown",
                "frequency": record.get("frequency") or 0,
                "keyword_gap": record.get("keyword_gap") or "",
                "product_area": record.get("product_area") or "",
                "status": record.get("validation_status", "invalid"),
            })
            for record in validation["records"]
            if record.get("validation_status") in {"valid", "warning"}
        ]
        if not eligible_records:
            raise ValueError("No valid or reviewable evidence records were supplied.")
        return EvidenceService.ingest(db, eligible_records)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Evidence ingestion failed")
        raise HTTPException(
            status_code=500,
            detail="Evidence ingestion failed. Check application logs for details.",
        ) from exc


@router.get("/", response_model=list[EvidenceResponse])
def list_evidence(
    domain: str | None = None,
    run_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return EvidenceService.list_evidence(db, domain, limit, run_id)


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


@router.post("/{evidence_id}/resolve", response_model=EvidenceResponse)
def resolve_warning_evidence(
    evidence_id: int,
    payload: EvidenceResolutionRequest,
    db: Session = Depends(get_db),
):
    try:
        return EvidenceService.resolve_warning(
            db=db,
            evidence_id=evidence_id,
            decision=payload.decision,
            actor=payload.actor,
            comment=payload.comment,
            source_url=payload.source_url,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# Register the static domain route before the parameterized evidence ID route.
@router.delete("/domain/{domain}")
def delete_evidence_by_domain(
    domain: str,
    db: Session = Depends(get_db),
):
    count = EvidenceRepository.delete_by_domain(db, domain)
    return {
        "success": True,
        "message": f"Deleted {count} evidence record(s) for {domain}.",
        "deleted_count": count,
    }


@router.delete("/{evidence_id}")
def delete_evidence(
    evidence_id: int,
    db: Session = Depends(get_db),
):
    deleted = EvidenceRepository.delete_by_id(db, evidence_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Evidence not found.")
    return {"success": True, "message": "Evidence deleted."}
