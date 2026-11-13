
import re
from datetime import datetime
from typing import Any


class NormalizationService:

    SOURCE_TYPE_ALIASES = {
        "semrush": "semrush",
        "g2": "g2",
        "g2 reviews": "g2",
        "capterra": "capterra",
        "competitor website": "competitor_website",
        "competitor_website": "competitor_website",
        "website": "competitor_website",
        "manual": "manual",
        "manual notes": "manual",
    }

    # Map different input signal names to standard signal types
    SIGNAL_TYPE_ALIASES = {
        "review": "review_theme",
        "review_theme": "review_theme",
        "website_claim": "competitor_claim",
        "competitor_claim": "competitor_claim",
        "keyword_gap": "keyword_gap",
        "feature_mention": "feature_mention",
        "pricing": "pricing",
        "product_update": "product_update",
        "other": "other",
    }

    @staticmethod
    def normalize_text(value: Any) -> str | None:
        if value is None:
            return None

        text = str(value).strip()

        if not text or text.lower() in {"nan", "none", "null"}:
            return None

        return text

    @staticmethod
    def normalize_domain(value: Any) -> str | None:
        domain = NormalizationService.normalize_text(value)

        if not domain:
            return None

        domain = domain.lower()
        domain = re.sub(r"^https?://", "", domain)
        domain = domain.split("/")[0]
        domain = domain.removeprefix("www.")

        return domain.rstrip(".")

    @staticmethod
    def normalize_source_type(value: Any) -> str:
        source_type = (
            NormalizationService.normalize_text(value) or ""
        ).lower()

        return NormalizationService.SOURCE_TYPE_ALIASES.get(
            source_type,
            source_type.replace(" ", "_")
        )

    # NEW METHOD: Normalize signal types
    @staticmethod
    def normalize_signal_type(value: Any) -> str | None:
        signal_type = (
            NormalizationService.normalize_text(value) or ""
        ).lower()

        if not signal_type:
            return None

        return NormalizationService.SIGNAL_TYPE_ALIASES.get(
            signal_type,
            signal_type.replace(" ", "_")
        )

    @staticmethod
    def normalize_date(value: Any) -> str | None:
        if value is None:
            return None

        text = NormalizationService.normalize_text(value)

        if not text:
            return None

        formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y/%m/%d",
        ]

        for date_format in formats:
            try:
                return datetime.strptime(
                    text, date_format
                ).date().isoformat()
            except ValueError:
                continue

        try:
            parsed = datetime.fromisoformat(text)
            return parsed.date().isoformat()
        except ValueError:
            return None

    @staticmethod
    def normalize_number(value: Any) -> float | None:
        if value is None:
            return None

        text = NormalizationService.normalize_text(value)

        if not text:
            return None

        try:
            number = float(text.replace(",", ""))

            if number != number or number in (
                float("inf"),
                float("-inf")
            ):
                return None

            return number

        except (ValueError, TypeError):
            return None

    @staticmethod
    def normalize_record(record: dict) -> dict:

        normalized = {
            key: NormalizationService.normalize_text(value)
            for key, value in record.items()
        }

        normalized["competitor_name"] = (
            NormalizationService.normalize_text(
                record.get("competitor_name")
            )
        )

        normalized["domain"] = (
            NormalizationService.normalize_domain(
                record.get("domain")
            )
        )

        normalized["source_type"] = (
            NormalizationService.normalize_source_type(
                record.get("source_type")
            )
        )

        normalized["source_url"] = (
            NormalizationService.normalize_text(
                record.get("source_url")
            )
        )

        # UPDATED: Use signal type normalization method
        normalized["signal_type"] = (
            NormalizationService.normalize_signal_type(
                record.get("signal_type")
            )
        )

        normalized["signal_date"] = (
            NormalizationService.normalize_date(
                record.get("signal_date")
            )
        )

        normalized["frequency"] = (
            NormalizationService.normalize_number(
                record.get("frequency")
            )
        )

        normalized["keyword_volume"] = (
            NormalizationService.normalize_number(
                record.get("keyword_volume")
            )
        )

        normalized["ranking_gap"] = (
            NormalizationService.normalize_number(
                record.get("ranking_gap")
            )
        )

        return normalized
