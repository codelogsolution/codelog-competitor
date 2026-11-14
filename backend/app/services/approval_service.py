
from sqlalchemy.orm import Session

from app.models.battlecard import Battlecard
from app.repositories.battlecard_repository import BattlecardRepository
from app.services.audit_service import AuditService


class ApprovalService:

    ALLOWED_TRANSITIONS = {
        "pending_review": {"approved", "rejected", "changes_requested"},
        "changes_requested": {"pending_review", "rejected"},
    }

    @classmethod
    def update_status(
        cls,
        db: Session,
        battlecard_id: int,
        action: str,
        actor: str,
        comment: str,
    ):
        item = BattlecardRepository.get_by_id(db, battlecard_id)

        if not item:
            raise LookupError("Battlecard not found.")

        target_status = {
            "approve": "approved",
            "reject": "rejected",
            "request_changes": "changes_requested",
            "resubmit": "pending_review",
        }.get(action)

        if not target_status:
            raise ValueError("Unsupported approval action.")

        allowed = cls.ALLOWED_TRANSITIONS.get(item.status, set())

        if target_status not in allowed:
            raise ValueError(
                f"Cannot change status from {item.status} to {target_status}."
            )

        previous_status = item.status

        try:
            item.status = target_status

            AuditService.record(
                db=db,
                entity_id=item.id,
                action=action,
                previous_status=previous_status,
                new_status=target_status,
                actor=actor,
                comment=comment,
            )

            db.commit()
            db.refresh(item)
            return item

        except Exception:
            db.rollback()
            raise
