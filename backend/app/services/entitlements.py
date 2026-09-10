from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.models.subscription import Subscription

DEFAULT_ENTITLEMENTS = {
    "max_daily_buys": 50,
    "max_keywords": 20,
    "max_locations": 20,
    "max_devices": 1,
    "advanced_rules": False,
    "daily_reports": True,
    "auto_refresh": True,
    "max_restricted_keywords": 50,
}


class EntitlementService:
    """Backend source of truth for plan entitlements. Do not hardcode plan names in callers."""

    @staticmethod
    def from_plan(plan: Plan | None) -> dict:
        base = dict(DEFAULT_ENTITLEMENTS)
        if plan and isinstance(plan.entitlement_config, dict):
            base.update(plan.entitlement_config)
        return base

    @staticmethod
    def for_tenant(db: Session, tenant_id: str) -> dict:
        sub = (
            db.query(Subscription)
            .filter(Subscription.tenant_id == tenant_id, Subscription.status.in_(["active", "trialing"]))
            .order_by(Subscription.created_at.desc())
            .first()
        )
        if not sub:
            return {**DEFAULT_ENTITLEMENTS, "access_allowed": False, "reason": "no_active_subscription"}
        plan = db.get(Plan, sub.plan_id)
        entitlements = EntitlementService.from_plan(plan)
        entitlements["access_allowed"] = True
        entitlements["plan_id"] = sub.plan_id
        entitlements["plan_name"] = plan.name if plan else ""
        entitlements["subscription_status"] = sub.status
        return entitlements

    @staticmethod
    def validate_config_against_entitlements(config: dict, entitlements: dict) -> list[str]:
        errors: list[str] = []
        keywords = config.get("keywords") or []
        locations = config.get("locations") or []
        restricted = config.get("restricted_keywords") or []
        if len(keywords) > int(entitlements.get("max_keywords", 20)):
            errors.append("keywords exceed plan entitlement")
        if len(locations) > int(entitlements.get("max_locations", 20)):
            errors.append("locations exceed plan entitlement")
        if len(restricted) > int(entitlements.get("max_restricted_keywords", 50)):
            errors.append("restricted_keywords exceed plan entitlement")
        if config.get("advanced_rules") and not entitlements.get("advanced_rules"):
            errors.append("advanced_rules not entitled")
        return errors
