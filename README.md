# Engyne / MartPilot

Multi-tenant IndiaMART automation platform.

## Layout

| Path | Role |
|------|------|
| `backend/` | FastAPI API (Supabase Postgres) |
| `extension/` | Chrome MV3 extension (customer product) |
| `martpilot-operations-hub/` | Internal Admin Control Center — **separate GitHub repo** [ShubhamAnap/martpilot-operations-hub](https://github.com/ShubhamAnap/martpilot-operations-hub) (Lovable) |
| `render.yaml` | Render Blueprint for API deploy |
| `project_context.md` | Living change log / procedure |

## Quick start (local)

See `backend/README.md`, `backend/DEPLOY.md`, and `extension/README.md`.

**Never commit** `backend/.env` (secrets).
