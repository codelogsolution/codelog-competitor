from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.source_import import SourceImport


class SourceImportRepository:
    @staticmethod
    def create(db: Session, data: dict) -> SourceImport:
        item = SourceImport(**data)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def get(db: Session, import_id: str) -> SourceImport | None:
        return db.get(SourceImport, import_id)

    @staticmethod
    def list_recent(db: Session, limit: int = 100, include_deleted: bool = False) -> list[SourceImport]:
        query = select(SourceImport)
        if not include_deleted:
            query = query.where(SourceImport.deleted_at.is_(None))
        return list(db.scalars(
            query.order_by(SourceImport.created_at.desc()).limit(limit)
        ).all())

    @staticmethod
    def update(db: Session, item: SourceImport, data: dict) -> SourceImport:
        for key, value in data.items():
            setattr(item, key, value)
        db.commit()
        db.refresh(item)
        return item
