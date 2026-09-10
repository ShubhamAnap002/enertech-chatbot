# Engyne Backend

FastAPI multi-tenant API for Engyne Admin Control Center and Chrome extension.

## Quick start

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python -m app.scripts.seed_admin
uvicorn app.main:app --reload --port 8000
```

Health: `GET http://localhost:8000/health`

API docs: `http://localhost:8000/docs`

## Layout

```
app/
  main.py
  core/          # settings, security, logging
  db/            # session, base
  models/
  schemas/
  api/admin/
  api/extension/
  services/      # entitlements, email, invoices, razorpay
  workers/       # daily reports scheduler
```
