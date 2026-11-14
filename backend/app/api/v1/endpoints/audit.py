
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/")
def list_audit_logs(
    entity_id: int | None = None,
    db: Session = Depends(get_db),
):
    return AuditService.list_logs(db, entity_id)
