from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SessionLocal
from app.services.reports import generate_and_send_daily_reports

_scheduler: BackgroundScheduler | None = None


def _job_daily_reports() -> None:
    db = SessionLocal()
    try:
        generate_and_send_daily_reports(db)
    finally:
        db.close()


def start_scheduler() -> None:
    global _scheduler
    if _scheduler:
        return
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(_job_daily_reports, "cron", hour=1, minute=5, id="daily_reports")
    _scheduler.start()


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
