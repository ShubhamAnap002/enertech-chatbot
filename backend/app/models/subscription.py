from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Subscription(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "subscriptions"

    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("plans.id"))
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_billing_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    billing_cycle: Mapped[str] = mapped_column(String(32), default="monthly")
    provider: Mapped[str] = mapped_column(String(64), default="manual")
    provider_customer_id: Mapped[str] = mapped_column(String(128), default="")
    provider_subscription_id: Mapped[str] = mapped_column(String(128), default="")
