from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import auth as admin_auth
from app.api.admin import customers as admin_customers
from app.api.admin import devices as admin_devices
from app.api.admin import invoices as admin_invoices
from app.api.admin import payments as admin_payments
from app.api.admin import plans as admin_plans
from app.api.admin import reports as admin_reports
from app.api.extension import routes as extension_routes
from app.api import webhooks
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.rate_limit import SimpleRateLimitMiddleware
from app.db.base import Base
from app.db.session import engine
from app import db as models_pkg  # noqa: F401
from app.workers.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SimpleRateLimitMiddleware, max_requests=300, window_seconds=60)

app.include_router(admin_auth.router)
app.include_router(admin_customers.router)
app.include_router(admin_plans.router)
app.include_router(admin_payments.router)
app.include_router(admin_invoices.router)
app.include_router(admin_devices.router)
app.include_router(admin_reports.router)
app.include_router(extension_routes.router)
app.include_router(webhooks.router)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}
