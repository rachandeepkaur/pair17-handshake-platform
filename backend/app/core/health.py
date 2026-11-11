"""Dependency checks behind each service's GET /health endpoint.

Every check returns a small dict and never raises, so one broken dependency
shows up in the response instead of turning the health check into a 500.
Only the standard library and drivers the service already needs are used;
pymongo is imported lazily so a service without MONGO_URI does not need it.
"""

import json
import socket
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from sqlalchemy import text

from app.config import settings
from app.database import engine

Check = dict[str, Any]


def _timed(probe: Callable[[], str | None]) -> Check:
    started = time.perf_counter()
    try:
        detail = probe()
    except Exception as exc:  # noqa: BLE001 - report any failure as "down"
        return {"status": "down", "error": f"{type(exc).__name__}: {exc}"[:300]}
    check: Check = {"status": "up", "latency_ms": round((time.perf_counter() - started) * 1000, 1)}
    if detail:
        check["detail"] = detail
    return check


def check_mysql() -> Check:
    def probe() -> None:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    return _timed(probe)


def check_mongodb() -> Check:
    def probe() -> str:
        from pymongo import MongoClient

        timeout_ms = int(settings.health_timeout_seconds * 1000)
        client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=timeout_ms, connectTimeoutMS=timeout_ms)
        try:
            client.admin.command("ping")
            return f"database={settings.mongo_db}"
        finally:
            client.close()

    return _timed(probe)


def check_kafka() -> Check:
    """TCP reachability of every bootstrap broker (no Kafka client dependency)."""

    def probe() -> str:
        brokers = [b.strip() for b in settings.kafka_bootstrap_servers.split(",") if b.strip()]
        for broker in brokers:
            host, _, port = broker.rpartition(":")
            with socket.create_connection((host, int(port)), timeout=settings.health_timeout_seconds):
                pass
        return ",".join(brokers)

    return _timed(probe)


def check_http(url: str) -> Check:
    def probe() -> str:
        try:
            with urllib.request.urlopen(url, timeout=settings.health_timeout_seconds) as response:
                return f"HTTP {response.status}"
        except urllib.error.HTTPError as exc:
            # The service answered; surface its own verdict without failing the probe on 503.
            body = exc.read().decode("utf-8", "replace")
            try:
                status = json.loads(body).get("status", "unknown")
            except ValueError:
                status = "unknown"
            raise RuntimeError(f"HTTP {exc.code} ({status})") from None

    return _timed(probe)


def run_checks(*, include_platform: bool = False, include_ollama: bool = False) -> tuple[bool, dict[str, Check]]:
    """Return (healthy, checks).

    Required: MySQL, plus MongoDB and Kafka when configured. Platform services
    and Ollama are reported but optional, so the assistant stays healthy (and
    can answer with a clear error) while a sibling restarts or Ollama is off.
    """

    required: dict[str, Check] = {"mysql": check_mysql()}
    if settings.mongo_uri:
        required["mongodb"] = check_mongodb()
    if settings.kafka_bootstrap_servers:
        required["kafka"] = check_kafka()

    optional: dict[str, Check] = {}
    if include_ollama:
        optional["ollama"] = check_http(f"{settings.ollama_host.rstrip('/')}/api/version")
    if include_platform:
        for name, base_url in settings.platform_services.items():
            optional[name] = check_http(f"{base_url}/health/live")
    for check in optional.values():
        check["required"] = False

    healthy = all(check["status"] == "up" for check in required.values())
    return healthy, {**required, **optional}
