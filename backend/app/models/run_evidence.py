from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class RunEvidence(Base):
    """Provenance link between an analysis run and evidence it used."""

    __tablename__ = "run_evidence_links"

    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agent_runs.run_id", ondelete="CASCADE"), primary_key=True
    )
    evidence_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True
    )
    is_creator: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
