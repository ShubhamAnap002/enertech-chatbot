from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import hash_token, try_decode_token
from app.db.session import get_db
from app.models.admin import Admin
from app.models.device import Device

bearer = HTTPBearer(auto_error=False)


def get_current_admin(
    db: Session = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> Admin:
    if not creds or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = try_decode_token(creds.credentials)
    if not payload or payload.get("typ") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")
    admin = db.get(Admin, payload.get("sub"))
    if not admin or not admin.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin inactive or missing")
    return admin


def get_current_device(
    db: Session = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> Device:
    if not creds or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token_hash = hash_token(creds.credentials)
    device = db.query(Device).filter(Device.access_token_hash == token_hash).first()
    if not device:
        # Also accept JWT device tokens
        payload = try_decode_token(creds.credentials)
        if payload and payload.get("typ") == "device":
            device = db.get(Device, payload.get("sub"))
    if not device or device.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Device not authorized")
    return device
