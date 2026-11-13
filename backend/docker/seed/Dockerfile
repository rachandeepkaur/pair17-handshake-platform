# syntax=docker/dockerfile:1
# One-shot jobs for the data layer:
#   docker compose --profile seed run --rm p17-db-seed          # demo data -> MongoDB
#   docker compose --profile migrate run --rm p17-db-migrate    # Lab 1 MySQL -> MongoDB
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app/backend
COPY docker/requirements-base.txt docker/seed/requirements.txt /tmp/requirements/
RUN pip install -r /tmp/requirements/requirements.txt && rm -rf /tmp/requirements

COPY app ./app
COPY db ./db

ENTRYPOINT ["python", "db/seed/generate_seed.py"]
