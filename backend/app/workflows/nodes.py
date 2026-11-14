from datetime import date

from pydantic import ValidationError

from app.schemas.evidence import EvidenceCreate
from app.services.scoring_service import ScoringService
from app.services.research_service import ResearchService
from app.services.evidence_service import EvidenceService
from app.services.battlecard_service import BattlecardService


def scoring_node(state: dict) -> dict:
    records = [
        record
        for record in state.get("records", [])
        if str(
            record.get(
                "validation_status",
                record.get("status", "valid")
            )
        ).lower() != "invalid"
    ]

    response = ScoringService.score_competitors(records)

    return {
        "scoring_results": [
            item.model_dump() for item in response.results
        ],
        "status": "scoring_completed",
    }


def evidence_node(state: dict) -> dict:
    db = state["db"]
    records = []
    errors = []

    # 1. Save uploaded CSV/XLSX evidence.
    for record in state.get("records", []):
        validation_status = str(
            record.get("validation_status", "valid")
        ).lower()

        if validation_status == "invalid":
            continue

        required_fields = [
            "competitor_name",
            "domain",
            "source_type",
            "source_url",
            "category",
            "signal_type",
            "signal_text",
        ]

        if not all(record.get(field) for field in required_fields):
            errors.append(
                f"Skipped incomplete uploaded evidence: "
                f"{record.get('domain', 'unknown domain')}"
            )
            continue

        try:
            records.append(
                EvidenceCreate(
                    competitor_name=str(record["competitor_name"]),
                    domain=str(record["domain"]).strip().lower(),
                    source_type=str(record["source_type"]),
                    source_url=record["source_url"],
                    category=str(record["category"]),
                    signal_type=str(record["signal_type"]),
                    signal_text=str(record["signal_text"]),
                    signal_date=str(
                        record.get("signal_date") or "unknown"
                    ),
                    sentiment=str(
                        record.get("sentiment") or "unknown"
                    ),
                    frequency=int(record.get("frequency") or 0),
                    keyword_gap=str(
                        record.get("keyword_gap") or ""
                    ),
                    product_area=str(
                        record.get("product_area") or ""
                    ),
                    status=(
                        "warning"
                        if validation_status == "warning"
                        else "valid"
                    ),
                )
            )

        except (ValidationError, ValueError, TypeError) as exc:
            errors.append(
                f"Uploaded evidence skipped: {str(exc)}"
            )

    # 2. Save public research evidence.
    for research in state.get("research_results", []):
        for source in research.get("sources", []):
            content = str(source.get("content") or "").strip()

            if not content:
                continue

            try:
                records.append(
                    EvidenceCreate(
                        competitor_name=research["competitor_name"],
                        domain=research["domain"],
                        source_type="public_research",
                        source_url=source["url"],
                        category="market_research",
                        signal_type="public_research",
                        signal_text=content,
                        signal_date=str(
                            source.get("published_date")
                            or date.today().isoformat()
                        ),
                        sentiment="unknown",
                        frequency=0,
                        keyword_gap="",
                        product_area="",
                    )
                )

            except (ValidationError, ValueError, TypeError, KeyError) as exc:
                errors.append(
                    f"Research evidence skipped: {str(exc)}"
                )

    # 3. Persist all evidence together.
    if not records:
        return {
            # This node runs twice (uploaded evidence, then research evidence).
            # Keep the earlier node's results instead of replacing them.
            "evidence_results": state.get("evidence_results", []),
            "errors": [*state.get("errors", []), *errors],
            "status": "no_evidence_to_ingest",
        }

    try:
        result = EvidenceService.ingest(db, records)

        new_results = [
            item.model_dump(mode="json")
            for item in result.results
        ]
        return {
            "evidence_results": [
                *state.get("evidence_results", []),
                *new_results,
            ],
            "errors": [*state.get("errors", []), *errors],
            "status": "evidence_completed",
        }

    except Exception:
        db.rollback()
        raise


async def research_node(state: dict) -> dict:
    response = await ResearchService.research_competitors(
        competitors=state.get("scoring_results", []),
        max_competitors=5,
        max_results_per_competitor=5,
    )

    return {
        "research_results": [
            item.model_dump() for item in response.results
        ],
        "status": "research_completed",
    }


def battlecard_node(state: dict) -> dict:
    db = state["db"]
    results = []
    errors = []

    for competitor in state.get("scoring_results", []):
        if (
            competitor.get("priority") != "high"
            or competitor.get("preliminary_score", 0) < 70
        ):
            continue

        domain = competitor["domain"]

        try:
            result = BattlecardService.generate(
                db,
                competitor["competitor_name"],
                domain,
            )

            results.append({
                "id": result["id"],
                "competitor_name": result["competitor_name"],
                "domain": result["domain"],
                "status": result["status"],
            })

        except Exception as exc:
            db.rollback()
            errors.append(
                f"{domain}: battlecard generation failed: {str(exc)}"
            )

    return {
        "battlecard_results": results,
        "errors": [*state.get("errors", []), *errors],
        "status": "battlecards_completed",
    }


def route_after_scoring(state: dict) -> str:
    high_priority = [
        item
        for item in state.get("scoring_results", [])
        if item.get("priority") == "high"
        and item.get("preliminary_score", 0) >= 70
    ]

    return "research" if high_priority else "finish"


def finish_node(state: dict) -> dict:
    return {"status": "completed"}