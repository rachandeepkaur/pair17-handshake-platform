"""The JSON envelope every event carries on the wire.

{"event_id": "<uuid>", "event_type": "<topic>", "schema_version": 1,
 "occurred_at": "<ISO-8601 UTC>", "source": "p17-<service>", "key": "<entity id>",
 "data": {...}}

`event_id` identifies one business event; consumers use it (or a business key)
to make their writes idempotent. `key` is also the Kafka message key, so all
events for one entity land on the same partition, in order.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    event_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    schema_version: int = 1
    occurred_at: datetime
    source: str = Field(min_length=1)
    key: str = Field(min_length=1)
    data: dict[str, Any]


def new_event(event_type: str, key: str | int, data: dict[str, Any], source: str) -> EventEnvelope:
    return EventEnvelope(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        occurred_at=datetime.now(timezone.utc),
        source=source,
        key=str(key),
        data=data,
    )


def encode(event: EventEnvelope) -> bytes:
    return event.model_dump_json().encode("utf-8")


def decode(raw: bytes | str | None) -> EventEnvelope:
    """Parse and validate one message value. Raises ValueError on anything malformed."""

    if raw is None:
        raise ValueError("message has no value")
    text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"value is not JSON: {exc.msg}") from exc
    return EventEnvelope.model_validate(payload)
