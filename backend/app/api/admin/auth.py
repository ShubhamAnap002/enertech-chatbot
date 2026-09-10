from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.admin import Admin
from app.schemas.common import AdminLoginRequest, AdminMe, TokenResponse

router = APIRouter(prefix="/api/admin/auth", tags=["admin-auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == body.email.lower()).first()
    if not admin or not verify_password(body.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin disabled")
    admin.last_login_at = datetime.now(timezone.utc)
    db.commit()
    token = create_access_token(admin.id, claims={"typ": "admin", "role": admin.role, "email": admin.email})
    return TokenResponse(access_token=token)


@router.post("/logout")
def logout(_: Admin = Depends(get_current_admin)):
    return {"ok": True}


@router.get("/me", response_model=AdminMe)
def me(admin: Admin = Depends(get_current_admin)):
    return admin
