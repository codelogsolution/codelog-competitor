
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
