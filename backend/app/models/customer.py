from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Customer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "customers"

    tenant_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255))
    contact_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), index=True)
    mobile: Mapped[str] = mapped_column(String(32), default="")
    alternate_mobile: Mapped[str] = mapped_column(String(32), default="")
    gstin: Mapped[str] = mapped_column(String(32), default="")
    website: Mapped[str] = mapped_column(String(255), default="")
    business_type: Mapped[str] = mapped_column(String(128), default="")
    country: Mapped[str] = mapped_column(String(64), default="India")
    state: Mapped[str] = mapped_column(String(64), default="")
    city: Mapped[str] = mapped_column(String(64), default="")
    billing_address: Mapped[str] = mapped_column(Text, default="")
    postal_code: Mapped[str] = mapped_column(String(32), default="")
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
