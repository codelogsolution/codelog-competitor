
from sqlalchemy import func, select
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

    @staticmethod
    def list_page(
        db: Session,
        *,
        limit: int,
        offset: int,
        entity_id: int | None = None,
    ) -> tuple[list[AuditLog], int]:
        query = select(AuditLog)
        count_query = select(func.count(AuditLog.id))

        if entity_id is not None:
            query = query.where(AuditLog.entity_id == entity_id)
            count_query = count_query.where(AuditLog.entity_id == entity_id)

        items = list(
            db.scalars(
                query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
                .offset(offset)
                .limit(limit)
            ).all()
        )
        total = db.scalar(count_query) or 0
        return items, total
