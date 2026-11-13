
from datetime import date

from app.services.scoring_service import ScoringService


def make_record(**overrides):
    record = {
        "competitor_name": "Test Competitor",
        "domain": "test.com",
        "source_type": "g2",
        "signal_type": "review_theme",
        "signal_text": "Payroll support delays",
        "signal_date": date.today().isoformat(),
        "sentiment": "negative",
        "frequency": 30,
        "category": "EOR",
        "product_area": "EOR",
        "status": "valid",
    }
    record.update(overrides)
    return record


def test_high_review_pain_score():
    record = make_record()
    assert ScoringService._review_score(record) == 30


def test_medium_review_pain_score():
    record = make_record(frequency=12)
    assert ScoringService._review_score(record) == 20


def test_low_review_pain_score():
    record = make_record(sentiment="positive", frequency=5)
    assert ScoringService._review_score(record) == 10


def test_high_seo_score():
    record = make_record(
        signal_type="keyword_gap",
        keyword_volume=1500,
        ranking_gap=25,
        relevance="EOR",
    )
    assert ScoringService._seo_score(record) == 25


def test_product_overlap_score():
    records = [make_record(product_area="EOR")]
    assert ScoringService._product_overlap(records) == 25


def test_priority_classification():
    assert ScoringService._priority(75) == "high"
    assert ScoringService._priority(55) == "medium"
    assert ScoringService._priority(40) == "low"


def test_competitor_aggregation_maximum_95():
    records = [
        make_record(),
        make_record(
            signal_type="keyword_gap",
            keyword_volume=1500,
            ranking_gap=25,
            relevance="EOR",
            signal_text="EOR software",
        ),
    ]

    response = ScoringService.score_competitors(records)

    assert response.total_competitors == 1
    result = response.results[0]
    assert result.preliminary_score == 95
    assert result.priority == "high"


def test_invalid_records_are_excluded():
    records = [make_record(status="invalid")]

    response = ScoringService.score_competitors(records)

    assert response.total_competitors == 0


def test_multiple_review_rows_are_not_added():
    records = [
        make_record(frequency=30),
        make_record(frequency=50, signal_text="Slow support"),
    ]

    response = ScoringService.score_competitors(records)

    assert response.results[0].breakdown.review_pain == 30
