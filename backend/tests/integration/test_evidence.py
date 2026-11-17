def sample_payload():
    return {
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


def test_ingest_evidence_api(client):
    response = client.post("/api/v1/evidence/ingest", json=sample_payload())
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["inserted_count"] == 1


def test_list_evidence_api(client):
    ingest = client.post("/api/v1/evidence/ingest", json=sample_payload())
    assert ingest.status_code == 200

    response = client.get(
        "/api/v1/evidence/",
        params={"domain": "competitor-a.com"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_evidence_summary_api(client):
    ingest = client.post("/api/v1/evidence/ingest", json=sample_payload())
    assert ingest.status_code == 200

    response = client.get("/api/v1/evidence/summary/competitor-a.com")
    assert response.status_code == 200
    assert response.json()["total_evidence"] == 1



def test_warning_evidence_remains_warning_when_ingested(client):
    payload = sample_payload()
    payload["records"][0]["source_url"] = ""

    response = client.post("/api/v1/evidence/ingest", json=payload)

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["status"] == "warning"
    assert result["source_url"] == ""
