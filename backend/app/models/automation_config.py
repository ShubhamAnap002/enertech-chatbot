from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AutomationConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "automation_configs"

    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    device_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("devices.id"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
