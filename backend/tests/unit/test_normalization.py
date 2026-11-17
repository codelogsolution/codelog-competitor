from app.services.normalization_service import NormalizationService


def test_normalize_domain():
    assert (
        NormalizationService.normalize_domain(
            "https://www.example.com/company"
        )
        == "example.com"
    )


def test_normalize_source_type_alias():
    assert (
        NormalizationService.normalize_source_type("manual notes")
        == "manual"
    )


def test_normalize_signal_type_alias():
    assert (
        NormalizationService.normalize_signal_type("review")
        == "review_theme"
    )


def test_normalize_date_formats():
    assert NormalizationService.normalize_date("15-11-2026") == "2026-11-15"
    assert NormalizationService.normalize_date("15/11/2026") == "2026-11-15"


def test_invalid_date_returns_none():
    assert NormalizationService.normalize_date("not-a-date") is None


def test_normalize_number_with_comma():
    assert NormalizationService.normalize_number("1,500") == 1500.0


def test_invalid_number_returns_none():
    assert NormalizationService.normalize_number("unknown") is None


def test_empty_text_returns_none():
    assert NormalizationService.normalize_text("   ") is None


def test_unknown_source_type_is_standardized():
    assert (
        NormalizationService.normalize_source_type("custom source")
        == "custom_source"
    )


def test_normalize_complete_record():
    record = {
        "competitor_name": "Deel",
        "domain": "https://www.deel.com/company",
        "source_type": "manual notes",
        "source_url": "https://www.deel.com",
        "category": "EOR",
        "signal_type": "review",
        "signal_text": "Payroll support delays",
        "signal_date": "15-11-2026",
        "sentiment": "negative",
        "frequency": "30",
        "keyword_volume": "1,500",
        "ranking_gap": "25",
    }

    result = NormalizationService.normalize_record(record)

    assert result["domain"] == "deel.com"
    assert result["source_type"] == "manual"
    assert result["signal_type"] == "review_theme"
    assert result["signal_date"] == "2026-11-15"
    assert result["frequency"] == 30.0
    assert result["keyword_volume"] == 1500.0
    assert result["ranking_gap"] == 25.0
