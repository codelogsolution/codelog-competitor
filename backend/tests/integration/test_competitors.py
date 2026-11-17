from datetime import date


def valid_review_record(**overrides):
    record = {
        "competitor_name": "Deel",
        "domain": "deel.com",
        "source_type": "g2",
        "source_url": "https://www.g2.com/products/deel",
        "category": "EOR",
        "signal_type": "review_theme",
        "signal_text": "Customers report payroll support delays.",
        "signal_date": date.today().isoformat(),
        "sentiment": "negative",
        "frequency": 30,
        "keyword_gap": "",
        "product_area": "EOR",
    }
    record.update(overrides)
    return record


def test_scoring_api_returns_explainable_high_priority_competitor(client):
    response = client.post(
        "/api/v1/scoring/score",
        json={"records": [valid_review_record()]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["total_competitors"] == 1

    competitor = payload["results"][0]
    assert competitor["domain"] == "deel.com"
    assert competitor["preliminary_score"] == 70
    assert competitor["priority"] == "high"
    assert competitor["breakdown"] == {
        "review_pain": 30,
        "seo_gap": 0,
        "product_overlap": 25,
        "recency": 15,
    }


def test_warning_evidence_is_excluded_from_scoring_api(client):
    response = client.post(
        "/api/v1/scoring/score",
        json={
            "records": [
                valid_review_record(source_url=""),
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_competitors"] == 0
    assert payload["results"] == []


def test_health_endpoint_checks_database(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
