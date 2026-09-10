from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.base import utcnow
from app.db.session import get_db
from app.models.admin import Admin
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.schemas.common import PaymentCreate, PaymentOut
from app.services.audit import write_audit
from app.services.razorpay_service import create_razorpay_order

router = APIRouter(prefix="/api/admin/payments", tags=["admin-payments"])


@router.get("", response_model=list[PaymentOut])
def list_payments(db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    return db.query(Payment).order_by(Payment.created_at.desc()).all()


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(payment_id: str, db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("", response_model=PaymentOut)
def create_payment(body: PaymentCreate, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    customer = db.query(Customer).filter(Customer.tenant_id == body.tenant_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Tenant/customer not found")

    subscription_id = None
    if body.assign_plan and body.plan_id:
        plan = db.get(Plan, body.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        # deactivate previous
        for sub in db.query(Subscription).filter(Subscription.tenant_id == body.tenant_id, Subscription.status == "active"):
            sub.status = "replaced"
        start = utcnow()
        end = start + timedelta(days=30 if plan.billing_period == "monthly" else 365)
        sub = Subscription(
            tenant_id=body.tenant_id,
            plan_id=plan.id,
            status="active",
            start_at=start,
            end_at=end,
            next_billing_at=end,
            billing_cycle=plan.billing_period,
            provider="manual" if body.payment_method != "razorpay" else "razorpay",
        )
        db.add(sub)
        db.flush()
        subscription_id = sub.id
        write_audit(db, actor=admin.email, action="plan.assign", tenant_id=body.tenant_id, target=plan.id)

    order_id = ""
    if body.payment_method == "razorpay":
        order = create_razorpay_order(int(round(body.amount * 100)), body.currency, receipt=body.tenant_id[:40])
        order_id = order.get("id", "")

    payment = Payment(
        tenant_id=body.tenant_id,
        subscription_id=subscription_id,
        amount=body.amount,
        currency=body.currency,
        payment_method=body.payment_method,
        transaction_id=body.transaction_id,
        provider_order_id=order_id,
        status=body.status if body.status != "recorded" or body.payment_method != "razorpay" else "pending",
        paid_at=utcnow() if body.status in {"recorded", "verified"} and body.payment_method != "razorpay" else None,
    )
    db.add(payment)
    write_audit(db, actor=admin.email, action="payment.record", tenant_id=body.tenant_id, target="")
    db.commit()
    db.refresh(payment)
    return payment
