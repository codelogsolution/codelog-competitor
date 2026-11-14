
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.battlecard import Battlecard
from app.schemas.approval import ApprovalActionRequest, ApprovalResponse
from app.services.approval_service import ApprovalService

router = APIRouter()


@router.get("/", response_model=list[ApprovalResponse])
def pending_approvals(db: Session = Depends(get_db)):
    return (
        db.query(Battlecard)
        .filter(Battlecard.status.in_(["pending_review", "changes_requested"]))
        .order_by(Battlecard.created_at.desc())
        .all()
    )


def perform_action(
    battlecard_id: int,
    action: str,
    payload: ApprovalActionRequest,
    db: Session,
):
    try:
        return ApprovalService.update_status(
            db=db,
            battlecard_id=battlecard_id,
            action=action,
            actor=payload.actor,
            comment=payload.comment,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{battlecard_id}/approve", response_model=ApprovalResponse)
def approve(
    battlecard_id: int,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db),
):
    return perform_action(battlecard_id, "approve", payload, db)


@router.post("/{battlecard_id}/reject", response_model=ApprovalResponse)
def reject(
    battlecard_id: int,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db),
):
    return perform_action(battlecard_id, "reject", payload, db)


@router.post("/{battlecard_id}/request-changes", response_model=ApprovalResponse)
def request_changes(
    battlecard_id: int,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db),
):
    return perform_action(battlecard_id, "request_changes", payload, db)


@router.post("/{battlecard_id}/resubmit", response_model=ApprovalResponse)
def resubmit(
    battlecard_id: int,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db),
):
    return perform_action(battlecard_id, "resubmit", payload, db)
