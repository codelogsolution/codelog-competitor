from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.main import app


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_ingest_evidence_api():
    payload = {
        "records": [
            {
                "competitor_name": "Competitor A",
                "domain": "competitor-a.com",
                "source_type": "website",
                "source_url": "https://competitor-a.com/pricing",
                "category": "pricing",
                "signal_type": "pricing_change",
                "signal_text": "Competitor updated its pricing plans.",
                "signal_date": "2026-11-10",
                "sentiment": "neutral",
                "frequency": 1,
                "keyword_gap": "",
                "product_area": "global payroll",
            }
        ]
    }

    response = client.post("/api/v1/evidence/ingest", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["inserted_count"] == 1


def test_list_evidence_api():
    response = client.get(
        "/api/v1/evidence/",
        params={"domain": "competitor-a.com"},
    )

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_evidence_summary_api():
    response = client.get(
        "/api/v1/evidence/summary/competitor-a.com"
    )

    assert response.status_code == 200
    assert response.json()["total_evidence"] >= 1