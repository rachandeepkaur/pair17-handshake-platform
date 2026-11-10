# syntax=docker/dockerfile:1
# One-shot job that loads the deterministic Pair 17 demo data into MySQL.
# Run with: docker compose --profile seed run --rm p17-db-seed
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app/backend
COPY docker/requirements-base.txt /tmp/requirements/
RUN pip install -r /tmp/requirements/requirements-base.txt && rm -rf /tmp/requirements

COPY app ./app
COPY db ./db

ENTRYPOINT ["python", "db/seed/generate_seed.py"]
