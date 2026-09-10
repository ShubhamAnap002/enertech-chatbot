from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment


def calculate_tax(subtotal: float) -> tuple[float, float]:
    tax = round(subtotal * (settings.tax_rate_percent / 100.0), 2)
    total = round(subtotal + tax, 2)
    return tax, total


def next_invoice_number(db: Session) -> str:
    count = db.query(Invoice).count() + 1
    return f"{settings.invoice_prefix}-{date.today().strftime('%Y%m')}-{count:05d}"


def generate_invoice_pdf(invoice: Invoice, customer: Customer, payment: Payment) -> str:
    out_dir = Path("storage") / "invoices"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{invoice.invoice_number}.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"{settings.company_name} — Invoice")
    y -= 30
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Invoice: {invoice.invoice_number}")
    y -= 18
    c.drawString(50, y, f"Date: {invoice.invoice_date.isoformat()}")
    y -= 18
    c.drawString(50, y, f"Bill To: {customer.company_name}")
    y -= 16
    c.drawString(50, y, f"Contact: {customer.contact_name} <{customer.email}>")
    y -= 16
    if customer.gstin:
        c.drawString(50, y, f"GSTIN: {customer.gstin}")
        y -= 16
    y -= 10
    c.drawString(50, y, f"Payment ref: {payment.transaction_id or payment.id}")
    y -= 18
    c.drawString(50, y, f"Subtotal: {invoice.currency} {invoice.subtotal:.2f}")
    y -= 16
    c.drawString(50, y, f"Tax ({settings.tax_rate_percent}%): {invoice.currency} {invoice.tax_amount:.2f}")
    y -= 16
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Total: {invoice.currency} {invoice.total_amount:.2f}")
    y -= 40
    c.setFont("Helvetica", 9)
    c.drawString(50, y, settings.company_address or "")
    c.save()
    return str(path)
