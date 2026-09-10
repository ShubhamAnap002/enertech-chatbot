"""Normalize DATABASE_URL for SQLAlchemy + Supabase/Render Postgres."""

from __future__ import annotations

from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse


def build_database_url_from_parts(
    *,
    user: str,
    password: str,
    host: str,
    port: str | int,
    dbname: str,
) -> str:
    """Build a URL with a safely encoded password (handles @, #, etc.)."""
    user_q = quote(user or "postgres", safe="")
    pass_q = quote(password or "", safe="")
    host = (host or "").strip()
    port = str(port or "5432")
    dbname = (dbname or "postgres").strip() or "postgres"
    return f"postgresql+psycopg://{user_q}:{pass_q}@{host}:{port}/{dbname}?sslmode=require"


def normalize_database_url(url: str) -> str:
    """
    Accepts common forms:
    - sqlite:///./engyne.db
    - postgresql://... (Supabase / Render)
    - postgres://...
    - postgresql+psycopg://...

    Ensures:
    - SQLAlchemy dialect uses psycopg3: postgresql+psycopg://
    - Supabase/hosted Postgres gets sslmode=require when missing
    """
    raw = (url or "").strip()
    if not raw:
        return "sqlite:///./engyne.db"

    if raw.startswith("sqlite:"):
        return raw

    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://") :]

    if raw.startswith("postgresql://"):
        raw = "postgresql+psycopg://" + raw[len("postgresql://") :]

    if not raw.startswith("postgresql+psycopg://"):
        return raw

    parsed = urlparse(raw)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    host = (parsed.hostname or "").lower()
    if "supabase.co" in host or "supabase.com" in host or "render.com" in host:
        query.setdefault("sslmode", "require")

    return urlunparse(parsed._replace(query=urlencode(query)))


def resolve_database_url(
    database_url: str,
    *,
    supabase_db_host: str = "",
    supabase_db_password: str = "",
    supabase_db_user: str = "postgres",
    supabase_db_port: str = "5432",
    supabase_db_name: str = "postgres",
) -> str:
    """
    Prefer composing from discrete Supabase DB parts when present so passwords
    with special characters (e.g. @) do not break the URI.
    """
    host = (supabase_db_host or "").strip()
    password = (supabase_db_password or "").strip()
    if host and password and password not in {"PASTE_DB_PASSWORD_HERE", "[DB-PASSWORD]"}:
        return build_database_url_from_parts(
            user=supabase_db_user or "postgres",
            password=password,
            host=host,
            port=supabase_db_port or "5432",
            dbname=supabase_db_name or "postgres",
        )
    return normalize_database_url(database_url)
