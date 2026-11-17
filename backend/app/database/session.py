from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database.url import normalize_database_url

DATABASE_URL = normalize_database_url(settings.DATABASE_URL.strip())
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is required. Configure a PostgreSQL connection string; "
        "KOMP no longer starts with a local SQLite database."
    )
if settings.APP_ENV == "testing" and DATABASE_URL.startswith("sqlite"):
    # In-memory SQLite is reserved for isolated automated tests.
    pass
elif not DATABASE_URL.startswith("postgresql+psycopg://"):
    raise RuntimeError("DATABASE_URL must use PostgreSQL with the psycopg driver.")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
