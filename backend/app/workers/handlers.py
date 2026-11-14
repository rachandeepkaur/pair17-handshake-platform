"""MongoDB projections built by the workers, one handler per worker.

Every write is idempotent, so a re-delivered or re-published event is harmless:
- inserts use a deterministic _id (the event_id or a business key) and treat a
  DuplicateKeyError as "already applied";
- derived values are recomputed (count_documents + $set), never incremented.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from app.events import topics
from app.events.envelope import EventEnvelope


def _now() -> datetime:
    return datetime.now(timezone.utc)


def insert_once(collection: Any, document: dict[str, Any]) -> bool:
    """Insert the document; False if one with the same _id already exists."""

    try:
        collection.insert_one(document)
        return True
    except DuplicateKeyError:
        return False


class ApplicationData(BaseModel):
    application_id: int
    job_id: int
    student_id: int
    company_id: int


class StatusChangeData(ApplicationData):
    old_status: str
    new_status: str


class RegistrationData(BaseModel):
    registration_id: int
    event_id: int
    student_id: int
    company_id: int


class JobData(BaseModel):
    job_id: int
    company_id: int
    title: str
    description: str | None = None
    category: str
    city: str
    location: str | None = None
    is_remote: bool = False
    salary: str | None = None
    skills_required: str | None = None
    posting_date: str
    deadline: str


# --------------------------------------------------------------- application worker
def build_application_handler(db: Any):
    """application.created / .updated / .status_changed -> application timeline + notifications."""

    timeline = db["application_events"]
    notifications = db["notifications"]
    timeline.create_index([("application_id", ASCENDING), ("occurred_at", ASCENDING)])
    notifications.create_index([("student_id", ASCENDING), ("created_at", ASCENDING)])

    def handle(event: EventEnvelope) -> str:
        if event.event_type not in (
            topics.APPLICATION_CREATED,
            topics.APPLICATION_UPDATED,
            topics.APPLICATION_STATUS_CHANGED,
        ):
            raise ValueError(f"unexpected event_type {event.event_type!r}")
        status_change = event.event_type == topics.APPLICATION_STATUS_CHANGED
        data = (StatusChangeData if status_change else ApplicationData).model_validate(event.data)

        wrote_timeline = insert_once(
            timeline,
            {
                "_id": event.event_id,
                "event_type": event.event_type,
                "application_id": data.application_id,
                "job_id": data.job_id,
                "student_id": data.student_id,
                "company_id": data.company_id,
                "data": event.data,
                "occurred_at": event.occurred_at,
                "processed_at": _now(),
            },
        )
        wrote_notification = False
        if status_change:
            wrote_notification = insert_once(
                notifications,
                {
                    "_id": event.event_id,
                    "student_id": data.student_id,
                    "application_id": data.application_id,
                    "message": f"Your application {data.application_id} moved from "
                    f"{data.old_status} to {data.new_status}.",
                    "read": False,
                    "created_at": _now(),
                },
            )
        return "processed" if (wrote_timeline or wrote_notification) else "duplicate"

    return handle


# --------------------------------------------------------------------- event worker
def build_event_handler(db: Any):
    """event.registration_created -> registration log + per-event registration count."""

    registrations = db["event_registrations"]
    stats = db["event_stats"]
    registrations.create_index([("event_id", ASCENDING)])

    def handle(event: EventEnvelope) -> str:
        if event.event_type != topics.EVENT_REGISTRATION_CREATED:
            raise ValueError(f"unexpected event_type {event.event_type!r}")
        data = RegistrationData.model_validate(event.data)
        # Business key: one document per registration, however many times it is published.
        inserted = insert_once(
            registrations,
            {
                "_id": f"registration-{data.registration_id}",
                "registration_id": data.registration_id,
                "event_id": data.event_id,
                "student_id": data.student_id,
                "company_id": data.company_id,
                "source_event_id": event.event_id,
                "registered_at": event.data.get("registered_at"),
                "processed_at": _now(),
            },
        )
        # Recomputed, not incremented, so a replay cannot double-count.
        count = registrations.count_documents({"event_id": data.event_id})
        stats.update_one(
            {"_id": data.event_id},
            {"$set": {"registrations": count, "updated_at": _now()}},
            upsert=True,
        )
        return "processed" if inserted else "duplicate"

    return handle


# ----------------------------------------------------------------------- job worker
def build_job_handler(db: Any):
    """job.created -> search index document per job (upsert by job_id)."""

    index = db["job_search_index"]
    index.create_index([("search_text", ASCENDING)])
    index.create_index([("city", ASCENDING), ("category", ASCENDING)])

    def handle(event: EventEnvelope) -> str:
        if event.event_type != topics.JOB_CREATED:
            raise ValueError(f"unexpected event_type {event.event_type!r}")
        data = JobData.model_validate(event.data)
        if index.find_one({"_id": data.job_id, "source_event_id": event.event_id}, {"_id": 1}):
            return "duplicate"
        search_text = " ".join(
            part.lower() for part in (data.title, data.city, data.category, data.skills_required or "") if part
        )
        index.update_one(
            {"_id": data.job_id},
            {
                "$set": {
                    **data.model_dump(),
                    "search_text": search_text,
                    "skills": [s.strip().lower() for s in (data.skills_required or "").split(",") if s.strip()],
                    "source_event_id": event.event_id,
                    "indexed_at": _now(),
                }
            },
            upsert=True,
        )
        return "processed"

    return handle
