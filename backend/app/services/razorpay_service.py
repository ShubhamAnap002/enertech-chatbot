from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import utcnow
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.webhook_event import WebhookEvent

logger = logging.getLogger(__name__)


def verify_razorpay_signature(raw_body: bytes, signature: str) -> bool:
    secret = settings.razorpay_webhook_secret.encode("utf-8")
    digest = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature or "")


def persist_webhook_event(
    db: Session,
    *,
    provider: str,
    provider_event_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> tuple[WebhookEvent, bool]:
    """Returns (event, is_new)."""
    existing = (
        db.query(WebhookEvent)
        .filter(WebhookEvent.provider == provider, WebhookEvent.provider_event_id == provider_event_id)
        .first()
    )
    if existing:
        return existing, False
    row = WebhookEvent(
        provider=provider,
        provider_event_id=provider_event_id,
        event_type=event_type,
        payload=payload,
        processed=False,
    )
    db.add(row)
    db.flush()
    return row, True


def apply_razorpay_event(db: Session, event: WebhookEvent) -> None:
    if event.processed:
        return
    payload = event.payload or {}
    entity = ((payload.get("payload") or {}).get("payment") or {}).get("entity") or {}
    payment_id = entity.get("id") or ""
    order_id = entity.get("order_id") or ""
    status = entity.get("status") or ""

    payment = None
    if payment_id:
        payment = db.query(Payment).filter(Payment.provider_payment_id == payment_id).first()
    if not payment and order_id:
        payment = db.query(Payment).filter(Payment.provider_order_id == order_id).first()

    if payment and status in {"captured", "authorized"}:
        payment.status = "verified"
        payment.paid_at = utcnow()
        if payment.subscription_id:
            sub = db.get(Subscription, payment.subscription_id)
            if sub:
                sub.status = "active"

    event.processed = True
    event.processed_at = utcnow()
    logger.info("Processed Razorpay webhook %s type=%s", event.provider_event_id, event.event_type)


def create_razorpay_order(amount_paise: int, currency: str = "INR", receipt: str = "") -> dict[str, Any]:
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        return {
            "id": f"order_local_{receipt or 'dev'}",
            "amount": amount_paise,
            "currency": currency,
            "status": "created",
            "mock": True,
        }
    import razorpay

    client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    return client.order.create({"amount": amount_paise, "currency": currency, "receipt": receipt, "payment_capture": 1})
