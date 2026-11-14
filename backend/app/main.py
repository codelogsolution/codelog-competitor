from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

from app.database.base import Base
from app.database.session import engine
from app.models.evidence import Evidence
from app.models.battlecard import Battlecard
from app.models.audit_log import AuditLog




app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered competitor intelligence platform",
    version="1.0.0",
    debug=settings.DEBUG,
)

@app.on_event("startup")
def create_database_tables():
    Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)


@app.get("/", tags=["Root"])
async def root():
    return {
        "success": True,
        "application": settings.APP_NAME,
        "message": "Welcome to KOMP Competitor Intelligence Agent API",
        "docs": "/docs",
    }