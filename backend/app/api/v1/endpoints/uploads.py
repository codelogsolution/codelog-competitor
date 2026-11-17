
import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.database.session import get_db
from app.models.agent_run import AgentRun
from app.repositories.agent_run_repository import AgentRunRepository
from app.repositories.source_import_repository import SourceImportRepository
from app.schemas.upload import UploadResponse
from app.services.file_service import FileService
from app.services.audit_service import AuditService
from app.services.validation_service import ValidationService

router = APIRouter()

@router.post("", response_model=UploadResponse)
async def upload_competitor_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    try:

        # 1. Check file size
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        content = await file.read(max_size + 1)

        if len(content) > max_size:
            raise ValueError(
                f"File exceeds maximum size of "
                f"{settings.MAX_UPLOAD_SIZE_MB} MB."
            )

        # 2. Validate file extension
        FileService.validate_file(file.filename)

        # 3. Validate uploaded file content
        report = ValidationService.validate_file(
            filename=file.filename,
            content=content,
        )

        # 4. Save uploaded file
        stored_filename = await run_in_threadpool(
            FileService.save_file,
            file.filename,
            content,
        )

        import_id = str(uuid4())
        try:
            SourceImportRepository.create(db, {
                "id": import_id,
                "original_filename": Path(file.filename).name[:255],
                "stored_filename": stored_filename,
                "total_records": report["total_records"],
                "valid_records": report["valid_records"],
                "warning_records": report["warning_records"],
                "invalid_records": report["invalid_records"],
                "status": "ready",
                "current_stage": "analysis",
                "stage_progress": json.dumps({"upload": "completed", "validation": "completed"}),
            })
        except Exception:
            await run_in_threadpool(FileService.delete_file, stored_filename)
            raise

        # 5. Return API response
        return UploadResponse(
            import_id=import_id,
            original_filename=file.filename,
            stored_filename=stored_filename,
            **report,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    finally:

        await file.close()


def _import_summary(item):
    return {
        "import_id": item.id,
        "original_filename": item.original_filename,
        "total_records": item.total_records,
        "valid_records": item.valid_records,
        "warning_records": item.warning_records,
        "invalid_records": item.invalid_records,
        "status": item.status,
        "current_stage": item.current_stage,
        "stage_progress": json.loads(item.stage_progress or "{}"),
        "error_message": item.error_message,
        "created_at": item.created_at.isoformat() if item.created_at else "",
        "updated_at": item.updated_at.isoformat() if item.updated_at else "",
    }


@router.get("")
def list_source_imports(
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return [_import_summary(item) for item in SourceImportRepository.list_recent(db, limit)]


@router.get("/{import_id}")
def get_source_import(import_id: str, db: Session = Depends(get_db)):
    item = SourceImportRepository.get(db, import_id)
    if not item or item.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Source import not found.")
    try:
        content = FileService.read_file(item.stored_filename)
        report = ValidationService.validate_file(item.original_filename, content)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Stored source file could not be read.") from exc
    return {
        **_import_summary(item),
        **report,
        "success": True,
        "original_filename": item.original_filename,
        "stored_filename": item.stored_filename,
    }


@router.delete("/{import_id}")
def delete_source_import(import_id: str, db: Session = Depends(get_db)):
    item = SourceImportRepository.get(db, import_id)
    if not item or item.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Source file not found.")
    if item.status == "running":
        raise HTTPException(status_code=409, detail="Wait for this analysis to finish before removing its source file.")
    runs = list(db.scalars(select(AgentRun).where(AgentRun.import_id == import_id)).all())
    if any(run.status == "running" for run in runs):
        raise HTTPException(status_code=409, detail="Wait for this analysis to finish before removing its source file.")
    try:
        FileService.delete_file(item.stored_filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        for run in runs:
            run_database_id = run.id
            previous_status = run.status
            deleted = AgentRunRepository.delete_run_and_owned_data(db, run)
            AuditService.record(
                db,
                entity_id=run_database_id,
                entity_type="analysis_run",
                action="delete_analysis",
                previous_status=previous_status,
                new_status="deleted",
                actor="workspace",
                comment=(
                    f"Source file {item.original_filename!r} was deleted with this analysis; "
                    f"{deleted['battlecards_deleted']} battlecard(s) and "
                    f"{deleted['evidence_deleted']} run-owned evidence record(s) removed."
                ),
            )
        filename = item.original_filename
        db.delete(item)
        db.flush()
        AuditService.record(
            db,
            entity_id=0,
            entity_type="source_import",
            action="delete_source",
            previous_status="saved",
            new_status="deleted",
            actor="workspace",
            comment=f"Source {import_id} ({filename}) and its linked analysis data were permanently deleted.",
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "success": True,
        "message": "Source file and linked analysis data deleted. Audit history is retained.",
        "analysis_runs_deleted": len(runs),
    }
