
from datetime import date, datetime
from io import BytesIO
from pathlib import Path

import pandas as pd

from app.services.normalization_service import NormalizationService


class ValidationService:

    REQUIRED_COLUMNS = {
        "competitor_name",
        "domain",
        "source_type",
        "source_url",
        "category",
        "signal_type",
        "signal_text",
        "signal_date",
        "sentiment",
        "frequency",
        "keyword_gap",
        "product_area",
    }

    REQUIRED_ROW_FIELDS = {
        "competitor_name",
        "domain",
        "source_type",
        "category",
        "signal_type",
        "signal_text",
    }

    KNOWN_SOURCE_TYPES = {
        "semrush",
        "g2",
        "capterra",
        "competitor_website",
        "manual",
    }

    ALLOWED_SIGNAL_TYPES = {
        "keyword_gap",
        "review_theme",
        "feature_mention",
        "competitor_claim",
        "pricing",
        "product_update",
        "other",
    }

    @staticmethod
    def validate_file(filename: str, content: bytes) -> dict:

        extension = Path(filename).suffix.lower()

        try:
            file_buffer = BytesIO(content)

            if extension == ".csv":
                df = pd.read_csv(file_buffer)

            elif extension == ".xlsx":
                df = pd.read_excel(
                    file_buffer,
                    engine="openpyxl"
                )

            else:
                raise ValueError(
                    "Unsupported file format. Upload CSV or XLSX."
                )

        except ValueError:
            raise

        except Exception as exc:
            raise ValueError(
                f"Unable to read uploaded file: {str(exc)}"
            ) from exc

        # Normalize column names
        df.columns = [
            str(column).strip().lower().replace(" ", "_")
            for column in df.columns
        ]

        if df.columns.duplicated().any():
            raise ValueError(
                "Duplicate column names found in uploaded file."
            )

        # Validate required headers
        missing_columns = (
            ValidationService.REQUIRED_COLUMNS - set(df.columns)
        )

        if missing_columns:
            raise ValueError(
                "Missing required columns: "
                + ", ".join(sorted(missing_columns))
            )

        records = []
        errors = []
        warnings = []

        valid_count = 0
        invalid_count = 0
        warning_count = 0

        today = date.today()

        # Track duplicate evidence, not just competitor domains
        seen_evidence = set()

        for index, row in df.iterrows():

            row_number = index + 2

            record = NormalizationService.normalize_record(
                row.to_dict()
            )

            row_errors = []
            row_warnings = []

            # 1. Required fields
            for field in ValidationService.REQUIRED_ROW_FIELDS:

                if not record.get(field):
                    row_errors.append(
                        f"{field} is required"
                    )

            # 2. Conditional keyword validation
            signal_type = (
                record.get("signal_type") or ""
            ).lower()

            if (
                signal_type == "keyword_gap"
                and not record.get("keyword_gap")
            ):
                row_errors.append(
                    "keyword_gap is required for keyword_gap signals"
                )

            # 3. Source type validation
            source_type = record.get("source_type")

            if (
                source_type
                and source_type not in ValidationService.KNOWN_SOURCE_TYPES
            ):
                row_warnings.append(
                    f"Unknown source_type: {source_type}"
                )

            # 4. Signal type validation
            if (
                signal_type
                and signal_type not in ValidationService.ALLOWED_SIGNAL_TYPES
            ):
                row_warnings.append(
                    f"Unknown signal_type: {signal_type}"
                )

            # 5. Source URL validation
            source_url = record.get("source_url")

            if not source_url:
                row_warnings.append(
                    "Source URL missing; manual evidence review required"
                )

            elif not source_url.startswith(("http://", "https://")):
                row_warnings.append(
                    "Source URL format should be reviewed"
                )

            # 6. Date validation
            signal_date = record.get("signal_date")

            if not signal_date:
                row_warnings.append(
                    "Signal date missing or invalid"
                )

            else:
                parsed_date = datetime.strptime(
                    signal_date,
                    "%Y-%m-%d"
                ).date()

                if parsed_date > today:
                    row_warnings.append(
                        "Signal date is in the future"
                    )
                else:
                    age_days = (today - parsed_date).days
                    record["signal_age_days"] = age_days

                    if age_days > 180:
                        row_warnings.append(
                            "Signal is older than 180 days; review confidence"
                        )

            # 7. Sentiment validation
            sentiment = (
                record.get("sentiment") or ""
            ).lower()

            if sentiment not in {
                "positive",
                "negative",
                "mixed",
                "neutral",
                "unknown",
            }:
                row_warnings.append(
                    "Sentiment missing or unrecognized"
                )

            # 8. Frequency validation
            frequency = record.get("frequency")

            if frequency is None:
                row_warnings.append(
                    "Frequency missing; review evidence strength"
                )

            elif frequency < 0:
                row_errors.append(
                    "Frequency cannot be negative"
                )

            elif not frequency.is_integer():
                row_errors.append(
                    "Frequency must be a whole number"
                )

            else:
                record["frequency"] = int(frequency)

            # 9. Optional SEO numeric validation
            for field in ["keyword_volume", "ranking_gap"]:

                value = record.get(field)

                if value is not None and value < 0:
                    row_errors.append(
                        f"{field} cannot be negative"
                    )

            # 10. Duplicate evidence detection
            domain = record.get("domain")

            evidence_key = (
                domain,
                source_type,
                signal_type,
                (record.get("signal_text") or "").lower(),
                record.get("signal_date"),
            )

            if domain:

                if evidence_key in seen_evidence:
                    row_warnings.append(
                        "Duplicate evidence detected; review before merging"
                    )

                else:
                    seen_evidence.add(evidence_key)

            # 11. Business relevance review
            category = (
                record.get("category") or ""
            ).lower()

            product_area = (
                record.get("product_area") or ""
            ).lower()

            relevance_terms = [
                "eor",
                "cor",
                "aor",
                "global workforce",
                "global hiring",
                "contractor",
                "payroll",
                "employment",
                "compliance",
            ]

            combined_text = (
                category
                + " "
                + product_area
                + " "
                + (record.get("signal_text") or "").lower()
            )

            if not any(
                term in combined_text
                for term in relevance_terms
            ):
                row_warnings.append(
                    "Business relevance is unclear; manual review required"
                )

            # 12. Final validation status
            record["validation_errors"] = row_errors
            record["validation_warnings"] = row_warnings

            if row_errors:

                record["validation_status"] = "invalid"
                invalid_count += 1

                for error in row_errors:
                    errors.append({
                        "row": row_number,
                        "message": error,
                    })

            elif row_warnings:

                record["validation_status"] = "warning"
                warning_count += 1

                for warning in row_warnings:
                    warnings.append({
                        "row": row_number,
                        "message": warning,
                    })

            else:

                record["validation_status"] = "valid"
                valid_count += 1

            records.append(record)

        return {
            "success": invalid_count == 0,
            "total_records": len(records),
            "valid_records": valid_count,
            "invalid_records": invalid_count,
            "warning_records": warning_count,
            "warnings": warnings,
            "errors": errors,
            "records": records,
        }
