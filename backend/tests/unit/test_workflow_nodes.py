from types import SimpleNamespace

from app.schemas.evidence import EvidenceIngestResponse
from app.workflows.nodes import (
    uploaded_evidence_node,
    research_evidence_node,
)


def _capture_ingest(monkeypatch):
    captured = {}

    def fake_ingest(db, records, run_id=None):
        captured["records"] = records
        return EvidenceIngestResponse(
            success=True,
            received_count=len(records),
            inserted_count=len(records),
            duplicate_count=0,
            results=[],
        )

    monkeypatch.setattr(
        "app.workflows.nodes.EvidenceService.ingest",
        fake_ingest,
    )
    return captured


def test_uploaded_evidence_node_does_not_ingest_research(monkeypatch):
    captured = _capture_ingest(monkeypatch)
    state = {
        "db": object(),
        "records": [{
            "competitor_name": "Acme",
            "domain": "acme.com",
            "source_type": "g2",
            "source_url": "https://example.com/review",
            "category": "EOR",
            "signal_type": "review_theme",
            "signal_text": "Slow payroll support",
            "signal_date": "2026-11-01",
            "sentiment": "negative",
            "frequency": 12,
        }],
        "research_results": [{
            "competitor_name": "Acme",
            "domain": "acme.com",
            "sources": [{
                "url": "https://acme.com/news",
                "content": "New product update",
            }],
        }],
        "evidence_results": [],
        "errors": [],
    }

    uploaded_evidence_node(state)

    assert len(captured["records"]) == 1
    assert captured["records"][0].source_type == "g2"


def test_research_evidence_node_does_not_reingest_uploads(monkeypatch):
    captured = _capture_ingest(monkeypatch)
    state = {
        "db": object(),
        "records": [{
            "competitor_name": "Acme",
            "domain": "acme.com",
            "source_type": "g2",
            "source_url": "https://example.com/review",
            "category": "EOR",
            "signal_type": "review_theme",
            "signal_text": "Slow payroll support",
        }],
        "research_results": [{
            "competitor_name": "Acme",
            "domain": "acme.com",
            "sources": [{
                "url": "https://acme.com/news",
                "content": "New product update",
            }],
        }],
        "evidence_results": [],
        "errors": [],
    }

    research_evidence_node(state)

    assert len(captured["records"]) == 1
    assert captured["records"][0].source_type == "public_research"



def test_warning_upload_without_source_url_is_kept_for_review(monkeypatch):
    captured = _capture_ingest(monkeypatch)
    state = {
        "db": object(),
        "records": [{
            "competitor_name": "Acme",
            "domain": "acme.com",
            "source_type": "g2",
            "source_url": "",
            "category": "EOR",
            "signal_type": "review_theme",
            "signal_text": "Slow payroll support",
            "validation_status": "warning",
        }],
        "research_results": [],
        "evidence_results": [],
        "errors": [],
    }

    uploaded_evidence_node(state)

    assert len(captured["records"]) == 1
    assert captured["records"][0].status == "warning"
    assert captured["records"][0].source_url == ""
