from datetime import date, time
from typing import Any

from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.core.activity import log_activity
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.events import producer as events, topics
from app.mongo import Doc, contains, doc, docs, next_id, today_iso, utcnow
from app.schemas.student_event import StudentEventOut, StudentRegistrationOut

OPEN_ELIGIBILITY = {"all", "all majors", "everyone"}


def _normalize_major(value: str) -> str:
    return " ".join(value.casefold().split())


def _is_eligible(eligibility: str | None, major: str | None) -> bool:
    """Match the existing eligibility text convention without changing company event data."""

    if not eligibility or not eligibility.strip():
        return True
    allowed_majors = {_normalize_major(value) for value in eligibility.split(",") if value.strip()}
    if allowed_majors & OPEN_ELIGIBILITY:
        return True
    return bool(major and _normalize_major(major) in allowed_majors)


def _student_major(db: Database, student_id: int) -> str | None:
    student = db.students.find_one({"_id": student_id}, {"major": 1})
    return student.get("major") if student else None


def _companies(db: Database, company_ids: set[int]) -> dict[int, Doc]:
    return {row.id: row for row in docs(db.companies.find({"_id": {"$in": list(company_ids)}}))}


def _registration_ids(db: Database, student_id: int, event_ids: list[int]) -> dict[int, int]:
    rows = db.registrations.find({"student_id": student_id, "event_id": {"$in": event_ids}}, {"event_id": 1})
    return {row["event_id"]: row["_id"] for row in rows}


def _event_out(event: Doc, company: Doc | None, registration_id: int | None, eligible: bool) -> StudentEventOut:
    company = company or Doc({})
    return StudentEventOut(
        id=event.id,
        name=event.name,
        description=event.description,
        event_date=event.event_date,
        event_time=event.event_time,
        location=event.location,
        eligibility=event.eligibility,
        company_name=company.company_name or event.company_name,
        company_location=company.location,
        registered=registration_id is not None,
        eligible=eligible,
    )


def _outs(db: Database, student_id: int, events: list[Doc], major: str | None) -> list[StudentEventOut]:
    companies = _companies(db, {event.company_id for event in events})
    registered = _registration_ids(db, student_id, [event.id for event in events])
    return [
        _event_out(event, companies.get(event.company_id), registered.get(event.id), _is_eligible(event.eligibility, major))
        for event in events
    ]


def list_events(
    db: Database,
    student_id: int,
    *,
    q: str | None = None,
    city: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    major: str | None = None,
    eligibility: str | None = None,
    eligible_only: bool = False,
) -> list[StudentEventOut]:
    student_major = _student_major(db, student_id)
    clauses: list[dict[str, Any]] = [{"event_date": {"$gte": max(start_date or date.today(), date.today()).isoformat()}}]
    if q:
        clauses.append({"name": contains(q)})
    if city:
        clauses.append({"location": contains(city)})
    if end_date:
        clauses.append({"event_date": {"$lte": end_date.isoformat()}})
    if major:
        clauses.append(
            {
                "$or": [
                    {"eligibility": None},
                    {"eligibility": ""},
                    {"eligibility": contains("everyone")},
                    {"eligibility": contains("all majors")},
                    {"eligibility": contains(major)},
                ]
            }
        )
    if eligibility:
        clauses.append({"eligibility": contains(eligibility)})
    events = docs(db.events.find({"$and": clauses}).sort([("event_date", 1), ("event_time", 1), ("_id", 1)]))
    outs = _outs(db, student_id, events, student_major)
    return [event for event in outs if event.eligible] if eligible_only else outs


def get_event(db: Database, student_id: int, event_id: int) -> StudentEventOut:
    event = doc(db.events.find_one({"_id": event_id, "event_date": {"$gte": today_iso()}}))
    if event is None:
        raise NotFoundError("Event not found")
    return _outs(db, student_id, [event], _student_major(db, student_id))[0]


def register_for_event(db: Database, student_id: int, event_id: int) -> StudentRegistrationOut:
    event = doc(db.events.find_one({"_id": event_id, "event_date": {"$gte": today_iso()}}))
    if event is None:
        raise NotFoundError("Event not found")
    if db.registrations.find_one({"event_id": event_id, "student_id": student_id}, {"_id": 1}):
        raise ConflictError("You are already registered for this event")

    major = _student_major(db, student_id)
    if not _is_eligible(event.eligibility, major):
        raise ForbiddenError("Your profile major does not meet this event's eligibility requirement")

    registration = {
        "_id": next_id(db, "registrations"),
        "student_id": student_id,
        "event_id": event_id,
        "company_id": event.company_id,
        "registered_at": utcnow(),
    }
    try:
        db.registrations.insert_one(registration)
    except DuplicateKeyError as exc:
        raise ConflictError("You are already registered for this event") from exc

    events.publish(
        topics.EVENT_REGISTRATION_CREATED,
        event_id,
        {
            "registration_id": registration["_id"],
            "event_id": event_id,
            "student_id": student_id,
            "company_id": event.company_id,
            "registered_at": registration["registered_at"].isoformat(),
        },
    )
    log_activity(db, student_id, "event.registered", role="student", entity_type="event", entity_id=event_id,
                 details={"registration_id": registration["_id"]})
    return StudentRegistrationOut(
        id=registration["_id"],
        registered_at=registration["registered_at"],
        event=_outs(db, student_id, [event], major)[0],
    )


def list_registrations(db: Database, student_id: int) -> list[StudentRegistrationOut]:
    major = _student_major(db, student_id)
    registrations = docs(db.registrations.find({"student_id": student_id}))
    events = {e.id: e for e in docs(db.events.find({"_id": {"$in": [r.event_id for r in registrations]}}))}
    outs = {out.id: out for out in _outs(db, student_id, list(events.values()), major)}
    rows = [
        StudentRegistrationOut(id=r.id, registered_at=r.registered_at, event=outs[r.event_id])
        for r in registrations
        if r.event_id in outs
    ]
    return sorted(rows, key=lambda row: (row.event.event_date, row.event.event_time or time.min, row.id))
