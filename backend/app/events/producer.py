"""Publishes domain events from the API services to Kafka.

Publishing happens after the MySQL commit. If Kafka is unreachable the API call
still succeeds and the failure is logged: the database is the source of truth.
(A transactional outbox would close that gap; see RUN_LOG.txt.)

With KAFKA_BOOTSTRAP_SERVERS unset (unit tests, the local monolith) publishing
is a no-op, so confluent-kafka is only imported when it is actually used.
"""

import logging
import threading
from typing import Any

from app.config import settings
from app.events.envelope import encode, new_event

logger = logging.getLogger("p17.events")

_lock = threading.Lock()
_producer: Any = None


def _get_producer() -> Any:
    global _producer
    if _producer is None:
        with _lock:
            if _producer is None:
                from confluent_kafka import Producer

                _producer = Producer(
                    {
                        "bootstrap.servers": settings.kafka_bootstrap_servers,
                        "client.id": f"p17-{settings.service_name}-service",
                        "acks": "all",
                        "enable.idempotence": True,
                        "message.timeout.ms": 10000,
                    }
                )
    return _producer


def publish(topic: str, key: str | int, data: dict[str, Any]) -> str | None:
    """Publish one event and wait (briefly) for the broker to acknowledge it.

    Returns the event_id, or None when publishing is disabled or failed.
    """

    if not settings.kafka_bootstrap_servers:
        return None
    event = new_event(topic, key, data, source=f"p17-{settings.service_name}-service")
    errors: list[str] = []

    def on_delivery(err: Any, msg: Any) -> None:
        if err is not None:
            errors.append(str(err))
        else:
            logger.info(
                "published %s key=%s event_id=%s partition=%s offset=%s",
                topic, event.key, event.event_id, msg.partition(), msg.offset(),
            )

    try:
        producer = _get_producer()
        producer.produce(topic, key=event.key.encode(), value=encode(event), on_delivery=on_delivery)
        remaining = producer.flush(settings.kafka_publish_timeout_seconds)
    except Exception as exc:  # noqa: BLE001 - never fail the API call over Kafka
        logger.error("could not publish %s key=%s: %s", topic, event.key, exc)
        return None
    if remaining or errors:
        logger.error("publish of %s key=%s not acknowledged: %s", topic, event.key, errors or "timeout")
        return None
    return event.event_id
