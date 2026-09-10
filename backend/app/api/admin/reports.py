from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.admin import Admin
from app.models.daily_report import DailyReport
from app.models.lead_event import LeadEvent
from app.services.audit import write_audit
from app.services.reports import generate_and_send_daily_reports

router = APIRouter(tags=["admin-reports-leads"])


@router.get("/api/admin/leads")
def list_leads(tenant_id: str | None = None, limit: int = 100, db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    q = db.query(LeadEvent).order_by(LeadEvent.created_at.desc())
    if tenant_id:
        q = q.filter(LeadEvent.tenant_id == tenant_id)
    rows = q.limit(min(limit, 500)).all()
    return [
        {
            "id": e.id,
            "tenant_id": e.tenant_id,
            "device_id": e.device_id,
            "lead_hash": e.lead_hash,
            "title": e.title,
            "capacity": e.capacity,
            "quantity": e.quantity,
            "location": e.location,
            "score": e.score,
            "action": e.action,
            "reason": e.reason,
            "event_timestamp": e.event_timestamp,
            "created_at": e.created_at,
        }
        for e in rows
    ]


@router.get("/api/admin/reports")
def list_reports(db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    rows = db.query(DailyReport).order_by(DailyReport.report_date.desc()).all()
    return [
        {
            "id": r.id,
            "tenant_id": r.tenant_id,
            "report_date": r.report_date,
            "scanned": r.scanned,
            "matched": r.matched,
            "bought": r.bought,
            "skipped": r.skipped,
            "average_score": r.average_score,
            "customer_email": r.customer_email,
            "admin_email": r.admin_email,
            "status": r.status,
            "sent_at": r.sent_at,
            "failure_reason": r.failure_reason,
        }
        for r in rows
    ]


@router.get("/api/admin/reports/{report_id}")
def get_report(report_id: str, db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    r = db.get(DailyReport, report_id)
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    return r


@router.post("/api/admin/reports/{report_id}/resend")
def resend_report(report_id: str, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    r = db.get(DailyReport, report_id)
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    r.status = "queued"
    db.commit()
    generate_and_send_daily_reports(db, r.report_date)
    write_audit(db, actor=admin.email, action="report.resend", tenant_id=r.tenant_id, target=r.id)
    db.commit()
    return {"ok": True}


@router.post("/api/admin/reports/run")
def run_reports(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    count = generate_and_send_daily_reports(db)
    write_audit(db, actor=admin.email, action="report.run", metadata={"sent": count})
    db.commit()
    return {"sent": count}
