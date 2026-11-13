"""Consumer loop shared by the Kafka workers.

Delivery guarantees (at-least-once, made effectively-once by idempotent handlers):

1. Offsets are committed manually, and only AFTER the handler's MongoDB write
   succeeded (or the message was parked in the dead-letter topic). A worker that
   dies mid-message never committed it, so the group re-delivers it on restart:
   nothing is lost, and the handler's idempotent write absorbs the replay.
2. A message that keeps failing is retried a bounded number of times
   (WORKER_MAX_ATTEMPTS, exponential backoff), then copied to "<topic>.dlq" with
   headers describing the failure, and its offset is committed so the partition
   keeps moving.
3. Infrastructure outages (MongoDB unreachable) are not the message's fault: the
   worker waits and retries the same message without dead-lettering it.
"""

import logging
import os
import signal
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pymongo.errors import ConnectionFailure

from app.config import settings
from app.events.envelope import EventEnvelope, decode
from app.events.topics import dead_letter_topic

Handler = Callable[[EventEnvelope], str]  # returns "processed" or "duplicate"

TRANSIENT_ERRORS: tuple[type[BaseException], ...] = (ConnectionFailure,)

logger = logging.getLogger("p17.worker")


@dataclass(frozen=True)
class Outcome:
    status: str  # "processed" | "duplicate" | "dead_letter"
    attempts: int
    event_id: str | None = None
    error: str | None = None


def process_with_retries(
    value: bytes | None,
    handler: Handler,
    *,
    max_attempts: int,
    backoff_seconds: float,
    sleep: Callable[[float], None] = time.sleep,
    context: str = "",
) -> Outcome:
    """Decode and handle one message, retrying failures up to max_attempts.

    Transient infrastructure errors propagate to the caller, which retries the
    same message without counting attempts or dead-lettering it.
    """

    last_error = "unknown error"
    event_id = None
    for attempt in range(1, max_attempts + 1):
        try:
            event = decode(value)
            event_id = event.event_id
            status = handler(event)
            return Outcome(status=status, attempts=attempt, event_id=event_id)
        except TRANSIENT_ERRORS:
            raise
        except Exception as exc:  # noqa: BLE001 - any handler failure is retried, then dead-lettered
            last_error = f"{type(exc).__name__}: {exc}"[:500]
            logger.warning("%s attempt %d/%d failed: %s", context, attempt, max_attempts, last_error)
            if attempt < max_attempts:
                sleep(backoff_seconds * 2 ** (attempt - 1))
    return Outcome(status="dead_letter", attempts=max_attempts, event_id=event_id, error=last_error)


def _heartbeat() -> None:
    Path(settings.worker_heartbeat_file).write_text(str(time.time()))


def configure_logging(worker: str) -> None:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format=f"%(asctime)s %(levelname)s [{worker}] %(message)s",
    )
    logging.getLogger("pymongo").setLevel(logging.WARNING)


def run_worker(worker: str, topics: tuple[str, ...], build_handler: Callable[[Any], Handler]) -> None:
    """Consume `topics` as consumer group p17-<worker> until SIGTERM/SIGINT."""

    from confluent_kafka import Consumer, KafkaException, Producer
    from pymongo import MongoClient

    configure_logging(worker)
    group = f"p17-{worker}"
    mongo = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)
    handler = build_handler(mongo[settings.mongo_db])

    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "group.id": group,
            "client.id": f"{group}-{os.getpid()}",
            "enable.auto.commit": False,  # commit only after the database write
            "auto.offset.reset": "earliest",
            "max.poll.interval.ms": 300000,
        }
    )
    dlq_producer = Producer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "client.id": f"{group}-dlq",
            "acks": "all",
            "enable.idempotence": True,
        }
    )

    running = True

    def stop(signum: int, _frame: Any) -> None:
        nonlocal running
        logger.info("received signal %d, finishing the current message and stopping", signum)
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    consumer.subscribe(list(topics))
    logger.info("consumer group %s subscribed to %s", group, ", ".join(topics))
    _heartbeat()

    while running:
        _heartbeat()
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            logger.error("consumer error: %s", msg.error())
            continue

        key = msg.key().decode("utf-8", "replace") if msg.key() else None
        where = f"{msg.topic()}[{msg.partition()}]@{msg.offset()} key={key}"
        logger.info("received %s", where)

        while True:
            try:
                outcome = process_with_retries(
                    msg.value(),
                    handler,
                    max_attempts=settings.worker_max_attempts,
                    backoff_seconds=settings.worker_retry_backoff_seconds,
                    context=where,
                )
                break
            except TRANSIENT_ERRORS as exc:
                logger.error("%s: MongoDB unavailable (%s); retrying in 5s without committing", where, exc)
                _heartbeat()
                time.sleep(5)

        if outcome.status == "dead_letter":
            dlq = dead_letter_topic(msg.topic())
            headers = [
                ("x-original-topic", msg.topic().encode()),
                ("x-original-partition", str(msg.partition()).encode()),
                ("x-original-offset", str(msg.offset()).encode()),
                ("x-error", (outcome.error or "").encode()),
                ("x-attempts", str(outcome.attempts).encode()),
                ("x-failed-at", datetime.now(timezone.utc).isoformat().encode()),
                ("x-consumer-group", group.encode()),
            ]
            dlq_producer.produce(dlq, key=msg.key(), value=msg.value(), headers=headers)
            if dlq_producer.flush(10):
                # Not parked yet: do not commit, so the message is retried after a restart.
                raise KafkaException(f"could not write {where} to {dlq}")
            logger.error("%s moved to %s after %d attempts: %s", where, dlq, outcome.attempts, outcome.error)
        elif outcome.status == "duplicate":
            logger.info("%s event_id=%s already applied; skipped (idempotent)", where, outcome.event_id)
        else:
            logger.info("%s event_id=%s written to MongoDB", where, outcome.event_id)

        if settings.worker_pause_after_write_seconds > 0 and outcome.status != "dead_letter":
            logger.info(
                "DEMO: write done, pausing %.0fs BEFORE committing the offset (kill the worker now)",
                settings.worker_pause_after_write_seconds,
            )
            time.sleep(settings.worker_pause_after_write_seconds)

        consumer.commit(message=msg, asynchronous=False)
        logger.info("committed offset %d for %s[%d]", msg.offset() + 1, msg.topic(), msg.partition())

    consumer.close()
    dlq_producer.flush(5)
    mongo.close()
    logger.info("stopped cleanly")


def heartbeat_is_fresh(max_age_seconds: float = 60.0) -> bool:
    """Used by the container health check."""

    try:
        return time.time() - float(Path(settings.worker_heartbeat_file).read_text()) < max_age_seconds
    except (OSError, ValueError):
        return False
