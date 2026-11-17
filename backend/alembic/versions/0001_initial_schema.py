"""Initial KOMP schema baseline.

This migration is safe to run against a fresh database and adds the two
previously introduced evidence fields to an existing SQLite database.
It intentionally does not drop tables on downgrade because KOMP data is
business evidence and must not be removed by a schema rollback.
"""
from alembic import op
from sqlalchemy import Column, Float, inspect

from app.database.base import Base
from app.models import agent_run, audit_log, battlecard, evidence  # noqa: F401

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)

    if bind.dialect.name == "sqlite":
        columns = {
            column["name"]
            for column in inspect(bind).get_columns("evidence")
        }
        if "keyword_volume" not in columns:
            op.add_column("evidence", Column("keyword_volume", Float(), nullable=True))
        if "ranking_gap" not in columns:
            op.add_column("evidence", Column("ranking_gap", Float(), nullable=True))


def downgrade() -> None:
    # Intentionally non-destructive. Restore schema from a verified backup
    # only through an explicit, reviewed migration.
    pass
