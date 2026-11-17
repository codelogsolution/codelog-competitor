from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.evidence import Evidence
from app.models.run_evidence import RunEvidence


class EvidenceRepository:

    @staticmethod
    def create_many(
        db: Session,
        records: list[dict],
    ) -> tuple[list[Evidence], int, list[Evidence]]:

        inserted = []
        resolved = []
        duplicates = 0

        try:
            for record in records:
                existing = db.scalar(
                    select(Evidence).where(
                        Evidence.domain == record["domain"],
                        Evidence.source_url == record["source_url"],
                        Evidence.signal_type == record["signal_type"],
                        func.lower(Evidence.signal_text)
                        == record["signal_text"].lower(),
                    )
                )

                if existing:
                    duplicates += 1
                    resolved.append(existing)
                    continue

                try:
                    with db.begin_nested():
                        evidence = Evidence(**record)
                        db.add(evidence)
                        db.flush()

                    inserted.append(evidence)
                    resolved.append(evidence)

                except IntegrityError:
                    duplicates += 1
                    existing = db.scalar(
                        select(Evidence).where(
                            Evidence.domain == record["domain"],
                            Evidence.source_url == record["source_url"],
                            Evidence.signal_type == record["signal_type"],
                            func.lower(Evidence.signal_text) == record["signal_text"].lower(),
                        )
                    )
                    if existing:
                        resolved.append(existing)

        except Exception:
            db.rollback()
            raise

        return inserted, duplicates, resolved

    @staticmethod
    def list_all(
        db: Session,
        domain: str | None = None,
        limit: int = 100,
        run_id: str | None = None,
    ) -> list[Evidence]:

        query = select(Evidence)

        if run_id:
            query = query.join(
                RunEvidence,
                RunEvidence.evidence_id == Evidence.id,
            ).where(RunEvidence.run_id == run_id)

        if domain:
            query = query.where(Evidence.domain == domain.lower())

        query = query.distinct().order_by(Evidence.created_at.desc()).limit(limit)

        return list(db.scalars(query).all())

    @staticmethod
    def delete_by_id(db: Session, evidence_id: int) -> bool:
        evidence = db.get(Evidence, evidence_id)
        if not evidence:
            return False
        db.delete(evidence)
        db.commit()
        return True

    @staticmethod
    def delete_by_domain(db: Session, domain: str) -> int:
        records = db.scalars(
            select(Evidence).where(Evidence.domain == domain.lower())
        ).all()
        count = len(records)
        for record in records:
            db.delete(record)
        if count:
            db.commit()
        return count

    @staticmethod
    def get_summary(
        db: Session,
        domain: str,
    ) -> dict:

        records = db.scalars(
            select(Evidence).where(Evidence.domain == domain.lower())
        ).all()

        if not records:
            return {}

        by_type: dict[str, int] = {}
        by_category: dict[str, int] = {}

        for item in records:
            by_type[item.signal_type] = (
                by_type.get(item.signal_type, 0) + 1
            )
            by_category[item.category] = (
                by_category.get(item.category, 0) + 1
            )

        return {
            "competitor_name": records[0].competitor_name,
            "domain": domain.lower(),
            "total_evidence": len(records),
            "evidence_by_type": by_type,
            "evidence_by_category": by_category,
            "sources": sorted({item.source_url for item in records}),
        }
