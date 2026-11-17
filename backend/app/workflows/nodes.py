import logging

from pydantic import ValidationError

from app.schemas.evidence import EvidenceCreate
from app.services.scoring_service import ScoringService
from app.services.research_service import ResearchService
from app.services.evidence_service import EvidenceService
from app.services.battlecard_service import BattlecardService

logger = logging.getLogger(__name__)


def _report_progress(state: dict, stage: str, status: str, message: str) -> None:
    callback = state.get("progress_callback")
    if callback:
        callback({"type": "progress", "stage": stage, "status": status, "message": message})


def scoring_node(state: dict) -> dict:
    _report_progress(state, "scoring", "started", "Scoring validated competitor signals.")
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
    _report_progress(state, "scoring", "completed", f"Scored {len(response.results)} competitors.")

    return {
        "scoring_results": [
            item.model_dump() for item in response.results
        ],
        "status": "scoring_completed",
    }


def _ingest_evidence(
    state: dict,
    *,
    include_uploaded: bool,
    include_research: bool,
) -> dict:
    stage = "uploaded_evidence" if include_uploaded else "research_evidence"
    _report_progress(state, stage, "started", "Saving source-backed evidence records.")
    db = state["db"]
    records = []
    errors = []

    if include_uploaded:
        for record in state.get("records", []):
            validation_status = str(
                record.get("validation_status", record.get("status", "valid"))
            ).lower()
            if validation_status == "invalid":
                continue

            required_fields = [
                "competitor_name", "domain", "source_type",
                "category", "signal_type", "signal_text",
            ]
            if not all(record.get(field) for field in required_fields):
                errors.append(
                    "Skipped incomplete uploaded evidence: "
                    f"{record.get('domain', 'unknown domain')}"
                )
                continue

            try:
                records.append(EvidenceCreate(
                    competitor_name=str(record["competitor_name"]),
                    domain=str(record["domain"]).strip().lower(),
                    source_type=str(record["source_type"]),
                    source_url=str(record.get("source_url") or ""),
                    category=str(record["category"]),
                    signal_type=str(record["signal_type"]),
                    signal_text=str(record["signal_text"]),
                    signal_date=str(record.get("signal_date") or "unknown"),
                    sentiment=str(record.get("sentiment") or "unknown"),
                    frequency=int(record.get("frequency") or 0),
                    keyword_gap=str(record.get("keyword_gap") or ""),
                    keyword_volume=record.get("keyword_volume"),
                    ranking_gap=record.get("ranking_gap"),
                    product_area=str(record.get("product_area") or ""),
                    status="warning" if validation_status == "warning" else "valid",
                ))
            except (ValidationError, ValueError, TypeError) as exc:
                errors.append(f"Uploaded evidence skipped: {exc}")

    if include_research:
        for research in state.get("research_results", []):
            for source in research.get("sources", []):
                content = str(source.get("content") or "").strip()
                if not content:
                    continue
                try:
                    records.append(EvidenceCreate(
                        competitor_name=research["competitor_name"],
                        domain=research["domain"],
                        source_type="public_research",
                        source_url=source["url"],
                        category="market_research",
                        signal_type="public_research",
                        signal_text=content,
                        signal_date=str(source.get("published_date") or "unknown"),
                        sentiment="unknown",
                        frequency=0,
                        keyword_gap="",
                        product_area="",
                    ))
                except (ValidationError, ValueError, TypeError, KeyError) as exc:
                    errors.append(f"Research evidence skipped: {exc}")

    if not records:
        _report_progress(state, stage, "completed", "No new evidence records needed saving.")
        return {
            "evidence_results": state.get("evidence_results", []),
            "errors": [*state.get("errors", []), *errors],
            "status": "evidence_completed",
        }

    try:
        result = EvidenceService.ingest(db, records, run_id=state.get("run_id"))
        new_results = [item.model_dump(mode="json") for item in result.results]
        _report_progress(state, stage, "completed", f"Saved {len(new_results)} evidence records.")
        return {
            "evidence_results": [*state.get("evidence_results", []), *new_results],
            "errors": [*state.get("errors", []), *errors],
            "status": "evidence_completed",
        }
    except Exception:
        db.rollback()
        raise


def uploaded_evidence_node(state: dict) -> dict:
    return _ingest_evidence(
        state, include_uploaded=True, include_research=False
    )


def research_evidence_node(state: dict) -> dict:
    return _ingest_evidence(
        state, include_uploaded=False, include_research=True
    )


async def research_node(state: dict) -> dict:
    _report_progress(state, "research", "started", "Searching public sources for eligible high-priority competitors.")
    response = await ResearchService.research_competitors(
        competitors=state.get("scoring_results", []),
        max_competitors=5,
        max_results_per_competitor=5,
    )
    source_count = sum(len(item.sources) for item in response.results)
    _report_progress(state, "research", "completed", f"Collected {source_count} public sources across {response.researched_count} competitors.")

    return {
        "research_results": [
            item.model_dump() for item in response.results
        ],
        "status": "research_completed",
    }


def battlecard_node(state: dict) -> dict:
    _report_progress(state, "battlecards", "started", "Preparing drafts from eligible, source-backed evidence.")
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
            logger.exception("Battlecard generation failed for domain=%s", domain)
            errors.append(
                f"{domain}: battlecard generation failed ({type(exc).__name__}). "
                "Check application logs for details."
            )

    _report_progress(state, "battlecards", "completed", f"Prepared {len(results)} battlecard drafts for review.")
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

    if high_priority:
        return "research"
    for stage in ("research", "research_evidence", "battlecards"):
        _report_progress(state, stage, "skipped", "No competitor met the research and draft eligibility rules.")
    return "finish"


def finish_node(state: dict) -> dict:
    _report_progress(state, "complete", "completed", "The analysis workflow is complete.")
    return {"status": "completed"}
