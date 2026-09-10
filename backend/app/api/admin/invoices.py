from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.config import settings
from app.db.base import utcnow
from app.db.session import get_db
from app.models.admin import Admin
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.schemas.common import InvoiceCreateRequest, InvoiceOut, InvoicePreviewRequest
from app.services.audit import write_audit
from app.services.email import EmailService
from app.services.invoices import calculate_tax, generate_invoice_pdf, next_invoice_number

router = APIRouter(prefix="/api/admin/invoices", tags=["admin-invoices"])


@router.get("", response_model=list[InvoiceOut])
def list_invoices(db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    return db.query(Invoice).order_by(Invoice.created_at.desc()).all()


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: str, db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return inv


@router.post("/preview")
def preview_invoice(body: InvoicePreviewRequest, db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    payment = db.get(Payment, body.payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    customer = db.query(Customer).filter(Customer.tenant_id == payment.tenant_id).first()
    tax, total = calculate_tax(payment.amount)
    return {
        "payment_id": payment.id,
        "company_name": customer.company_name if customer else "",
        "subtotal": payment.amount,
        "tax_rate_percent": settings.tax_rate_percent,
        "tax_amount": tax,
        "total_amount": total,
        "currency": payment.currency,
        "invoice_number_preview": next_invoice_number(db),
    }


@router.post("", response_model=InvoiceOut)
def create_invoice(body: InvoiceCreateRequest, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    payment = db.get(Payment, body.payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    existing = db.query(Invoice).filter(Invoice.payment_id == payment.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Invoice already exists for payment")
    customer = db.query(Customer).filter(Customer.tenant_id == payment.tenant_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    tax, total = calculate_tax(payment.amount)
    inv = Invoice(
        tenant_id=payment.tenant_id,
        payment_id=payment.id,
        invoice_number=next_invoice_number(db),
        invoice_date=date.today(),
        subtotal=payment.amount,
        tax_amount=tax,
        total_amount=total,
        currency=payment.currency,
        status="generated",
        notes=body.notes,
    )
    db.add(inv)
    db.flush()
    inv.pdf_path = generate_invoice_pdf(inv, customer, payment)
    write_audit(db, actor=admin.email, action="invoice.generate", tenant_id=payment.tenant_id, target=inv.id)
    db.commit()
    db.refresh(inv)
    return inv


@router.post("/{invoice_id}/send", response_model=InvoiceOut)
def send_invoice(invoice_id: str, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    customer = db.query(Customer).filter(Customer.tenant_id == inv.tenant_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    html = f"""
    <html><body>
    <h2>Invoice {inv.invoice_number}</h2>
    <p>Dear {customer.contact_name},</p>
    <p>Please find your Engyne invoice totaling {inv.currency} {inv.total_amount:.2f}.</p>
    <p>PDF reference: {inv.pdf_path}</p>
    </body></html>
    """
    result = EmailService().send(
        to=customer.email,
        subject=f"Invoice {inv.invoice_number} — Engyne",
        html=html,
        bcc=settings.admin_report_email,
    )
    inv.email_status = result.status
    if result.status == "sent":
        inv.status = "sent"
        inv.sent_at = utcnow()
    write_audit(db, actor=admin.email, action="invoice.send", tenant_id=inv.tenant_id, target=inv.id)
    db.commit()
    db.refresh(inv)
    return inv
