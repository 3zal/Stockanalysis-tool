# investr.info FastAPI (the Investr Score, search, full analysis) — the container Railway runs.
#
# Railway's service "Root Directory" is `backend`, so this file is found automatically and the
# build context is this folder only. A plain Dockerfile on purpose: the same image runs on
# Fly, DigitalOcean or a VPS, so the host stays swappable — the app talks to the fixed hostname
# api.investr.info (a CNAME), never to the host's own *.railway.app name.
#
# Build locally (needs Docker):  docker build -t investr-info-api backend
# Run locally:                   docker run --rm -p 8000:8000 investr-info-api

FROM python:3.11.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first, so this layer is cached until requirements.txt changes. Every pin in
# requirements.txt ships a manylinux wheel for CPython 3.11, so no compiler is installed.
# If a future pin ever needs one, uncomment the apt line.
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install -r requirements.txt

# Source + data/stocks.json (see .dockerignore for what is left out).
COPY . .

# database.py creates stock_analyzer.db next to main.py at startup (a cache, ephemeral on
# Railway exactly as it was on Render), so the runtime user must own /app.
RUN useradd --create-home --uid 1000 app && chown -R app:app /app
USER app

# Railway injects PORT at runtime; 8000 is only the local default.
EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
