from pymongo.database import Database

from app.core.activity import log_activity
from app.core.exceptions import NotFoundError
from app.mongo import Doc, doc, docs, encode, next_id, today_iso, utcnow
from app.schemas.event import EventCreate, EventOut, RegistrationOut
from app.services import student_service


def _to_out(event: Doc, registration_count: int) -> EventOut:
    return EventOut.model_validate(event).model_copy(update={"registration_count": registration_count})


def registration_counts(db: Database, event_ids: list[int]) -> dict[int, int]:
    rows = db.registrations.aggregate(
        [{"$match": {"event_id": {"$in": event_ids}}}, {"$group": {"_id": "$event_id", "n": {"$sum": 1}}}]
    )
    return {row["_id"]: row["n"] for row in rows}


def create_event(db: Database, company_id: int, payload: EventCreate) -> EventOut:
    company = db.companies.find_one({"_id": company_id}, {"company_name": 1})
    event_id = next_id(db, "events")
    db.events.insert_one(
        {
            "_id": event_id,
            "company_id": company_id,
            "company_name": company["company_name"] if company else None,
            **encode(payload.model_dump()),
            "created_at": utcnow(),
        }
    )
    log_activity(db, company_id, "event.created", role="company", entity_type="event", entity_id=event_id)
    return _to_out(get_owned_event(db, company_id, event_id), 0)


def get_owned_event(db: Database, company_id: int, event_id: int) -> Doc:
    event = doc(db.events.find_one({"_id": event_id}))
    if event is None or event.company_id != company_id:
        raise NotFoundError("Event not found")
    return event


def get_event_out(db: Database, company_id: int, event_id: int) -> EventOut:
    event = get_owned_event(db, company_id, event_id)
    return _to_out(event, db.registrations.count_documents({"event_id": event.id}))


def list_company_events(db: Database, company_id: int) -> list[EventOut]:
    events = docs(db.events.find({"company_id": company_id}).sort([("event_date", 1), ("event_time", 1), ("_id", 1)]))
    counts = registration_counts(db, [event.id for event in events])
    return [_to_out(event, counts.get(event.id, 0)) for event in events]


def list_registrations(db: Database, company_id: int, event_id: int) -> list[RegistrationOut]:
    get_owned_event(db, company_id, event_id)
    rows = docs(db.registrations.find({"event_id": event_id}).sort([("registered_at", -1), ("_id", -1)]))
    students = student_service.summaries_by_id(db, {row.student_id for row in rows})
    return [
        RegistrationOut(id=row.id, registered_at=row.registered_at, student=students[row.student_id])
        for row in rows
        if row.student_id in students
    ]


def count_upcoming_events(db: Database, company_id: int) -> int:
    return db.events.count_documents({"company_id": company_id, "event_date": {"$gte": today_iso()}})


def count_registrations(db: Database, company_id: int) -> int:
    return db.registrations.count_documents({"company_id": company_id})
