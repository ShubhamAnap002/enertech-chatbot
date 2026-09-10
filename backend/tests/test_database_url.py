from app.core.database_url import normalize_database_url


def test_sqlite_passthrough():
    assert normalize_database_url("sqlite:///./engyne.db") == "sqlite:///./engyne.db"


def test_postgres_scheme_upgrade():
    url = normalize_database_url("postgresql://user:pass@localhost:5432/engyne")
    assert url.startswith("postgresql+psycopg://")


def test_supabase_adds_sslmode():
    url = normalize_database_url(
        "postgresql://postgres.abc:secret@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
    )
    assert "postgresql+psycopg://" in url
    assert "sslmode=require" in url


def test_postgres_short_scheme():
    url = normalize_database_url("postgres://user:pass@host:5432/db")
    assert url.startswith("postgresql+psycopg://")
