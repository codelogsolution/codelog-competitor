
from app.services.normalization_service import NormalizationService


def test_manual_source_alias():
    assert (
        NormalizationService.normalize_source_type("manual notes")
        == "manual"
    )


def test_review_signal_alias():
    assert (
        NormalizationService.normalize_signal_type("review")
        == "review_theme"
    )


def test_website_claim_alias():
    assert (
        NormalizationService.normalize_signal_type("website_claim")
        == "competitor_claim"
    )


def test_domain_normalization():
    assert (
        NormalizationService.normalize_domain(
            "https://www.example.com/company"
        )
        == "example.com"
    )


def test_number_normalization():
    assert (
        NormalizationService.normalize_number("1,500")
        == 1500.0
    )


def test_invalid_number():
    assert (
        NormalizationService.normalize_number("unknown")
        is None
    )


def test_keyword_gap_is_conditional():
    from app.services.validation_service import ValidationService

    assert (
        "keyword_gap"
        not in ValidationService.REQUIRED_ROW_FIELDS
    )



def test_api_records_are_revalidated_instead_of_trusting_client_status():
    from app.services.validation_service import ValidationService

    report = ValidationService.validate_records([{
        "competitor_name": "Acme",
        "domain": "www.acme.com",
        "source_type": "g2",
        "source_url": "",
        "category": "EOR",
        "signal_type": "review_theme",
        "signal_text": "Customers report slow onboarding.",
        "signal_date": "2026-11-01",
        "sentiment": "negative",
        "frequency": 25,
        "validation_status": "valid",
    }])

    assert report["warning_records"] == 1
    assert report["records"][0]["validation_status"] == "warning"


def test_malformed_signal_date_becomes_warning_not_upload_crash():
    from app.services.validation_service import ValidationService

    report = ValidationService.validate_records([{
        "competitor_name": "Acme",
        "domain": "acme.com",
        "source_type": "g2",
        "source_url": "https://acme.com/reviews",
        "category": "EOR",
        "signal_type": "review_theme",
        "signal_text": "Customers report slow onboarding.",
        "signal_date": "not-a-date",
        "sentiment": "negative",
        "frequency": 25,
    }])

    assert report["warning_records"] == 1
    assert report["records"][0]["validation_status"] == "warning"



def test_upload_row_limit_is_enforced(monkeypatch):
    from datetime import date
    import pytest
    from app.core.config import settings
    from app.services.validation_service import ValidationService

    monkeypatch.setattr(settings, "MAX_UPLOAD_ROWS", 1)
    records = []
    for name in ("Acme", "Beta"):
        records.append({
            "competitor_name": name,
            "domain": f"{name.lower()}.com",
            "source_type": "g2",
            "source_url": f"https://{name.lower()}.com/reviews",
            "category": "EOR",
            "signal_type": "review_theme",
            "signal_text": "Slow onboarding",
            "signal_date": date.today().isoformat(),
            "sentiment": "negative",
            "frequency": 25,
        })
    with pytest.raises(ValueError, match="allowed 1 rows"):
        ValidationService.validate_records(records)
