from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.admin import Admin
from app.models.customer import Customer
from app.schemas.common import CustomerCreate, CustomerOut, CustomerUpdate
from app.services.audit import write_audit

router = APIRouter(prefix="/api/admin/customers", tags=["admin-customers"])


@router.get("", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    return db.query(Customer).order_by(Customer.created_at.desc()).all()


@router.post("", response_model=CustomerOut)
def create_customer(body: CustomerCreate, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    existing = db.query(Customer).filter(Customer.email == str(body.email).lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Customer email already exists")
    customer = Customer(
        tenant_id=str(uuid4()),
        company_name=body.company_name,
        contact_name=body.contact_name,
        email=str(body.email).lower(),
        mobile=body.mobile,
        alternate_mobile=body.alternate_mobile,
        gstin=body.gstin,
        website=body.website,
        business_type=body.business_type,
        country=body.country,
        state=body.state,
        city=body.city,
        billing_address=body.billing_address,
        postal_code=body.postal_code,
        status=body.status,
    )
    db.add(customer)
    write_audit(db, actor=admin.email, action="customer.create", tenant_id=customer.tenant_id, target=customer.id)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: str, db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.patch("/{customer_id}", response_model=CustomerOut)
def patch_customer(
    customer_id: str,
    body: CustomerUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    data = body.model_dump(exclude_unset=True)
    if "email" in data and data["email"]:
        data["email"] = str(data["email"]).lower()
    for k, v in data.items():
        setattr(customer, k, v)
    write_audit(db, actor=admin.email, action="customer.update", tenant_id=customer.tenant_id, target=customer.id, metadata=data)
    db.commit()
    db.refresh(customer)
    return customer
