from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.admin import Admin
from app.services.razorpay_service import apply_razorpay_event, persist_webhook_event, verify_razorpay_signature

router = APIRouter(tags=["webhooks"])


@router.post("/api/webhooks/razorpay")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    if not verify_razorpay_signature(raw, signature):
        # Allow unsigned in development with empty secret and mock header
        from app.core.config import settings

        if settings.razorpay_webhook_secret:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    import json

    payload = json.loads(raw.decode("utf-8") or "{}")
    event_id = payload.get("event_id") or payload.get("id") or payload.get("created_at") and f"rz_{payload.get('created_at')}"
    event_id = str(event_id or "unknown")
    event_type = str(payload.get("event") or "")
    row, is_new = persist_webhook_event(
        db,
        provider="razorpay",
        provider_event_id=event_id,
        event_type=event_type,
        payload=payload,
    )
    db.commit()
    if is_new or not row.processed:
        apply_razorpay_event(db, row)
        db.commit()
    return {"ok": True, "duplicate": not is_new}


@router.get("/api/admin/me")
def admin_me_alias(admin: Admin = Depends(get_current_admin)):
    return {"id": admin.id, "email": admin.email, "name": admin.name, "role": admin.role}
