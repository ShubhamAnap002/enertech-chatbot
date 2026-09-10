"""Diagnose DATABASE_URL without printing secrets."""
from __future__ import annotations

import re

from app.core.config import settings
from app.core.database_url import normalize_database_url

url = (settings.database_url or "").strip()
print("len", len(url))
print("scheme_prefix", url.split(":", 1)[0] if url else "")
print("is_sqlite", url.startswith("sqlite"))
print("has_brackets", "[" in url or "]" in url)
print("has_space", " " in url)
print("has_angle", "<" in url or ">" in url)
print("at_count", url.count("@"))
print("still_placeholder", any(x in url for x in ("[PROJECT-REF]", "[DB-PASSWORD]", "[PASSWORD]", "[REGION]", "YOUR-PASSWORD")))

safe = re.sub(
    r"(postgresql(?:\+psycopg)?://|postgres://)([^:/?\s]+):([^@]+)@",
    r"\1\2:***@",
    url,
)
print("safe_url", safe)

try:
    norm = normalize_database_url(url)
    safe_n = re.sub(
        r"(postgresql(?:\+psycopg)?://|postgres://)([^:/?\s]+):([^@]+)@",
        r"\1\2:***@",
        norm,
    )
    print("normalize_ok", True)
    print("safe_normalized", safe_n)
except Exception as exc:
    print("normalize_ok", False)
    print("normalize_error", type(exc).__name__, str(exc))
