from datetime import date

import app.api.v1.endpoints.agent as agent_endpoint


def test_agent_run_persists_run_trace(client, monkeypatch):
    class FakeCompetitorAgent:
        async def run(self, records, db, run_id=None):
            return {
                "status": "completed",
                "scoring_results": [
                    {
                        "competitor_name": "Deel",
                        "domain": "deel.com",
                        "preliminary_score": 70,
                        "priority": "high",
                    }
                ],
                "research_results": [],
                "evidence_results": [],
                "battlecard_results": [],
                "errors": [],
            }

    monkeypatch.setattr(agent_endpoint, "CompetitorAgent", FakeCompetitorAgent)

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

    response = client.post("/api/v1/agent/run", json={"records": [record]})
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "completed"
    assert result["run_id"]

    history = client.get("/api/v1/agent/runs")
    assert history.status_code == 200
    assert len(history.json()) == 1
    saved = history.json()[0]
    assert saved["run_id"] == result["run_id"]
    assert saved["uploaded_count"] == 1
    assert saved["valid_count"] == 1
    assert saved["scoring_results"][0]["domain"] == "deel.com"



def test_langgraph_runs_low_priority_upload_without_external_research(test_engine):
    import asyncio
    from datetime import date

    from sqlalchemy.orm import Session

    from app.workflows.competitor_workflow import build_competitor_workflow

    record = {
        "competitor_name": "Sample Vendor",
        "domain": "sample-vendor.example",
        "source_type": "manual",
        "source_url": "https://sample-vendor.example/source",
        "category": "general",
        "signal_type": "other",
        "signal_text": "A general competitor observation.",
        "signal_date": date.today().isoformat(),
        "sentiment": "unknown",
        "frequency": 0,
        "keyword_gap": "",
        "product_area": "general",
        "validation_status": "valid",
        "status": "valid",
    }

    with Session(test_engine) as db:
        result = asyncio.run(build_competitor_workflow().ainvoke({
            "records": [record],
            "db": db,
            "scoring_results": [],
            "research_results": [],
            "evidence_results": [],
            "battlecard_results": [],
            "errors": [],
            "status": "started",
        }))

        assert result["status"] == "completed"
        assert result["scoring_results"][0]["priority"] != "high"
        assert result["research_results"] == []
        assert len(result["evidence_results"]) == 1
