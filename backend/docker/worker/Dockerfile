# syntax=docker/dockerfile:1
# Pair 17 Kafka worker image. One image, three consumers, selected by the command:
#   python -m app.workers.application_worker | event_worker | job_worker
# Build context: backend/   ->   docker build -f docker/worker/Dockerfile -t p17-kafka-worker backend
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY docker/worker/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

RUN useradd --system --uid 10017 --no-create-home p17

# Only the packages the workers import.
COPY app/__init__.py app/config.py ./app/
COPY app/events ./app/events
COPY app/workers ./app/workers

USER p17

# Healthy while the consumer loop keeps writing its heartbeat (at least once a minute).
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
  CMD ["python", "-m", "app.workers.healthcheck"]

CMD ["python", "-m", "app.workers.application_worker"]
