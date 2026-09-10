from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.security import generate_setup_key, hash_setup_key
from app.db.base import utcnow
from app.db.session import get_db
from app.models.admin import Admin
from app.models.customer import Customer
from app.models.device import Device
from app.models.setup_key import SetupKey
from app.schemas.common import SetupKeyCreate, SetupKeyOut
from app.services.audit import write_audit

router = APIRouter(tags=["admin-devices-keys"])


@router.get("/api/admin/devices")
def list_devices(db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    rows = db.query(Device).order_by(Device.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "tenant_id": d.tenant_id,
            "device_id": d.device_id,
            "extension_version": d.extension_version,
            "status": d.status,
            "first_connected_at": d.first_connected_at,
            "last_seen_at": d.last_seen_at,
            "runtime_state": d.runtime_state,
            "config_version_seen": d.config_version_seen,
        }
        for d in rows
    ]


@router.post("/api/admin/devices/{id}/reset")
def reset_device(id: str, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    device = db.get(Device, id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.access_token_hash = ""
    device.status = "reset"
    write_audit(db, actor=admin.email, action="device.reset", tenant_id=device.tenant_id, target=device.id)
    db.commit()
    return {"ok": True}


@router.post("/api/admin/devices/{id}/disable")
def disable_device(id: str, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    device = db.get(Device, id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.status = "disabled"
    write_audit(db, actor=admin.email, action="device.disable", tenant_id=device.tenant_id, target=device.id)
    db.commit()
    return {"ok": True}


@router.post("/api/admin/devices/{id}/enable")
def enable_device(id: str, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    device = db.get(Device, id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.status = "active"
    write_audit(db, actor=admin.email, action="device.enable", tenant_id=device.tenant_id, target=device.id)
    db.commit()
    return {"ok": True}


@router.post("/api/admin/setup-keys", response_model=SetupKeyOut)
def create_setup_key(body: SetupKeyCreate, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    customer = db.query(Customer).filter(Customer.tenant_id == body.tenant_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Tenant not found")
    raw = generate_setup_key()
    row = SetupKey(
        tenant_id=body.tenant_id,
        key_hash=hash_setup_key(raw),
        status="active",
        expires_at=utcnow() + timedelta(hours=body.expires_hours),
    )
    db.add(row)
    write_audit(db, actor=admin.email, action="setup_key.generate", tenant_id=body.tenant_id, target=row.id)
    db.commit()
    db.refresh(row)
    return SetupKeyOut(
        id=row.id,
        tenant_id=row.tenant_id,
        status=row.status,
        expires_at=row.expires_at,
        created_at=row.created_at,
        raw_key=raw,
    )


@router.post("/api/admin/setup-keys/{id}/revoke")
def revoke_setup_key(id: str, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    row = db.get(SetupKey, id)
    if not row:
        raise HTTPException(status_code=404, detail="Setup key not found")
    row.status = "revoked"
    row.revoked_at = utcnow()
    write_audit(db, actor=admin.email, action="setup_key.revoke", tenant_id=row.tenant_id, target=row.id)
    db.commit()
    return {"ok": True}
