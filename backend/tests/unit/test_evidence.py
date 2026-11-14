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