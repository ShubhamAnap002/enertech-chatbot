from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import utcnow
from app.models.customer import Customer
from app.models.daily_report import DailyReport
from app.models.device import Device
from app.models.lead_event import LeadEvent
from app.services.email import EmailService
from app.services.entitlements import EntitlementService

logger = logging.getLogger(__name__)


def _html_report(customer: Customer, report: DailyReport, purchased: list[LeadEvent], admin_extra: str) -> str:
    rows = "".join(
        f"<tr><td>{e.title}</td><td>{e.capacity}</td><td>{e.score}</td><td>{e.reason}</td></tr>" for e in purchased
    )
    return f"""
    <html><body>
    <h2>Engyne Daily Report — {report.report_date.isoformat()}</h2>
    <p>Hello {customer.contact_name},</p>
    <p>Summary for <strong>{customer.company_name}</strong>:</p>
    <ul>
      <li>Scanned: {report.scanned}</li>
      <li>Matched: {report.matched}</li>
      <li>Bought: {report.bought}</li>
      <li>Skipped: {report.skipped}</li>
      <li>Average score: {report.average_score:.1f}</li>
    </ul>
    <h3>Purchased leads</h3>
    <table border="1" cellpadding="6" cellspacing="0">
      <tr><th>Title</th><th>Capacity</th><th>Score</th><th>Reason</th></tr>
      {rows or "<tr><td colspan='4'>None</td></tr>"}
    </table>
    {admin_extra}
    <p>— Engyne</p>
    </body></html>
    """


def generate_and_send_daily_reports(db: Session, report_day: date | None = None) -> int:
    day = report_day or (datetime.now(timezone.utc).date() - timedelta(days=1))
    start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    email = EmailService()
    sent = 0

    tenants = [r[0] for r in db.query(LeadEvent.tenant_id).filter(LeadEvent.created_at >= start, LeadEvent.created_at < end).distinct()]
    # Also include active customers with entitlements even if zero events
    customers = db.query(Customer).filter(Customer.status == "active").all()
    tenant_set = {c.tenant_id for c in customers} | set(tenants)

    for tenant_id in tenant_set:
        customer = db.query(Customer).filter(Customer.tenant_id == tenant_id).first()
        if not customer:
            continue
        ents = EntitlementService.for_tenant(db, tenant_id)
        if not ents.get("daily_reports", True):
            continue

        existing = (
            db.query(DailyReport).filter(DailyReport.tenant_id == tenant_id, DailyReport.report_date == day).first()
        )
        if existing and existing.status == "sent":
            continue

        events = (
            db.query(LeadEvent)
            .filter(LeadEvent.tenant_id == tenant_id, LeadEvent.created_at >= start, LeadEvent.created_at < end)
            .all()
        )
        bought_events = [e for e in events if e.action.upper() in {"BUY", "BOUGHT"}]
        skipped = [e for e in events if e.action.upper() == "SKIP"]
        matched = [e for e in events if e.score and e.score > 0]
        avg = float(sum(e.score for e in events) / len(events)) if events else 0.0

        report = existing or DailyReport(tenant_id=tenant_id, report_date=day)
        report.scanned = len(events)
        report.matched = len(matched)
        report.bought = len(bought_events)
        report.skipped = len(skipped)
        report.average_score = avg
        report.customer_email = customer.email
        report.admin_email = settings.admin_report_email
        report.status = "queued"
        if not existing:
            db.add(report)
        db.flush()

        devices = db.query(Device).filter(Device.tenant_id == tenant_id).all()
        admin_extra = (
            f"<h3>Admin copy</h3><ul>"
            f"<li>Tenant: {tenant_id}</li>"
            f"<li>Plan: {ents.get('plan_name')}</li>"
            f"<li>Devices: {len(devices)}</li>"
            f"<li>Extension versions: {', '.join(sorted({d.extension_version or '-' for d in devices}))}</li>"
            f"</ul>"
        )
        html = _html_report(customer, report, bought_events, admin_extra)
        result = email.send(
            to=customer.email,
            subject=f"Engyne Daily Report — {day.isoformat()}",
            html=html,
            bcc=settings.admin_report_email,
        )
        if result.status == "sent":
            report.status = "sent"
            report.sent_at = utcnow()
            report.provider_message_id = result.provider_message_id
            sent += 1
        else:
            report.status = "failed"
            report.failure_reason = result.error or "send_failed"
        db.commit()
    return sent
