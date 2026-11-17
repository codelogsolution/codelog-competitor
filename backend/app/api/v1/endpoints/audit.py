
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/")
def list_audit_logs(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    entity_id: int | None = None,
    db: Session = Depends(get_db),
):
    return AuditService.list_page(
        db,
        limit=limit,
        offset=offset,
        entity_id=entity_id,
    )
