# syntax=docker/dockerfile:1
# Pair 17 Company service: login, company profile, team, messages, dashboards.
# Build context: backend/   ->   docker build -f docker/company/Dockerfile -t p17-company-service backend
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SERVICE_NAME=company \
    PORT=9172

WORKDIR /app

# Dependencies first so code edits do not invalidate the pip layer.
COPY docker/requirements-base.txt docker/company/requirements.txt /tmp/requirements/
RUN pip install -r /tmp/requirements/requirements.txt && rm -rf /tmp/requirements

RUN useradd --system --uid 10017 --no-create-home p17 \
 && mkdir -p /app/uploads/resumes /app/uploads/profile_pictures \
 && chown -R p17:p17 /app/uploads

# Code stays root-owned (read-only to the service user); only uploads are writable.
COPY app ./app

USER p17
EXPOSE 9172

# GET /health returns 503 unless MySQL, MongoDB, and Kafka are reachable; urlopen raises on it.
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
  CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ['PORT'], timeout=4)"]

CMD ["sh", "-c", "exec uvicorn app.entrypoints.company_service:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
