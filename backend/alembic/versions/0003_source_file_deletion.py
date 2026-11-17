"""Track uploaded source removal while retaining analysis and audit history."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0003_source_file_deletion"
down_revision = "0002_source_imports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {item["name"] for item in inspect(op.get_bind()).get_columns("source_imports")}
    if "deleted_at" not in columns:
        op.add_column("source_imports", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        op.create_index("ix_source_imports_deleted_at", "source_imports", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_source_imports_deleted_at", table_name="source_imports")
    op.drop_column("source_imports", "deleted_at")
