import asyncio
import json
import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.agents.competitor_agent import CompetitorAgent
from app.database.session import SessionLocal, get_db
from app.models.agent_run import AgentRun
from app.repositories.agent_run_repository import AgentRunRepository
from app.repositories.source_import_repository import SourceImportRepository
from app.services.validation_service import ValidationService
from app.services.audit_service import AuditService
from app.schemas.agent import (
    AgentRunHistoryResponse,
    AgentRunRequest,
    AgentRunResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _json(value) -> str:
    return json.dumps(value or [], ensure_ascii=False, default=str)


def _history_response(item: AgentRun) -> dict:
    return {
        "run_id": item.run_id,
        "import_id": item.import_id,
        "source_name": item.source_name,
        "status": item.status,
        "uploaded_count": item.uploaded_count,
        "valid_count": item.valid_count,
        "warning_count": item.warning_count,
        "invalid_count": item.invalid_count,
        "scoring_results": json.loads(item.scoring_results or "[]"),
        "research_targets": json.loads(item.research_targets or "[]"),
        "research_results": json.loads(item.research_results or "[]"),
        "source_urls": json.loads(item.source_urls or "[]"),
        "battlecard_ids": json.loads(item.battlecard_ids or "[]"),
        "errors": json.loads(item.errors or "[]"),
        "created_at": item.created_at.isoformat() if item.created_at else "",
        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
    }


def _result_payload(run_id: str, result: dict) -> dict:
    return {
        "run_id": run_id,
        "status": result.get("status", "completed"),
        "scoring_results": result.get("scoring_results", []),
        "research_results": result.get("research_results", []),
        "evidence_results": result.get("evidence_results", []),
        "battlecard_results": result.get("battlecard_results", []),
        "errors": result.get("errors", []),
    }


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


def _save_import_progress(import_id: str | None, event: dict) -> None:
    if not import_id or event.get("type") != "progress":
        return
    db = SessionLocal()
    try:
        source_import = SourceImportRepository.get(db, import_id)
        if not source_import:
            return
        if source_import.status != "running":
            return
        progress = json.loads(source_import.stage_progress or "{}")
        stage = str(event.get("stage") or "analysis")
        progress[stage] = {
            "status": event.get("status", "started"),
            "message": event.get("message", ""),
        }
        SourceImportRepository.update(db, source_import, {
            "status": "running",
            "current_stage": stage,
            "stage_progress": json.dumps(progress, ensure_ascii=False),
        })
    finally:
        db.close()


def _finish_import(db: Session, import_id: str | None, battlecard_ids: list[int], status: str, errors: list[str]) -> None:
    if not import_id:
        return
    source_import = SourceImportRepository.get(db, import_id)
    if not source_import:
        return
    progress = json.loads(source_import.stage_progress or "{}")
    has_drafts = bool(battlecard_ids)
    progress["complete"] = {"status": "completed", "message": "Analysis run finished."}
    SourceImportRepository.update(db, source_import, {
        "status": "pending_review" if has_drafts else status,
        "current_stage": "human_approval" if has_drafts else "complete",
        "stage_progress": json.dumps(progress, ensure_ascii=False),
        "error_message": " ".join(errors)[:2000],
    })


def _start_import(db: Session, import_id: str | None) -> None:
    if not import_id:
        return
    source_import = SourceImportRepository.get(db, import_id)
    if not source_import:
        raise HTTPException(status_code=404, detail="Uploaded source record not found.")
    if source_import.status == "running":
        raise HTTPException(status_code=409, detail="This source is already being analyzed.")
    SourceImportRepository.update(db, source_import, {
        "status": "running",
        "current_stage": "scoring",
        "error_message": "",
        "stage_progress": json.dumps({
            "upload": {"status": "completed", "message": "Source file uploaded."},
            "validation": {"status": "completed", "message": "Rows validated."},
        }),
    })


@router.get("/runs", response_model=list[AgentRunHistoryResponse])
def list_agent_runs(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return [_history_response(item) for item in AgentRunRepository.list_recent(db, limit)]


@router.get("/runs/{run_id}", response_model=AgentRunHistoryResponse)
def get_agent_run(run_id: str, db: Session = Depends(get_db)):
    item = AgentRunRepository.get_by_run_id(db, run_id)
    if not item:
        raise HTTPException(status_code=404, detail="Analysis run not found.")
    return _history_response(item)


@router.delete("/runs/{run_id}")
def delete_agent_run(run_id: str, db: Session = Depends(get_db)):
    item = AgentRunRepository.get_by_run_id(db, run_id)
    if not item:
        raise HTTPException(status_code=404, detail="Analysis run not found.")
    run_database_id = item.id
    previous_status = item.status
    try:
        deleted = AgentRunRepository.delete_run_and_owned_data(db, item)
        AuditService.record(
            db,
            entity_id=run_database_id,
            entity_type="analysis_run",
            action="delete_analysis",
            previous_status=previous_status,
            new_status="deleted",
            actor="workspace",
            comment=(
                f"Run and its scores were deleted; {deleted['battlecards_deleted']} battlecard(s) "
                f"and {deleted['evidence_deleted']} run-owned evidence record(s) removed. "
                "Audit events were retained."
            ),
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception:
        db.rollback()
        raise
    return {
        "success": True,
        "message": "Analysis data deleted. The uploaded source file and audit trail are retained.",
        **deleted,
    }


@router.post("/run/stream")
async def run_agent_stream(payload: AgentRunRequest):
    """Run the existing workflow and stream actual LangGraph node progress."""
    try:
        validation_report = ValidationService.validate_records(payload.records)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    validated_records = validation_report["records"]
    statuses = [
        str(record.get("validation_status") or "invalid").lower()
        for record in validated_records
    ]
    run_id = str(uuid4())

    # Persist the run before opening the response stream so clients can safely
    # display its reference while the graph continues to execute.
    initial_db = SessionLocal()
    try:
        _start_import(initial_db, payload.import_id)
        source_import = SourceImportRepository.get(initial_db, payload.import_id) if payload.import_id else None
        AgentRunRepository.create(
            initial_db,
            {
                "run_id": run_id,
                "import_id": payload.import_id,
                "source_name": (source_import.original_filename if source_import else payload.source_name)[:255],
                "status": "running",
                "uploaded_count": len(validated_records),
                "valid_count": statuses.count("valid"),
                "warning_count": statuses.count("warning"),
                "invalid_count": statuses.count("invalid"),
            },
        )
    finally:
        initial_db.close()

    async def event_stream():
        events: asyncio.Queue[dict] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def publish(event: dict) -> None:
            loop.call_soon_threadsafe(events.put_nowait, event)

        async def execute_run() -> dict:
            db = SessionLocal()
            try:
                result = await CompetitorAgent().run(
                    records=validated_records,
                    db=db,
                    run_id=run_id,
                    progress_callback=publish,
                )
                scoring_results = result.get("scoring_results", [])
                research_results = result.get("research_results", [])
                evidence_results = result.get("evidence_results", [])
                battlecard_results = result.get("battlecard_results", [])
                research_targets = [
                    {
                        "competitor_name": item.get("competitor_name"),
                        "domain": item.get("domain"),
                        "preliminary_score": item.get("preliminary_score"),
                    }
                    for item in scoring_results
                    if item.get("priority") == "high"
                    and item.get("preliminary_score", 0) >= 70
                ]
                source_urls = sorted({
                    str(url)
                    for url in (
                        [item.get("source_url") for item in evidence_results]
                        + [
                            source.get("url")
                            for research in research_results
                            for source in research.get("sources", [])
                        ]
                    )
                    if url
                })
                battlecard_ids = [
                    int(item["id"])
                    for item in battlecard_results
                    if item.get("id") is not None
                ]
                run_record = AgentRunRepository.get_by_run_id(db, run_id)
                if run_record:
                    AgentRunRepository.update(
                        db,
                        run_record,
                        {
                            "status": result.get("status", "completed"),
                            "scoring_results": _json(scoring_results),
                            "research_targets": _json(research_targets),
                            "research_results": _json(research_results),
                            "source_urls": _json(source_urls),
                            "battlecard_ids": _json(battlecard_ids),
                            "errors": _json(result.get("errors", [])),
                        },
                    )
                _finish_import(
                    db,
                    payload.import_id,
                    battlecard_ids,
                    result.get("status", "completed"),
                    result.get("errors", []),
                )
                return _result_payload(run_id, result)
            except Exception:
                db.rollback()
                logger.exception("Streamed competitor workflow failed run_id=%s", run_id)
                try:
                    run_record = AgentRunRepository.get_by_run_id(db, run_id)
                    if run_record:
                        AgentRunRepository.update(
                            db,
                            run_record,
                            {
                                "status": "failed",
                                "errors": _json(["Workflow execution failed. See server logs."]),
                            },
                        )
                    source_import = SourceImportRepository.get(db, payload.import_id) if payload.import_id else None
                    if source_import:
                        SourceImportRepository.update(db, source_import, {
                            "status": "failed",
                            "error_message": "Workflow execution failed. See run history for details.",
                        })
                except Exception:
                    db.rollback()
                    logger.exception("Failed to persist failed run status run_id=%s", run_id)
                raise
            finally:
                db.close()

        yield _sse({"type": "started", "run_id": run_id})
        task = asyncio.create_task(execute_run())
        try:
            while not task.done() or not events.empty():
                try:
                    event = await asyncio.wait_for(events.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                _save_import_progress(payload.import_id, event)
                yield _sse(event)

            # Let callbacks scheduled from sync LangGraph nodes reach the queue.
            await asyncio.sleep(0)
            while not events.empty():
                yield _sse(events.get_nowait())

            completed = await task
            yield _sse({"type": "completed", "result": completed})
        except Exception:
            logger.exception("Could not stream competitor workflow run_id=%s", run_id)
            yield _sse({
                "type": "failed",
                "run_id": run_id,
                "message": f"Analysis failed. Run reference: {run_id}",
            })
            failed_db = SessionLocal()
            try:
                source_import = SourceImportRepository.get(failed_db, payload.import_id) if payload.import_id else None
                if source_import:
                    SourceImportRepository.update(failed_db, source_import, {
                        "status": "failed",
                        "current_stage": source_import.current_stage,
                        "error_message": f"Analysis failed. Run reference: {run_id}",
                    })
            finally:
                failed_db.close()
        # If the client disconnects, execute_run owns its database session and
        # can finish and persist run history independently of this response.

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    payload: AgentRunRequest,
    db: Session = Depends(get_db),
):
    run_id = str(uuid4())
    try:
        validation_report = ValidationService.validate_records(payload.records)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    validated_records = validation_report["records"]
    statuses = [
        str(record.get("validation_status") or "invalid").lower()
        for record in validated_records
    ]
    _start_import(db, payload.import_id)
    source_import = SourceImportRepository.get(db, payload.import_id) if payload.import_id else None
    run_record = AgentRunRepository.create(
        db,
        {
            "run_id": run_id,
            "import_id": payload.import_id,
            "source_name": (source_import.original_filename if source_import else payload.source_name)[:255],
            "status": "running",
            "uploaded_count": len(validated_records),
            "valid_count": statuses.count("valid"),
            "warning_count": statuses.count("warning"),
            "invalid_count": statuses.count("invalid"),
        },
    )

    try:
        result = await CompetitorAgent().run(
            records=validated_records,
            db=db,
            run_id=run_id,
        )
        scoring_results = result.get("scoring_results", [])
        research_results = result.get("research_results", [])
        evidence_results = result.get("evidence_results", [])
        battlecard_results = result.get("battlecard_results", [])
        errors = result.get("errors", [])
        research_targets = [
            {
                "competitor_name": item.get("competitor_name"),
                "domain": item.get("domain"),
                "preliminary_score": item.get("preliminary_score"),
            }
            for item in scoring_results
            if item.get("priority") == "high"
            and item.get("preliminary_score", 0) >= 70
        ]
        source_urls = sorted({
            str(url)
            for url in (
                [item.get("source_url") for item in evidence_results]
                + [
                    source.get("url")
                    for research in research_results
                    for source in research.get("sources", [])
                ]
            )
            if url
        })
        battlecard_ids = [
            int(item["id"])
            for item in battlecard_results
            if item.get("id") is not None
        ]
        status = result.get("status", "completed")
        AgentRunRepository.update(
            db,
            run_record,
            {
                "status": status,
                "scoring_results": _json(scoring_results),
                "research_targets": _json(research_targets),
                "research_results": _json(research_results),
                "source_urls": _json(source_urls),
                "battlecard_ids": _json(battlecard_ids),
                "errors": _json(errors),
            },
        )
        _finish_import(db, payload.import_id, battlecard_ids, status, errors)

        return {
            "run_id": run_id,
            "status": status,
            "scoring_results": scoring_results,
            "research_results": research_results,
            "evidence_results": evidence_results,
            "battlecard_results": battlecard_results,
            "errors": errors,
        }

    except Exception as exc:
        db.rollback()
        logger.exception("Competitor workflow failed run_id=%s", run_id)
        try:
            current = AgentRunRepository.get_by_run_id(db, run_id)
            if current:
                AgentRunRepository.update(
                    db,
                    current,
                    {
                        "status": "failed",
                        "errors": _json(["Workflow execution failed. See server logs."]),
                    },
                )
            source_import = SourceImportRepository.get(db, payload.import_id) if payload.import_id else None
            if source_import:
                SourceImportRepository.update(db, source_import, {
                    "status": "failed",
                    "error_message": "Workflow execution failed. See run history for details.",
                })
        except Exception:
            db.rollback()
            logger.exception("Failed to persist failed run status run_id=%s", run_id)
        raise HTTPException(
            status_code=500,
            detail=f"Competitor workflow execution failed. Run ID: {run_id}",
        ) from exc
