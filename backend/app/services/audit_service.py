
from sqlalchemy.orm import Session

from app.repositories.audit_repository import AuditRepository


class AuditService:

    @staticmethod
    def record(
        db: Session,
        entity_id: int,
        action: str,
        previous_status: str,
        new_status: str,
        actor: str,
        comment: str = "",
        entity_type: str = "battlecard",
    ):
        return AuditRepository.create(
            db,
            {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
                "previous_status": previous_status,
                "new_status": new_status,
                "actor": actor,
                "comment": comment,
            },
        )

    @staticmethod
    def list_logs(db: Session, entity_id: int | None = None):
        return AuditRepository.list_all(db, entity_id)

    @staticmethod
    def list_page(
        db: Session,
        *,
        limit: int,
        offset: int,
        entity_id: int | None = None,
    ):
        items, total = AuditRepository.list_page(
            db,
            limit=limit,
            offset=offset,
            entity_id=entity_id,
        )
        return {"items": items, "total": total, "limit": limit, "offset": offset}
