import logging
from time import perf_counter
from typing import Any
from uuid import uuid4


logger = logging.getLogger("p17.assistant.trace")


def new_trace_id() -> str:
    return uuid4().hex


def log_timing(trace_id: str, operation: str, started_at: float, **fields: Any) -> None:
    elapsed_ms = round((perf_counter() - started_at) * 1000, 1)
    details = " ".join(f"{key}={value}" for key, value in fields.items())
    logger.info("trace_id=%s operation=%s elapsed_ms=%s %s", trace_id, operation, elapsed_ms, details)
