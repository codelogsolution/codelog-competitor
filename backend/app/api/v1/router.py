from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.uploads import router as uploads_router
from app.api.v1.endpoints.scoring import router as scoring_router
from app.api.v1.endpoints.research import router as research_router
from app.api.v1.endpoints.evidence import router as evidence_router
from app.api.v1.endpoints.battlecards import router as battlecards_router
from app.api.v1.endpoints.approvals import router as approvals_router
from app.api.v1.endpoints.audit import router as audit_router
from app.api.v1.endpoints.agent import router as agent_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])

api_router.include_router(
    uploads_router,
    prefix="/uploads",
    tags=["Uploads"],
)

api_router.include_router(
    scoring_router,
    prefix="/scoring",
    tags=["Scoring"],
)

api_router.include_router(
    research_router,
    prefix="/research",
    tags=["Research"],
)

api_router.include_router(
    evidence_router,
    prefix="/evidence",
    tags=["Evidence"],
)

api_router.include_router(
    battlecards_router,
    prefix="/battlecards",
    tags=["Battlecards"],
)

api_router.include_router(
    approvals_router,
    prefix="/approvals",
    tags=["Approvals"],
)

api_router.include_router(
    audit_router,
    prefix="/audit",
    tags=["Audit"],
)

api_router.include_router(
    agent_router,
    prefix="/agent",
    tags=["AI Agent"],
)