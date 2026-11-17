from sqlalchemy.orm import Session

from app.repositories.evidence_repository import EvidenceRepository
from app.core.security import is_safe_http_url
from app.models.evidence import Evidence
from app.repositories.run_evidence_repository import RunEvidenceRepository
from app.services.audit_service import AuditService
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

        has_valid_source = is_safe_http_url(data["source_url"])
        if data.get("status", "valid") == "valid" and not has_valid_source:
            raise ValueError("Valid evidence must include a valid HTTP/HTTPS source URL.")

        return data

    @classmethod
    def ingest(
        cls,
        db: Session,
        records: list[EvidenceCreate],
        run_id: str | None = None,
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

        inserted, database_duplicates, resolved = EvidenceRepository.create_many(
            db, normalized
        )

        if run_id:
            inserted_ids = {item.id for item in inserted}
            RunEvidenceRepository.link_many(
                db,
                run_id,
                [item.id for item in resolved],
                inserted_ids,
            )
        db.commit()
        for item in inserted:
            db.refresh(item)

        duplicate_count += database_duplicates

        return EvidenceIngestResponse(
            success=True,
            received_count=len(records),
            inserted_count=len(inserted),
            duplicate_count=duplicate_count,
            results=inserted,
        )

    @staticmethod
    def resolve_warning(
        db: Session,
        evidence_id: int,
        decision: str,
        actor: str,
        comment: str = "",
        source_url: str | None = None,
    ):
        item = db.get(Evidence, evidence_id)
        if item is None:
            raise LookupError("Evidence not found.")
        if item.status != "warning":
            raise ValueError("Only warning evidence records can be resolved.")

        previous_status = item.status
        if source_url is not None:
            item.source_url = source_url.strip()
        if decision == "confirm_valid":
            if not is_safe_http_url(item.source_url):
                raise ValueError(
                    "Add a valid HTTP/HTTPS source URL before confirming this evidence as valid."
                )
            if not str(item.signal_text or "").strip():
                raise ValueError("Evidence text is required before confirming this record.")
            item.status = "valid"
            action = "confirm_valid"
        elif decision == "mark_invalid":
            item.status = "invalid"
            action = "mark_invalid"
        else:
            raise ValueError("Unsupported evidence resolution decision.")

        try:
            AuditService.record(
                db=db,
                entity_id=item.id,
                action=action,
                previous_status=previous_status,
                new_status=item.status,
                actor=actor,
                comment=comment,
                entity_type="evidence",
            )
            db.commit()
            db.refresh(item)
            return item
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def list_evidence(
        db: Session,
        domain: str | None = None,
        limit: int = 100,
        run_id: str | None = None,
    ):
        return EvidenceRepository.list_all(db, domain, limit, run_id)

    @staticmethod
    def summary(db: Session, domain: str) -> EvidenceSummary | None:
        result = EvidenceRepository.get_summary(db, domain.strip().lower())

        if not result:
            return None

        return EvidenceSummary(**result)
