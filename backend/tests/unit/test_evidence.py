from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.models.evidence import Evidence
from app.schemas.evidence import EvidenceCreate
from app.services.evidence_service import EvidenceService


def create_test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    return session_factory()


def sample_evidence():
    return EvidenceCreate(
        competitor_name="Competitor A",
        domain="Competitor-A.com",
        source_type="website",
        source_url="https://competitor-a.com/pricing",
        category="pricing",
        signal_type="pricing_change",
        signal_text="Competitor updated its pricing plans.",
        signal_date="2026-11-10",
        sentiment="neutral",
        frequency=1,
        product_area="global payroll",
    )


def test_evidence_ingestion_and_normalization():
    db = create_test_db()

    try:
        result = EvidenceService.ingest(db, [sample_evidence()])

        assert result.success is True
        assert result.received_count == 1
        assert result.inserted_count == 1
        assert result.duplicate_count == 0

        saved = db.query(Evidence).first()

        assert saved.domain == "competitor-a.com"
        assert saved.category == "pricing"
    finally:
        db.close()


def test_duplicate_evidence_is_skipped():
    db = create_test_db()

    try:
        record = sample_evidence()

        result = EvidenceService.ingest(db, [record, record])

        assert result.received_count == 2
        assert result.inserted_count == 1
        assert result.duplicate_count == 1
    finally:
        db.close()


def test_evidence_summary():
    db = create_test_db()

    try:
        EvidenceService.ingest(db, [sample_evidence()])

        summary = EvidenceService.summary(
            db,
            "competitor-a.com",
        )

        assert summary is not None
        assert summary.total_evidence == 1
        assert summary.evidence_by_type["pricing_change"] == 1
        assert len(summary.sources) == 1
    finally:
        db.close()

def test_case_insensitive_duplicate_across_separate_ingestions():
    db = create_test_db()

    try:
        first_record = sample_evidence()
        second_record = sample_evidence().model_copy(
            update={
                "signal_text": "competitor updated its pricing plans."
            }
        )

        first_result = EvidenceService.ingest(db, [first_record])
        second_result = EvidenceService.ingest(db, [second_record])

        assert first_result.inserted_count == 1
        assert second_result.inserted_count == 0
        assert second_result.duplicate_count == 1
        assert db.query(Evidence).count() == 1

    finally:
        db.close()


def test_warning_evidence_without_source_url_is_retained_for_review():
    db = create_test_db()
    try:
        record = sample_evidence().model_copy(
            update={"source_url": "", "status": "warning"}
        )
        result = EvidenceService.ingest(db, [record])
        saved = db.query(Evidence).one()

        assert result.inserted_count == 1
        assert saved.status == "warning"
        assert saved.source_url == ""
    finally:
        db.close()


def test_valid_evidence_without_source_url_is_rejected():
    import pytest

    db = create_test_db()
    try:
        record = sample_evidence().model_copy(update={"source_url": ""})
        with pytest.raises(ValueError, match="valid HTTP/HTTPS"):
            EvidenceService.ingest(db, [record])
    finally:
        db.close()



def test_warning_evidence_requires_explicit_review_and_records_audit():
    from app.models.audit_log import AuditLog

    db = create_test_db()
    try:
        record = sample_evidence().model_copy(update={"status": "warning"})
        EvidenceService.ingest(db, [record])
        saved = db.query(Evidence).one()

        resolved = EvidenceService.resolve_warning(
            db,
            saved.id,
            "confirm_valid",
            "reviewer@example.test",
            "Source checked by reviewer",
        )

        audit = db.query(AuditLog).one()
        assert resolved.status == "valid"
        assert audit.entity_type == "evidence"
        assert audit.entity_id == saved.id
        assert audit.previous_status == "warning"
        assert audit.new_status == "valid"
        assert audit.actor == "reviewer@example.test"
        assert audit.comment == "Source checked by reviewer"
    finally:
        db.close()


def test_warning_without_source_url_cannot_be_confirmed_valid():
    import pytest

    db = create_test_db()
    try:
        record = sample_evidence().model_copy(
            update={"source_url": "", "status": "warning"}
        )
        EvidenceService.ingest(db, [record])
        saved = db.query(Evidence).one()

        with pytest.raises(ValueError, match="valid HTTP/HTTPS"):
            EvidenceService.resolve_warning(
                db, saved.id, "confirm_valid", "reviewer"
            )
        assert saved.status == "warning"
    finally:
        db.close()


def test_warning_can_be_explicitly_marked_invalid():
    db = create_test_db()
    try:
        record = sample_evidence().model_copy(update={"status": "warning"})
        EvidenceService.ingest(db, [record])
        saved = db.query(Evidence).one()

        resolved = EvidenceService.resolve_warning(
            db, saved.id, "mark_invalid", "reviewer"
        )
        assert resolved.status == "invalid"
    finally:
        db.close()



def test_warning_can_be_confirmed_after_reviewer_adds_source_url():
    db = create_test_db()
    try:
        record = sample_evidence().model_copy(
            update={"source_url": "", "status": "warning"}
        )
        EvidenceService.ingest(db, [record])
        saved = db.query(Evidence).one()

        resolved = EvidenceService.resolve_warning(
            db,
            saved.id,
            "confirm_valid",
            "reviewer",
            "Verified source",
            "https://competitor-a.com/reviews",
        )
        assert resolved.status == "valid"
        assert resolved.source_url == "https://competitor-a.com/reviews"
    finally:
        db.close()
