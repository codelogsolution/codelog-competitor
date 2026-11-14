from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence import Evidence


class EvidenceRepository:

    @staticmethod
    def create_many(
        db: Session,
        records: list[dict],
    ) -> tuple[list[Evidence], int]:

        inserted = []
        duplicates = 0

        for record in records:
            existing = db.scalar(
                select(Evidence).where(
                    Evidence.domain == record["domain"],
                    Evidence.source_url == record["source_url"],
                    Evidence.signal_type == record["signal_type"],
                    Evidence.signal_text == record["signal_text"],
                )
            )

            if existing:
                duplicates += 1
                continue

            evidence = Evidence(**record)
            db.add(evidence)
            inserted.append(evidence)

        try:
            db.commit()
            for item in inserted:
                db.refresh(item)
        except Exception:
            db.rollback()
            raise

        return inserted, duplicates

    @staticmethod
    def list_all(
        db: Session,
        domain: str | None = None,
        limit: int = 100,
    ) -> list[Evidence]:

        query = select(Evidence)

        if domain:
            query = query.where(Evidence.domain == domain.lower())

        query = query.order_by(Evidence.created_at.desc()).limit(limit)

        return list(db.scalars(query).all())

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