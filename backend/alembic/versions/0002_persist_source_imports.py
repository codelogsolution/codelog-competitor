"""Persist uploaded source batches and link workflow runs."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0002_source_imports"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if "source_imports" not in tables:
        op.create_table(
            "source_imports",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("original_filename", sa.String(length=255), nullable=False),
            sa.Column("stored_filename", sa.String(length=255), nullable=False, unique=True),
            sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("valid_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("warning_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("invalid_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("status", sa.String(length=40), nullable=False, server_default="ready"),
            sa.Column("current_stage", sa.String(length=50), nullable=False, server_default="analysis"),
            sa.Column("stage_progress", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    source_indexes = {item["name"] for item in inspect(bind).get_indexes("source_imports")}
    if "ix_source_imports_status" not in source_indexes:
        op.create_index("ix_source_imports_status", "source_imports", ["status"])
    if "ix_source_imports_created_at" not in source_indexes:
        op.create_index("ix_source_imports_created_at", "source_imports", ["created_at"])

    run_columns = {item["name"] for item in inspect(bind).get_columns("agent_runs")}
    if "import_id" not in run_columns:
        op.add_column("agent_runs", sa.Column("import_id", sa.String(length=36), nullable=True))
    if "source_name" not in run_columns:
        op.add_column("agent_runs", sa.Column("source_name", sa.String(length=255), nullable=False, server_default=""))
    run_indexes = {item["name"] for item in inspect(bind).get_indexes("agent_runs")}
    if "ix_agent_runs_import_id" not in run_indexes:
        op.create_index("ix_agent_runs_import_id", "agent_runs", ["import_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_runs_import_id", table_name="agent_runs")
    op.drop_column("agent_runs", "source_name")
    op.drop_column("agent_runs", "import_id")
    op.drop_index("ix_source_imports_created_at", table_name="source_imports")
    op.drop_index("ix_source_imports_status", table_name="source_imports")
    op.drop_table("source_imports")
