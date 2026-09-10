# Engyne — Project Context

Living procedure and change log. Update after every phase and meaningful change.

## Mission

Engyne is a professional multi-tenant B2B automation platform. The customer-facing product is a Chrome extension on the customer's IndiaMART seller session. The web app is an internal Admin Control Center only (no customer dashboard).

## MVP Definition of Done

| Step | Status |
|------|--------|
| Admin creates customer | done |
| Payment recorded/verified | done |
| Plan assigned | done |
| Setup key generated | done |
| Invoice generated + emailed | done (console email in dev) |
| Extension pairs via setup key | done |
| Save Training + versioned config | done |
| Local BUY/SKIP + score + reasons | done |
| Lead events under correct tenant | done |
| Daily report email + admin BCC | done |
| Subscription/entitlement controls access | done |
| Admin views customers/payments/invoices/devices/leads/reports | done |

## Current Phase / Status

| Phase | Name | Status |
|-------|------|--------|
| 0 | Foundation + project_context | **completed** |
| 1 | Database + admin auth + tenant model | **completed** |
| 2 | Admin APIs + wire Lovable UI | **completed** |
| 3 | Setup keys + devices + extension auth | **completed** |
| 4 | Extension shell + Save Training | **completed** |
| 5 | Scanner + rule engine + scoring | **completed** |
| 6 | Lead events + usage + admin activity | **completed** |
| 7 | Daily reports + email | **completed** |
| 8 | Razorpay + webhooks + entitlements | **completed** |
| 9 | Invoice PDF + email | **completed** |
| 10 | Security, tests, observability, deploy | **completed** |

## Architecture Snapshot

```
Martpilot/
  project_context.md
  backend/                    # FastAPI + SQLAlchemy + Alembic + APScheduler worker
  extension/                  # Chrome MV3 (local rule engine)
  martpilot-operations-hub/   # Lovable admin UI wired to Engyne API
```

**Stack:** FastAPI, SQLAlchemy 2, Alembic, SQLite (local) / **Supabase Postgres**, Render Docker deploy, APScheduler, ReportLab PDF, Razorpay SDK, console/SMTP email, Chrome MV3, TanStack Start admin.

## Entity Checklist

| Entity | Status |
|--------|--------|
| admins | done |
| customers | done |
| plans | done |
| subscriptions | done |
| payments | done |
| setup_keys | done |
| devices | done |
| automation_configs | done |
| lead_events | done |
| daily_reports | done |
| invoices | done |
| admin_notes | done |
| webhook_events | done |
| audit_logs | done |

## API Checklist

| Area | Status |
|------|--------|
| Admin auth login/logout/me | done |
| Customers / plans / payments | done |
| Invoices preview/create/send | done |
| Devices / setup keys | done |
| Extension pair / config / heartbeat / lead-event / entitlements | done |
| Reports list/resend/run | done |
| Razorpay webhooks | done |

## Cursor / Product Rules

- Preserve multi-tenancy; never shortcut to single tenant.
- No customer dashboard.
- Setup keys are pairing-only, not permanent API credentials.
- No secrets in extension; no raw tokens in admin UI or logs.
- BUY/SKIP decisions run locally in the extension.
- Prefer safe SKIP when IndiaMART DOM is uncertain.
- Derive tenant from authenticated context, never blind client input.

## Environment Variables Index

See `backend/.env.example`. Admin: `VITE_ENGYNE_API_URL`. Default admin after seed: `admin@engyne.example` / `changeme123`.

## Local run

```bash
# Backend (Python 3.12 recommended)
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Admin
cd martpilot-operations-hub
bun install   # or npm
bun run dev

# Extension: chrome://extensions → Load unpacked → extension/
```

## Known Gaps / Next Steps

- Paste Supabase `DATABASE_URL` into local `.env` and Render env (see `backend/DEPLOY.md`).
- Push repo → Render Blueprint deploy (`render.yaml`).
- Point admin `VITE_ENGYNE_API_URL` + extension `apiBase` at Render URL.
- Replace console email with production transactional provider.
- Harden IndiaMART selectors against live DOM changes.
- Chrome Web Store packaging and production Razorpay keys.
- Multiple admin roles (architecture ready via `Admin.role`).

## Change Log

### 2026-09-09 — Supabase connected
- Connected via pooler `aws-0-ap-southeast-1.pooler.supabase.com:6543` (direct `db.*` is IPv6-only).
- Fixed `@` in DB password via URL encoding / parts builder; disabled prepared statements for PgBouncer.
- Seeded admin + STARTER/PRO plans on Supabase; local API `/health` + admin login verified.

### 2026-09-09 — Phase 0
- Created `project_context.md`.
- Scaffolded `backend/` with FastAPI, settings, health, Alembic stub, `.env.example`, README.

### 2026-09-09 — Phase 1
- Added all SQLAlchemy models (customers, plans, subscriptions, payments, setup_keys, devices, automation_configs, lead_events, daily_reports, invoices, admin_notes, webhook_events, audit_logs, admins).
- Admin JWT auth + `EntitlementService` stub.
- Seed script for admin + STARTER/PRO plans.

### 2026-09-09 — Phase 2
- Admin CRUD APIs for customers, plans, payments; audit logging.
- Wired Lovable hub via `engyne-api.ts` + `connected-pages.tsx` + login gate.

### 2026-09-09 — Phase 3
- Setup key generate/revoke (hash-at-rest, raw once).
- `POST /api/extension/pair`, device enable/disable/reset, heartbeat, entitlements, config get/put.

### 2026-09-09 — Phase 4–5
- MV3 extension: popup pairing, options Save Training, auto-refresh alarms.
- Scanner adapters + deterministic rule engine + scoring (local BUY/SKIP).

### 2026-09-09 — Phase 6–7
- Lead-event idempotency by tenant+lead_hash.
- Daily report worker + `EmailService` (console/SMTP) + admin resend/run.

### 2026-09-09 — Phase 8–9
- Razorpay order helper + signed webhook idempotency → payment/subscription update.
- Invoice tax/PDF (ReportLab) + email send; one invoice per payment.

### 2026-09-09 — Phase 10
- CORS, rate limit middleware, DEPLOY.md, pytest suite (5 passed: tax, entitlements, E2E admin→pair→config→lead→invoice, tenant isolation, webhook idempotency).
