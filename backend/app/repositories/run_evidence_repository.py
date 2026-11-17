from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.run_evidence import RunEvidence


class RunEvidenceRepository:
    @staticmethod
    def link_many(db: Session, run_id: str, evidence_ids: list[int], creator_ids: set[int]) -> None:
        unique_ids = set(evidence_ids)
        if not unique_ids:
            return
        linked_ids = set(db.scalars(
            select(RunEvidence.evidence_id).where(
                RunEvidence.run_id == run_id,
                RunEvidence.evidence_id.in_(unique_ids),
            )
        ).all())
        db.add_all(
            RunEvidence(
                run_id=run_id,
                evidence_id=evidence_id,
                is_creator=evidence_id in creator_ids,
            )
            for evidence_id in unique_ids - linked_ids
        )
