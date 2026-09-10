from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminMe(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: str

    model_config = {"from_attributes": True}


class CustomerCreate(BaseModel):
    company_name: str
    contact_name: str
    email: EmailStr
    mobile: str = ""
    alternate_mobile: str = ""
    gstin: str = ""
    website: str = ""
    business_type: str = ""
    country: str = "India"
    state: str = ""
    city: str = ""
    billing_address: str = ""
    postal_code: str = ""
    status: str = "active"


class CustomerUpdate(BaseModel):
    company_name: str | None = None
    contact_name: str | None = None
    email: EmailStr | None = None
    mobile: str | None = None
    alternate_mobile: str | None = None
    gstin: str | None = None
    website: str | None = None
    business_type: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    billing_address: str | None = None
    postal_code: str | None = None
    status: str | None = None


class CustomerOut(BaseModel):
    id: str
    tenant_id: str
    company_name: str
    contact_name: str
    email: EmailStr
    mobile: str
    alternate_mobile: str
    gstin: str
    website: str
    business_type: str
    country: str
    state: str
    city: str
    billing_address: str
    postal_code: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlanCreate(BaseModel):
    name: str
    price: float = 0
    currency: str = "INR"
    billing_period: str = "monthly"
    active: bool = True
    entitlement_config: dict[str, Any] = Field(default_factory=dict)
    description: str = ""


class PlanUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    currency: str | None = None
    billing_period: str | None = None
    active: bool | None = None
    entitlement_config: dict[str, Any] | None = None
    description: str | None = None


class PlanOut(BaseModel):
    id: str
    name: str
    price: float
    currency: str
    billing_period: str
    active: bool
    entitlement_config: dict[str, Any]
    description: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentCreate(BaseModel):
    tenant_id: str
    plan_id: str | None = None
    amount: float
    currency: str = "INR"
    payment_method: str = "manual"
    transaction_id: str = ""
    status: str = "recorded"
    assign_plan: bool = True


class PaymentOut(BaseModel):
    id: str
    tenant_id: str
    subscription_id: str | None
    amount: float
    currency: str
    payment_method: str
    transaction_id: str
    provider_payment_id: str
    provider_order_id: str
    status: str
    paid_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InvoicePreviewRequest(BaseModel):
    payment_id: str


class InvoiceCreateRequest(BaseModel):
    payment_id: str
    notes: str = ""


class InvoiceOut(BaseModel):
    id: str
    tenant_id: str
    payment_id: str
    invoice_number: str
    invoice_date: datetime | Any
    subtotal: float
    tax_amount: float
    total_amount: float
    currency: str
    pdf_path: str
    status: str
    email_status: str
    sent_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SetupKeyCreate(BaseModel):
    tenant_id: str
    expires_hours: int = 72


class SetupKeyOut(BaseModel):
    id: str
    tenant_id: str
    status: str
    expires_at: datetime | None
    created_at: datetime
    raw_key: str | None = None  # only at generation time


class PairRequest(BaseModel):
    setup_key: str
    device_id: str
    extension_version: str = "0.1.0"


class PairResponse(BaseModel):
    connected: bool
    tenant_id: str
    device_id: str
    access_token: str
    plan: str
    entitlements: dict[str, Any]
    config_version: int


class ConfigPut(BaseModel):
    config: dict[str, Any]


class LeadEventIn(BaseModel):
    device_id: str
    lead_hash: str
    title: str = ""
    product: str = ""
    capacity: str = ""
    quantity: str = ""
    location: str = ""
    score: float = 0
    action: str
    reason: str = ""
    rule_results: dict[str, Any] = Field(default_factory=dict)
    event_timestamp: datetime | None = None


class HeartbeatIn(BaseModel):
    device_id: str
    extension_version: str = ""
    state: str = "running"
    config_version: int = 0
    runtime: dict[str, Any] = Field(default_factory=dict)
