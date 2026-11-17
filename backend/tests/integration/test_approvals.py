import json

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.battlecard import Battlecard


def create_battlecard(db: Session, competitor: str, status: str) -> Battlecard:
    item = Battlecard(
        competitor_name=competitor,
        domain=f"{competitor.lower().replace(' ', '-')}.example",
        status=status,
        content=json.dumps({
            "overview": "Evidence-backed overview",
            "positioning": "Not available in supplied evidence",
            "strengths": [],
            "weaknesses": [],
            "product_gaps": [],
            "pricing": "Not available in supplied evidence",
            "opportunities": [],
            "threat_level": "Low",
            "recommended_actions": [],
            "evidence_notes": [],
        }),
        evidence_urls="[]",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def test_approval_is_audited_and_only_approved_cards_export(client, test_engine):
    with Session(test_engine) as db:
        pending = create_battlecard(db, "Deel", "pending_review")
        pending_id = pending.id
        create_battlecard(db, "Remote", "pending_review")

    response = client.post(
        f"/api/v1/approvals/{pending_id}/approve",
        json={"actor": "marketing-reviewer", "comment": "Reviewed source evidence."},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

    queue = client.get("/api/v1/approvals/")
    assert queue.status_code == 200
    assert len(queue.json()) == 1
    assert queue.json()[0]["competitor_name"] == "Remote"

    export = client.get("/api/v1/battlecards/export/approved")
    assert export.status_code == 200
    assert "Deel" in export.text
    assert "Remote" not in export.text

    audit = client.get("/api/v1/audit/")
    assert audit.status_code == 200
    assert any(
        row["actor"] == "marketing-reviewer"
        and row["new_status"] == "approved"
        for row in audit.json()["items"]
    )


def test_audit_history_is_paginated(client, test_engine):
    with Session(test_engine) as db:
        db.add_all([
            AuditLog(
                entity_type="battlecard",
                entity_id=index,
                action="approve",
                actor="reviewer",
                previous_status="pending_review",
                new_status="approved",
                comment="",
            )
            for index in range(30)
        ])
        db.commit()

    first_page = client.get("/api/v1/audit/?limit=25&offset=0")
    second_page = client.get("/api/v1/audit/?limit=25&offset=25")

    assert first_page.status_code == 200
    assert len(first_page.json()["items"]) == 25
    assert first_page.json()["total"] == 30
    assert first_page.json()["offset"] == 0
    assert len(second_page.json()["items"]) == 5
    assert second_page.json()["total"] == 30
    assert second_page.json()["offset"] == 25


def test_audit_page_size_is_bounded(client):
    response = client.get("/api/v1/audit/?limit=101")

    assert response.status_code == 422


def test_rejected_battlecard_cannot_be_approved_later(client, test_engine):
    with Session(test_engine) as db:
        item = create_battlecard(db, "Remote", "pending_review")
        item_id = item.id

    rejected = client.post(
        f"/api/v1/approvals/{item_id}/reject",
        json={"actor": "reviewer", "comment": "Not sufficiently supported."},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"

    approve_again = client.post(
        f"/api/v1/approvals/{item_id}/approve",
        json={"actor": "reviewer", "comment": ""},
    )
    assert approve_again.status_code == 409
