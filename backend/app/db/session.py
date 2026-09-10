from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.database_url import resolve_database_url

DATABASE_URL = resolve_database_url(
    settings.database_url,
    supabase_db_host=settings.supabase_db_host,
    supabase_db_password=settings.supabase_db_password,
    supabase_db_user=settings.supabase_db_user,
    supabase_db_port=settings.supabase_db_port,
    supabase_db_name=settings.supabase_db_name,
)

connect_args: dict = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif "postgresql" in DATABASE_URL:
    # Required for Supabase transaction pooler (PgBouncer) — disables prepared statements
    connect_args = {"prepare_threshold": None}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    future=True,
    pool_pre_ping=True,
)

if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ARG001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
