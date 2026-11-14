from collections import Counter
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.repositories.evidence_repository import EvidenceRepository
from app.schemas.evidence import (
    EvidenceCreate,
    EvidenceIngestResponse,
    EvidenceSummary,
)


class EvidenceService:

    @staticmethod
    def normalize_record(record: EvidenceCreate) -> dict:
        data = record.model_dump(mode="json")

        data["competitor_name"] = data["competitor_name"].strip()
        data["domain"] = data["domain"].strip().lower()
        data["source_type"] = data["source_type"].strip().lower()
        data["source_url"] = str(data["source_url"]).strip()
        data["category"] = data["category"].strip().lower()
        data["signal_type"] = data["signal_type"].strip().lower()
        data["signal_text"] = " ".join(data["signal_text"].split())
        data["sentiment"] = data["sentiment"].strip().lower()
        data["product_area"] = data["product_area"].strip().lower()
        data["keyword_gap"] = data["keyword_gap"].strip()

        parsed = urlparse(data["source_url"])
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Evidence source must be a valid HTTP/HTTPS URL.")

        return data

    @classmethod
    def ingest(
        cls,
        db: Session,
        records: list[EvidenceCreate],
    ) -> EvidenceIngestResponse:

        normalized = []
        seen = set()
        duplicate_count = 0

        for record in records:
            data = cls.normalize_record(record)

            key = (
                data["domain"],
                data["source_url"],
                data["signal_type"],
                data["signal_text"].casefold(),
            )

            if key in seen:
                duplicate_count += 1
                continue

            seen.add(key)
            normalized.append(data)

        inserted, database_duplicates = EvidenceRepository.create_many(
            db, normalized
        )

        duplicate_count += database_duplicates

        return EvidenceIngestResponse(
            success=True,
            received_count=len(records),
            inserted_count=len(inserted),
            duplicate_count=duplicate_count,
            results=inserted,
        )

    @staticmethod
    def list_evidence(
        db: Session,
        domain: str | None = None,
        limit: int = 100,
    ):
        return EvidenceRepository.list_all(db, domain, limit)

    @staticmethod
    def summary(db: Session, domain: str) -> EvidenceSummary | None:
        result = EvidenceRepository.get_summary(db, domain.strip().lower())

        if not result:
            return None

        return EvidenceSummary(**result)