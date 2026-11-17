
from collections import defaultdict
from datetime import date, datetime
from typing import Any

from app.schemas.scoring import (
    CompetitorScore,
    ScoreBreakdown,
    ScoreResponse,
)


TARGET_AREAS = {
    "eor",
    "cor",
    "aor",
    "employer of record",
    "contractor of record",
    "global workforce",
    "global hiring",
    "payroll",
    "employment compliance",
    "contractor management",
}


class ScoringService:

    @staticmethod
    def _text(value: Any) -> str:
        return str(value or "").strip().lower()

    @staticmethod
    def _number(value: Any) -> float:
        if value is None or value == "":
            return 0
        try:
            return float(str(value).replace(",", "").strip())
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _age(record: dict) -> int | None:
        age = record.get("signal_age_days")

        if age is not None:
            try:
                return max(0, int(float(age)))
            except (ValueError, TypeError):
                pass

        raw_date = record.get("signal_date")
        if not raw_date:
            return None

        try:
            parsed = date.fromisoformat(str(raw_date)[:10])
            return max(0, (date.today() - parsed).days)
        except (ValueError, TypeError):
            return None

    @classmethod
    def _review_score(cls, record: dict) -> int:
        if cls._text(record.get("signal_type")) != "review_theme":
            return 0

        sentiment = cls._text(record.get("sentiment"))
        frequency = cls._number(record.get("frequency"))
        age = cls._age(record)

        if age is None:
            return 0

        if sentiment == "negative" and frequency >= 25 and age <= 90:
            return 30

        if sentiment in {"negative", "mixed"} and frequency >= 10 and age <= 180:
            return 20

        if frequency > 0:
            return 10

        return 0

    @classmethod
    def _seo_score(cls, record: dict) -> int:
        if cls._text(record.get("signal_type")) != "keyword_gap":
            return 0

        volume = cls._number(
            record.get("keyword_volume", record.get("search_volume"))
        )
        ranking_gap = cls._number(record.get("ranking_gap"))
        relevance = cls._text(
            record.get("relevance")
            or record.get("category")
            or record.get("product_area")
        )

        is_relevant = any(
            term in relevance for term in ("eor", "cor")
        )

        if volume >= 1000 and ranking_gap >= 20 and is_relevant:
            return 25

        if volume >= 300 and ranking_gap >= 10:
            return 15

        if volume > 0:
            return 5

        return 0

    @classmethod
    def _product_overlap(cls, records: list[dict]) -> int:
        eligible_areas = []

        for record in records:
            signal_type = cls._text(record.get("signal_type"))

            if signal_type == "public_research":
                continue

            area = cls._text(record.get("product_area"))
            category = cls._text(record.get("category"))
            combined = f"{area} {category}".strip()

            if combined:
                eligible_areas.append(combined)

        if not eligible_areas:
            return 0

        if any(
            target in area
            for area in eligible_areas
            for target in TARGET_AREAS
        ):
            return 25

        return 10

    @classmethod
    def _recency_score(cls, records: list[dict]) -> int:
        ages = [
            age for age in (cls._age(record) for record in records)
            if age is not None
        ]

        if not ages:
            return 0

        newest_age = min(ages)
        return 15 if newest_age <= 60 else 5

    @staticmethod
    def _priority(score: int) -> str:
        if score >= 70:
            return "high"
        if score >= 50:
            return "medium"
        return "low"

    @classmethod
    def score_competitors(cls, records: list[dict]) -> ScoreResponse:
        grouped = defaultdict(list)

        for record in records:
            # Invalid rows must never contribute to a score.
            validation_status = cls._text(
                record.get("validation_status") or record.get("status") or "valid"
            )
            if validation_status != "valid":
                continue

            domain = cls._text(record.get("domain"))
            name = str(record.get("competitor_name") or "").strip()

            if not domain or not name:
                continue

            grouped[domain].append(record)

        results = []

        for domain, evidence in grouped.items():
            review_points = max(
                (cls._review_score(record) for record in evidence),
                default=0,
            )

            seo_points = max(
                (cls._seo_score(record) for record in evidence),
                default=0,
            )

            overlap_points = cls._product_overlap(evidence)
            recency_points = cls._recency_score(evidence)

            total = (
                review_points
                + seo_points
                + overlap_points
                + recency_points
            )

            reasons = [
                f"Review pain contributed {review_points}/30 points.",
                f"SEO keyword gap contributed {seo_points}/25 points.",
                f"Product overlap contributed {overlap_points}/25 points.",
                f"Recency contributed {recency_points}/15 points.",
            ]

            missing_data = []

            keyword_records = [
                r for r in evidence
                if cls._text(r.get("signal_type")) == "keyword_gap"
            ]

            if keyword_records and not any(
                cls._number(r.get("keyword_volume", r.get("search_volume"))) > 0
                and cls._number(r.get("ranking_gap")) > 0
                for r in keyword_records
            ):
                missing_data.append(
                    "SEO scoring requires keyword_volume and ranking_gap."
                )

            if not any(cls._age(r) is not None for r in evidence):
                missing_data.append("Signal dates are missing or invalid.")

            results.append(
                CompetitorScore(
                    competitor_name=str(
                        evidence[0].get("competitor_name") or domain
                    ),
                    domain=domain,
                    preliminary_score=total,
                    priority=cls._priority(total),
                    breakdown=ScoreBreakdown(
                        review_pain=review_points,
                        seo_gap=seo_points,
                        product_overlap=overlap_points,
                        recency=recency_points,
                    ),
                    reasons=reasons,
                    missing_data=missing_data,
                    evidence_count=len(evidence),
                )
            )

        results.sort(
            key=lambda item: item.preliminary_score,
            reverse=True,
        )

        return ScoreResponse(
            success=True,
            total_competitors=len(results),
            results=results,
        )
