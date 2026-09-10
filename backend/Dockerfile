FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Render sets PORT; default for local docker run
ENV PORT=8000

CMD ["sh", "-c", "python -m app.scripts.seed_admin && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
