"""Critical unit and integration tests for Engyne backend."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import generate_setup_key, hash_password, hash_setup_key, hash_token
from app.db.base import Base, utcnow
from app.db.session import get_db
from app.main import app
from app.models.admin import Admin
from app.models.customer import Customer
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.services.entitlements import EntitlementService, DEFAULT_ENTITLEMENTS
from app.services.invoices import calculate_tax


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def _override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    # seed admin + plan
    db_session.add(
        Admin(email="admin@test.example", password_hash=hash_password("secret123"), name="Test", role="admin")
    )
    plan = Plan(
        name="PRO",
        price=9999,
        entitlement_config={**DEFAULT_ENTITLEMENTS, "max_keywords": 5, "max_devices": 1, "advanced_rules": True},
    )
    db_session.add(plan)
    db_session.commit()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_calculate_tax():
    tax, total = calculate_tax(1000)
    assert tax == 180.0
    assert total == 1180.0


def test_entitlement_validation():
    ents = {**DEFAULT_ENTITLEMENTS, "max_keywords": 2, "advanced_rules": False}
    errors = EntitlementService.validate_config_against_entitlements(
        {"keywords": ["a", "b", "c"], "locations": [], "restricted_keywords": []},
        ents,
    )
    assert "keywords exceed plan entitlement" in errors


def test_admin_login_and_customer_flow(client, db_session):
    login = client.post("/api/admin/auth/login", json={"email": "admin@test.example", "password": "secret123"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/admin/customers",
        headers=headers,
        json={
            "company_name": "Acme Solar",
            "contact_name": "Ada",
            "email": "ada@acme.example",
            "mobile": "9999999999",
        },
    )
    assert created.status_code == 200
    customer = created.json()
    tenant_id = customer["tenant_id"]

    plan = db_session.query(Plan).first()
    pay = client.post(
        "/api/admin/payments",
        headers=headers,
        json={
            "tenant_id": tenant_id,
            "plan_id": plan.id,
            "amount": 9999,
            "payment_method": "manual",
            "transaction_id": "txn_1",
            "status": "verified",
            "assign_plan": True,
        },
    )
    assert pay.status_code == 200

    key_res = client.post(
        "/api/admin/setup-keys",
        headers=headers,
        json={"tenant_id": tenant_id, "expires_hours": 24},
    )
    assert key_res.status_code == 200
    raw_key = key_res.json()["raw_key"]
    assert raw_key.startswith("engy_")

    pair = client.post(
        "/api/extension/pair",
        json={"setup_key": raw_key, "device_id": "device-abc", "extension_version": "0.1.0"},
    )
    assert pair.status_code == 200
    body = pair.json()
    assert body["connected"] is True
    assert body["tenant_id"] == tenant_id
    device_token = body["access_token"]
    assert device_token
    # raw token must not appear in admin device list
    devices = client.get("/api/admin/devices", headers=headers).json()
    assert "access_token" not in json.dumps(devices)

    cfg = {
        "keywords": ["solar", "inverter"],
        "locations": ["Pune"],
        "restricted_keywords": [],
        "auto_refresh": {"enabled": True, "interval_seconds": 30},
        "scheduler": {"enabled": False, "daily_limit": 20},
    }
    save = client.put(
        "/api/extension/config",
        headers={"Authorization": f"Bearer {device_token}"},
        json={"config": cfg},
    )
    assert save.status_code == 200
    assert save.json()["version"] == 1

    # entitlement exceed
    too_many = dict(cfg)
    too_many["keywords"] = ["a", "b", "c", "d", "e", "f"]
    bad = client.put(
        "/api/extension/config",
        headers={"Authorization": f"Bearer {device_token}"},
        json={"config": too_many},
    )
    assert bad.status_code == 400

    lead = client.post(
        "/api/extension/lead-event",
        headers={"Authorization": f"Bearer {device_token}"},
        json={
            "device_id": "device-abc",
            "lead_hash": "abc123",
            "title": "Solar Hybrid Inverter",
            "capacity": "10 kVA",
            "score": 94,
            "action": "BOUGHT",
            "reason": "Keyword + location",
        },
    )
    assert lead.status_code == 200
    dup = client.post(
        "/api/extension/lead-event",
        headers={"Authorization": f"Bearer {device_token}"},
        json={
            "device_id": "device-abc",
            "lead_hash": "abc123",
            "title": "Solar Hybrid Inverter",
            "score": 94,
            "action": "BOUGHT",
        },
    )
    assert dup.json()["duplicate"] is True

    inv = client.post(
        "/api/admin/invoices",
        headers=headers,
        json={"payment_id": pay.json()["id"]},
    )
    assert inv.status_code == 200
    send = client.post(f"/api/admin/invoices/{inv.json()['id']}/send", headers=headers)
    assert send.status_code == 200
    assert send.json()["email_status"] == "sent"


def test_tenant_isolation_on_lead_submit(client, db_session):
    # Create two tenants manually
    c1 = Customer(tenant_id="t1", company_name="A", contact_name="A", email="a@t.example")
    c2 = Customer(tenant_id="t2", company_name="B", contact_name="B", email="b@t.example")
    db_session.add_all([c1, c2])
    plan = db_session.query(Plan).first()
    db_session.add(Subscription(tenant_id="t1", plan_id=plan.id, status="active", start_at=utcnow()))
    db_session.add(Subscription(tenant_id="t2", plan_id=plan.id, status="active", start_at=utcnow()))
    from app.models.device import Device

    d1 = Device(tenant_id="t1", device_id="d1", status="active", access_token_hash=hash_token("tok1"))
    d2 = Device(tenant_id="t2", device_id="d2", status="active", access_token_hash=hash_token("tok2"))
    db_session.add_all([d1, d2])
    db_session.commit()

    r = client.post(
        "/api/extension/lead-event",
        headers={"Authorization": "Bearer tok1"},
        json={"device_id": "d1", "lead_hash": "h1", "title": "x", "action": "SKIP", "score": 1},
    )
    assert r.status_code == 200
    leads = client.get(
        "/api/admin/leads",
        headers={"Authorization": f"Bearer {client.post('/api/admin/auth/login', json={'email': 'admin@test.example', 'password': 'secret123'}).json()['access_token']}"},
    ).json()
    assert all(l["tenant_id"] != "t2" or l["lead_hash"] != "h1" for l in leads)
    assert any(l["tenant_id"] == "t1" and l["lead_hash"] == "h1" for l in leads)


def test_webhook_idempotency(client, db_session):
    from app.core.config import settings

    settings.razorpay_webhook_secret = "whsec"
    payload = {"id": "evt_1", "event": "payment.captured", "payload": {"payment": {"entity": {"id": "pay_1", "status": "captured"}}}}
    raw = json.dumps(payload).encode()
    sig = hmac.new(b"whsec", raw, hashlib.sha256).hexdigest()
    r1 = client.post("/api/webhooks/razorpay", content=raw, headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"})
    r2 = client.post("/api/webhooks/razorpay", content=raw, headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"})
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json()["duplicate"] is True
