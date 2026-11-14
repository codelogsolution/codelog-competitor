
import json

from fastapi import APIRouter, Depends, HTTPException
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
        raise HTTPException(
            status_code=500,
            detail="Battlecard generation failed.",
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
