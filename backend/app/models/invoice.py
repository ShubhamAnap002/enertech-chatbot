from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin, utcnow


class Invoice(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("payment_id", name="uq_invoice_payment"),)

    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    payment_id: Mapped[str] = mapped_column(String(36), ForeignKey("payments.id"))
    invoice_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    invoice_date: Mapped[date] = mapped_column(Date)
    subtotal: Mapped[float] = mapped_column(Float)
    tax_amount: Mapped[float] = mapped_column(Float, default=0.0)
    total_amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    pdf_path: Mapped[str] = mapped_column(String(512), default="")
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    email_status: Mapped[str] = mapped_column(String(32), default="queued")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
