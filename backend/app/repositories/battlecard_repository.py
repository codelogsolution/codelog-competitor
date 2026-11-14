
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.battlecard import Battlecard


class BattlecardRepository:

    @staticmethod
    def create(db: Session, data: dict) -> Battlecard:
        item = Battlecard(**data)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def get_by_id(db: Session, battlecard_id: int):
        return db.get(Battlecard, battlecard_id)

    @staticmethod
    def list_all(db: Session, status: str | None = None):
        query = select(Battlecard).order_by(Battlecard.created_at.desc())

        if status:
            query = query.where(Battlecard.status == status)

        return list(db.scalars(query).all())

    @staticmethod
    def update_status(
        db: Session,
        item: Battlecard,
        status: str,
    ):
        item.status = status
        item.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
        return item
