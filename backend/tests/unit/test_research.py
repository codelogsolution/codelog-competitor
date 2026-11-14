import pytest

from app.services.research_service import ResearchService


def competitor(score=85, priority="high", domain="acme.com"):
    return {
        "competitor_name": "Acme Global",
        "domain": domain,
        "preliminary_score": score,
        "priority": priority,
    }


def test_high_priority_competitor_is_researchable():
    assert ResearchService.is_researchable(competitor()) is True


def test_medium_score_is_not_researchable():
    assert ResearchService.is_researchable(
        competitor(score=60, priority="medium")
    ) is False


def test_low_priority_is_not_researchable():
    assert ResearchService.is_researchable(
        competitor(score=40, priority="low")
    ) is False


def test_synthetic_domain_is_not_researchable():
    assert ResearchService.is_researchable(
        competitor(domain="rival.invalid")
    ) is False


def test_example_domain_is_not_researchable():
    assert ResearchService.is_researchable(
        competitor(domain="example.com")
    ) is False


def test_research_query_contains_competitor():
    query = ResearchService.build_query("Acme Global", "acme.com")

    assert "Acme Global" in query
    assert "acme.com" in query
    assert "pricing" in query


def test_parse_sources():
    data = {
        "results": [
            {
                "title": "Acme Product Update",
                "url": "https://acme.com/news",
                "content": "New product features",
                "score": 0.95,
            }
        ]
    }

    sources = ResearchService.parse_sources(data, 5)

    assert len(sources) == 1
    assert sources[0].title == "Acme Product Update"
    assert sources[0].url == "https://acme.com/news"


def test_research_only_first_five_targets():
    competitors = [
        competitor(score=90 - i, domain=f"company{i}.com")
        for i in range(7)
    ]

    eligible = [
        item for item in competitors
        if ResearchService.is_researchable(item)
    ]

    eligible.sort(
        key=lambda item: item["preliminary_score"],
        reverse=True,
    )

    assert len(eligible[:5]) == 5
    assert len(eligible[5:]) == 2

@pytest.mark.asyncio
async def test_research_competitors_runs_searches_concurrently(monkeypatch):
    import asyncio

    active = 0
    max_active = 0

    async def fake_search(competitor, max_results=5):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.02)
        active -= 1
        from app.schemas.research import CompetitorResearch
        return CompetitorResearch(
            competitor_name=competitor["competitor_name"],
            domain=competitor["domain"],
            preliminary_score=competitor["preliminary_score"],
            status="completed",
            query="test query",
            sources=[],
        )

    monkeypatch.setattr(ResearchService, "search_competitor", fake_search)
    competitors = [
        competitor(score=90 - i, domain=f"company{i}.com")
        for i in range(5)
    ]

    response = await ResearchService.research_competitors(competitors)

    assert response.researched_count == 5
    assert max_active > 1
    assert max_active <= 3
