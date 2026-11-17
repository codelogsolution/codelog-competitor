"""Track which analysis runs used each evidence record."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0004_run_evidence_links"
down_revision = "0003_source_file_deletion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "run_evidence_links" in set(inspect(op.get_bind()).get_table_names()):
        return
    op.create_table(
        "run_evidence_links",
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("agent_runs.run_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("evidence_id", sa.Integer(), sa.ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("is_creator", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    if "run_evidence_links" in set(inspect(op.get_bind()).get_table_names()):
        op.drop_table("run_evidence_links")
