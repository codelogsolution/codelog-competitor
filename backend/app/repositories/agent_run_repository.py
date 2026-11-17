from datetime import datetime, timezone
import json

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.agent_run import AgentRun
from app.models.battlecard import Battlecard
from app.models.evidence import Evidence
from app.models.run_evidence import RunEvidence
from app.models.source_import import SourceImport


class AgentRunRepository:
    @staticmethod
    def create(db: Session, data: dict) -> AgentRun:
        item = AgentRun(**data)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def get_by_run_id(db: Session, run_id: str) -> AgentRun | None:
        return db.scalar(select(AgentRun).where(AgentRun.run_id == run_id))

    @staticmethod
    def list_recent(db: Session, limit: int = 50) -> list[AgentRun]:
        return list(
            db.scalars(
                select(AgentRun)
                .order_by(AgentRun.created_at.desc())
                .limit(limit)
            ).all()
        )

    @staticmethod
    def update(db: Session, item: AgentRun, data: dict) -> AgentRun:
        for key, value in data.items():
            setattr(item, key, value)
        item.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def delete_run_and_owned_data(db: Session, item: AgentRun) -> dict[str, int | str | None]:
        if item.status == "running":
            raise ValueError("A running analysis cannot be deleted.")

        try:
            card_ids = [int(value) for value in json.loads(item.battlecard_ids or "[]")]
        except (ValueError, TypeError, json.JSONDecodeError):
            card_ids = []

        deleted_cards = 0
        if card_ids:
            result = db.execute(delete(Battlecard).where(Battlecard.id.in_(card_ids)))
            deleted_cards = result.rowcount or 0

        links = list(db.scalars(select(RunEvidence).where(RunEvidence.run_id == item.run_id)).all())
        deleted_evidence = 0
        for link in links:
            if not link.is_creator:
                continue
            remaining_link = db.scalar(
                select(RunEvidence)
                .where(
                    RunEvidence.evidence_id == link.evidence_id,
                    RunEvidence.run_id != item.run_id,
                )
                .order_by(RunEvidence.is_creator.desc())
                .limit(1)
            )
            if remaining_link:
                remaining_link.is_creator = True
            else:
                db.execute(delete(Evidence).where(Evidence.id == link.evidence_id))
                deleted_evidence += 1

        db.execute(delete(RunEvidence).where(RunEvidence.run_id == item.run_id))
        source_id = item.import_id
        source = db.get(SourceImport, source_id) if source_id else None
        db.delete(item)
        db.flush()

        if source and source.deleted_at is None:
            other_runs = db.scalar(
                select(func.count()).select_from(AgentRun).where(AgentRun.import_id == source_id)
            ) or 0
            if not other_runs:
                source.status = "ready"
                source.current_stage = "analysis"
                source.stage_progress = json.dumps({
                    "upload": {"status": "completed", "message": "Source file uploaded."},
                    "validation": {"status": "completed", "message": "Rows validated."},
                })
                source.error_message = ""

        return {
            "battlecards_deleted": deleted_cards,
            "evidence_deleted": deleted_evidence,
            "import_id": source_id,
        }
