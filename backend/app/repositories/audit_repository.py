
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditRepository:

    @staticmethod
    def create(db: Session, data: dict):
        item = AuditLog(**data)
        db.add(item)
        db.flush()
        db.refresh(item)
        return item

    @staticmethod
    def list_all(db: Session, entity_id: int | None = None):
        query = select(AuditLog).order_by(AuditLog.created_at.desc())

        if entity_id is not None:
            query = query.where(AuditLog.entity_id == entity_id)

        return list(db.scalars(query).all())
