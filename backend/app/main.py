from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("KOMP API startup complete (environment=%s)", settings.APP_ENV)
    yield
    logger.info("KOMP API shutdown complete")

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered competitor intelligence platform",
    version="1.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

frontend_origins = [origin.strip() for origin in settings.FRONTEND_ORIGIN.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
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
