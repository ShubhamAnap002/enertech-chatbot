"""Import all models so Alembic and metadata see them."""

from app.models.admin import Admin  # noqa: F401
from app.models.admin_note import AdminNote  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.automation_config import AutomationConfig  # noqa: F401
from app.models.customer import Customer  # noqa: F401
from app.models.daily_report import DailyReport  # noqa: F401
from app.models.device import Device  # noqa: F401
from app.models.invoice import Invoice  # noqa: F401
from app.models.lead_event import LeadEvent  # noqa: F401
from app.models.payment import Payment  # noqa: F401
from app.models.plan import Plan  # noqa: F401
from app.models.setup_key import SetupKey  # noqa: F401
from app.models.subscription import Subscription  # noqa: F401
from app.models.webhook_event import WebhookEvent  # noqa: F401
