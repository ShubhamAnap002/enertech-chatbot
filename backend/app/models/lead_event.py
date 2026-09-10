from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin, utcnow


class LeadEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "lead_events"
    __table_args__ = (UniqueConstraint("tenant_id", "lead_hash", name="uq_tenant_lead_hash"),)

    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    device_id: Mapped[str] = mapped_column(String(36), index=True)
    lead_hash: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(512), default="")
    product: Mapped[str] = mapped_column(String(512), default="")
    capacity: Mapped[str] = mapped_column(String(128), default="")
    quantity: Mapped[str] = mapped_column(String(128), default="")
    location: Mapped[str] = mapped_column(String(255), default="")
    score: Mapped[float] = mapped_column(Float, default=0.0)
    action: Mapped[str] = mapped_column(String(32), index=True)
    reason: Mapped[str] = mapped_column(Text, default="")
    rule_results: Mapped[dict] = mapped_column(JSON, default=dict)
    event_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
