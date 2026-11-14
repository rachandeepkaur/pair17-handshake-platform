"""Kafka topic names. Each topic has a dead-letter twin named "<topic>.dlq"."""

APPLICATION_CREATED = "application.created"
APPLICATION_UPDATED = "application.updated"
APPLICATION_STATUS_CHANGED = "application.status_changed"
EVENT_REGISTRATION_CREATED = "event.registration_created"
JOB_CREATED = "job.created"

ALL_TOPICS = (
    APPLICATION_CREATED,
    APPLICATION_UPDATED,
    APPLICATION_STATUS_CHANGED,
    EVENT_REGISTRATION_CREATED,
    JOB_CREATED,
)

DLQ_SUFFIX = ".dlq"


def dead_letter_topic(topic: str) -> str:
    return f"{topic}{DLQ_SUFFIX}"
