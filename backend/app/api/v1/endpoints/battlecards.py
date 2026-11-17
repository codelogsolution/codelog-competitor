
import csv
import io
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.battlecard_repository import BattlecardRepository
from app.schemas.battlecard import (
    BattlecardContent,
    BattlecardGenerateRequest,
    BattlecardResponse,
)
from app.services.battlecard_service import BattlecardService

router = APIRouter()
logger = logging.getLogger(__name__)


def safe_csv_cell(value) -> str:
    """Escape spreadsheet formulas in user/model-controlled CSV values."""
    text = "" if value is None else str(value)
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


@router.get("/export/approved")
def export_approved_battlecards(
    db: Session = Depends(get_db),
):
    """Export approved battlecards only; this endpoint never publishes externally."""
    records = BattlecardRepository.list_all(db, "approved")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "competitor_name", "domain", "status", "content",
        "evidence_urls", "created_at",
    ])

    for item in records:
        writer.writerow([
            safe_csv_cell(item.competitor_name),
            safe_csv_cell(item.domain),
            safe_csv_cell(item.status),
            safe_csv_cell(item.content),
            safe_csv_cell(item.evidence_urls),
            safe_csv_cell(item.created_at.isoformat() if item.created_at else ""),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="komp-approved-battlecards.csv"'
        },
    )


@router.delete("/{battlecard_id}")
def delete_battlecard(
    battlecard_id: int,
    db: Session = Depends(get_db),
):
    deleted = BattlecardRepository.delete_by_id(db, battlecard_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Battlecard not found.")
    return {"success": True, "message": "Battlecard deleted."}


@router.post("/generate", response_model=BattlecardResponse)
def generate_battlecard(
    payload: BattlecardGenerateRequest,
    db: Session = Depends(get_db),
):
    try:
        return BattlecardService.generate(
            db,
            payload.competitor_name,
            payload.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Battlecard generation failed for domain=%s", payload.domain)
        raise HTTPException(
            status_code=500,
            detail="Battlecard generation failed. Check application logs for the run details.",
        ) from exc


@router.get("/", response_model=list[BattlecardResponse])
def list_battlecards(
    status: str | None = None,
    db: Session = Depends(get_db),
):
    records = BattlecardRepository.list_all(db, status)

    return [
        {
            "id": item.id,
            "competitor_name": item.competitor_name,
            "domain": item.domain,
            "status": item.status,
            "content": BattlecardContent.model_validate_json(item.content),
            "evidence_urls": json.loads(item.evidence_urls),
            "created_at": item.created_at,
        }
        for item in records
    ]


@router.get("/{battlecard_id}", response_model=BattlecardResponse)
def get_battlecard(
    battlecard_id: int,
    db: Session = Depends(get_db),
):
    item = BattlecardRepository.get_by_id(db, battlecard_id)

    if not item:
        raise HTTPException(status_code=404, detail="Battlecard not found.")

    return {
        "id": item.id,
        "competitor_name": item.competitor_name,
        "domain": item.domain,
        "status": item.status,
        "content": BattlecardContent.model_validate_json(item.content),
        "evidence_urls": json.loads(item.evidence_urls),
        "created_at": item.created_at,
    }
