"""Seed default admin and starter plans."""

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app import db as _models  # noqa: F401
from app.models.admin import Admin
from app.models.plan import Plan
from app.services.entitlements import DEFAULT_ENTITLEMENTS


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.email == settings.admin_email.lower()).first()
        if not admin:
            db.add(
                Admin(
                    email=settings.admin_email.lower(),
                    password_hash=hash_password(settings.admin_password),
                    name="Engyne Admin",
                    role="admin",
                )
            )
            print(f"Created admin {settings.admin_email}")
        else:
            print("Admin already exists")

        if not db.query(Plan).filter(Plan.name == "STARTER").first():
            db.add(
                Plan(
                    name="STARTER",
                    price=4999,
                    currency="INR",
                    billing_period="monthly",
                    entitlement_config={
                        **DEFAULT_ENTITLEMENTS,
                        "max_daily_buys": 30,
                        "max_keywords": 10,
                        "max_locations": 10,
                        "advanced_rules": False,
                    },
                    description="Starter automation plan",
                )
            )
        if not db.query(Plan).filter(Plan.name == "PRO").first():
            db.add(
                Plan(
                    name="PRO",
                    price=9999,
                    currency="INR",
                    billing_period="monthly",
                    entitlement_config={
                        **DEFAULT_ENTITLEMENTS,
                        "max_daily_buys": 100,
                        "max_keywords": 40,
                        "max_locations": 40,
                        "advanced_rules": True,
                        "max_devices": 2,
                    },
                    description="Pro automation plan",
                )
            )
        db.commit()
        print("Seed complete")
    finally:
        db.close()


if __name__ == "__main__":
    main()
