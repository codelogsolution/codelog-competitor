from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Evidence(Base):
    __tablename__ = "evidence"

    __table_args__ = (
        UniqueConstraint(
            "domain",
            "source_url",
            "signal_type",
            "signal_text",
            name="uq_evidence_source_signal",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    competitor_name: Mapped[str] = mapped_column(String(255), index=True)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    source_type: Mapped[str] = mapped_column(String(100))
    source_url: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(150))
    signal_type: Mapped[str] = mapped_column(String(100), index=True)
    signal_text: Mapped[str] = mapped_column(Text)
    signal_date: Mapped[str] = mapped_column(String(30))
    sentiment: Mapped[str] = mapped_column(String(30), default="unknown")
    frequency: Mapped[int] = mapped_column(Integer, default=0)
    keyword_gap: Mapped[str] = mapped_column(Text, default="")
    keyword_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    ranking_gap: Mapped[float | None] = mapped_column(Float, nullable=True)
    product_area: Mapped[str] = mapped_column(String(150), default="")
    status: Mapped[str] = mapped_column(String(30), default="valid")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


Index(
    "uq_evidence_source_signal_ci",
    Evidence.domain,
    Evidence.source_url,
    Evidence.signal_type,
    func.lower(Evidence.signal_text),
    unique=True,
)
