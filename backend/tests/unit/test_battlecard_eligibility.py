from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from app.services.battlecard_service import BattlecardService


def evidence(**overrides):
    values = {
        "competitor_name": "Example Competitor",
        "domain": "example.com",
        "source_type": "g2",
        "source_url": "https://example.com/reviews",
        "signal_type": "review_theme",
        "category": "EOR",
        "product_area": "Employer of Record",
        "sentiment": "negative",
        "frequency": 25,
        "keyword_volume": None,
        "ranking_gap": None,
        "signal_text": "Customers report slow onboarding.",
        "signal_date": (date.today() - timedelta(days=30)).isoformat(),
        "status": "valid",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_high_priority_valid_evidence_is_eligible():
    valid = evidence()
    result = BattlecardService._assert_battlecard_eligibility(
        "Example Competitor", "example.com", [valid]
    )
    assert result == [valid]


def test_warning_evidence_cannot_qualify_or_enter_battlecard():
    warning = evidence(status="warning")
    with pytest.raises(ValueError, match="score of at least 70"):
        BattlecardService._assert_battlecard_eligibility(
            "Example Competitor", "example.com", [warning]
        )


def test_low_priority_competitor_cannot_generate_battlecard():
    low = evidence(
        sentiment="neutral",
        frequency=0,
        category="Other",
        product_area="Other",
        signal_date=(date.today() - timedelta(days=200)).isoformat(),
    )
    with pytest.raises(ValueError, match="score of at least 70"):
        BattlecardService._assert_battlecard_eligibility(
            "Example Competitor", "example.com", [low]
        )


def test_public_research_does_not_increase_qualification_score():
    uploaded = evidence(
        sentiment="neutral",
        frequency=0,
        category="Other",
        product_area="Other",
        signal_date=(date.today() - timedelta(days=200)).isoformat(),
    )
    research = evidence(
        signal_type="public_research",
        source_type="public_research",
        sentiment="unknown",
        frequency=0,
        category="market_research",
        product_area="",
        signal_date=date.today().isoformat(),
    )
    with pytest.raises(ValueError, match="score of at least 70"):
        BattlecardService._assert_battlecard_eligibility(
            "Example Competitor", "example.com", [uploaded, research]
        )


def test_invalid_source_url_is_not_usable_battlecard_evidence():
    valid_score_but_bad_source = evidence(source_url="javascript:alert(1)")
    with pytest.raises(ValueError, match="usable, source-backed valid evidence"):
        BattlecardService._assert_battlecard_eligibility(
            "Example Competitor", "example.com", [valid_score_but_bad_source]
        )
