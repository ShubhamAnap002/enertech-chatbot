from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_device
from app.core.config import settings
from app.core.security import generate_device_token, hash_setup_key, hash_token
from app.db.base import utcnow
from app.db.session import get_db
from app.models.automation_config import AutomationConfig
from app.models.device import Device
from app.models.lead_event import LeadEvent
from app.models.setup_key import SetupKey
from app.schemas.common import ConfigPut, HeartbeatIn, LeadEventIn, PairRequest, PairResponse
from app.services.entitlements import EntitlementService

router = APIRouter(prefix="/api/extension", tags=["extension"])


@router.post("/pair", response_model=PairResponse)
def pair(body: PairRequest, db: Session = Depends(get_db)):
    key_hash = hash_setup_key(body.setup_key.strip())
    setup = db.query(SetupKey).filter(SetupKey.key_hash == key_hash).first()
    if not setup:
        raise HTTPException(status_code=400, detail="Invalid setup key")
    if setup.status == "revoked" or setup.revoked_at:
        raise HTTPException(status_code=400, detail="Setup key revoked")
    if setup.expires_at:
        exp = setup.expires_at
        if exp.tzinfo is None:
            from datetime import timezone

            exp = exp.replace(tzinfo=timezone.utc)
        if exp < utcnow():
            raise HTTPException(status_code=400, detail="Setup key expired")
    if setup.status == "used" and setup.used_at:
        raise HTTPException(status_code=400, detail="Setup key already used")

    entitlements = EntitlementService.for_tenant(db, setup.tenant_id)
    if not entitlements.get("access_allowed"):
        raise HTTPException(status_code=403, detail="Subscription inactive")

    active_devices = (
        db.query(Device).filter(Device.tenant_id == setup.tenant_id, Device.status == "active").count()
    )
    max_devices = int(entitlements.get("max_devices", 1))
    existing = (
        db.query(Device)
        .filter(Device.tenant_id == setup.tenant_id, Device.device_id == body.device_id)
        .first()
    )
    if not existing and active_devices >= max_devices:
        raise HTTPException(status_code=403, detail="Device limit reached")

    access_token = generate_device_token()
    now = utcnow()
    if existing:
        device = existing
        device.extension_version = body.extension_version
        device.status = "active"
        device.access_token_hash = hash_token(access_token)
        device.last_seen_at = now
        if not device.first_connected_at:
            device.first_connected_at = now
    else:
        device = Device(
            tenant_id=setup.tenant_id,
            device_id=body.device_id,
            extension_version=body.extension_version,
            status="active",
            access_token_hash=hash_token(access_token),
            first_connected_at=now,
            last_seen_at=now,
        )
        db.add(device)

    setup.status = "used"
    setup.used_at = now
    db.flush()

    cfg = (
        db.query(AutomationConfig)
        .filter(AutomationConfig.tenant_id == setup.tenant_id, AutomationConfig.active.is_(True))
        .order_by(AutomationConfig.version.desc())
        .first()
    )
    config_version = cfg.version if cfg else 0
    db.commit()

    return PairResponse(
        connected=True,
        tenant_id=setup.tenant_id,
        device_id=device.device_id,
        access_token=access_token,
        plan=str(entitlements.get("plan_name") or ""),
        entitlements=entitlements,
        config_version=config_version,
    )


@router.get("/entitlements")
def entitlements(device: Device = Depends(get_current_device), db: Session = Depends(get_db)):
    return EntitlementService.for_tenant(db, device.tenant_id)


@router.get("/config")
def get_config(device: Device = Depends(get_current_device), db: Session = Depends(get_db)):
    cfg = (
        db.query(AutomationConfig)
        .filter(AutomationConfig.tenant_id == device.tenant_id, AutomationConfig.active.is_(True))
        .order_by(AutomationConfig.version.desc())
        .first()
    )
    if not cfg:
        return {"version": 0, "config": {}, "updated_at": None}
    return {"version": cfg.version, "config": cfg.config_json, "updated_at": cfg.updated_at}


@router.put("/config")
def put_config(body: ConfigPut, device: Device = Depends(get_current_device), db: Session = Depends(get_db)):
    entitlements = EntitlementService.for_tenant(db, device.tenant_id)
    if not entitlements.get("access_allowed"):
        raise HTTPException(status_code=403, detail="Subscription inactive")
    errors = EntitlementService.validate_config_against_entitlements(body.config, entitlements)
    refresh = body.config.get("auto_refresh") or {}
    if refresh.get("enabled"):
        interval = int(refresh.get("interval_seconds") or 0)
        if interval < settings.refresh_interval_min or interval > settings.refresh_interval_max:
            errors.append("auto_refresh interval out of bounds")
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    current = (
        db.query(AutomationConfig)
        .filter(AutomationConfig.tenant_id == device.tenant_id, AutomationConfig.active.is_(True))
        .order_by(AutomationConfig.version.desc())
        .first()
    )
    next_version = (current.version + 1) if current else 1
    if current:
        current.active = False
    cfg = AutomationConfig(
        tenant_id=device.tenant_id,
        device_id=device.id,
        version=next_version,
        config_json=body.config,
        active=True,
    )
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return {"version": cfg.version, "config": cfg.config_json, "updated_at": cfg.updated_at}


@router.post("/heartbeat")
def heartbeat(body: HeartbeatIn, device: Device = Depends(get_current_device), db: Session = Depends(get_db)):
    if body.device_id and body.device_id != device.device_id:
        raise HTTPException(status_code=403, detail="device_id mismatch")
    device.last_seen_at = utcnow()
    if body.extension_version:
        device.extension_version = body.extension_version
    device.runtime_state = body.state
    device.config_version_seen = body.config_version
    db.commit()
    return {"ok": True, "server_time": utcnow().isoformat()}


@router.post("/lead-event")
def lead_event(body: LeadEventIn, device: Device = Depends(get_current_device), db: Session = Depends(get_db)):
    if body.device_id and body.device_id != device.device_id:
        raise HTTPException(status_code=403, detail="device_id mismatch")
    existing = (
        db.query(LeadEvent)
        .filter(LeadEvent.tenant_id == device.tenant_id, LeadEvent.lead_hash == body.lead_hash)
        .first()
    )
    if existing:
        return {"ok": True, "duplicate": True, "id": existing.id}

    row = LeadEvent(
        tenant_id=device.tenant_id,
        device_id=device.id,
        lead_hash=body.lead_hash,
        title=body.title,
        product=body.product or body.title,
        capacity=body.capacity,
        quantity=body.quantity,
        location=body.location,
        score=body.score,
        action=body.action,
        reason=body.reason,
        rule_results=body.rule_results,
        event_timestamp=body.event_timestamp or utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"ok": True, "duplicate": False, "id": row.id}
