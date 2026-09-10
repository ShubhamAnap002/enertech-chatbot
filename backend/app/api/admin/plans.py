from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.admin import Admin
from app.models.plan import Plan
from app.schemas.common import PlanCreate, PlanOut, PlanUpdate
from app.services.audit import write_audit

router = APIRouter(prefix="/api/admin/plans", tags=["admin-plans"])


@router.get("", response_model=list[PlanOut])
def list_plans(db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    return db.query(Plan).order_by(Plan.created_at.desc()).all()


@router.post("", response_model=PlanOut)
def create_plan(body: PlanCreate, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    if db.query(Plan).filter(Plan.name == body.name).first():
        raise HTTPException(status_code=409, detail="Plan name exists")
    plan = Plan(**body.model_dump())
    db.add(plan)
    write_audit(db, actor=admin.email, action="plan.create", target=body.name)
    db.commit()
    db.refresh(plan)
    return plan


@router.patch("/{plan_id}", response_model=PlanOut)
def patch_plan(plan_id: str, body: PlanUpdate, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(plan, k, v)
    write_audit(db, actor=admin.email, action="plan.update", target=plan.id, metadata=data)
    db.commit()
    db.refresh(plan)
    return plan
