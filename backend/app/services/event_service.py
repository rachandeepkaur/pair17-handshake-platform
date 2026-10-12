from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.models.event import Event
from app.models.registration import Registration
from app.schemas.event import EventCreate, EventOut, RegistrationOut
from app.schemas.student import StudentSummary


def _to_out(event: Event, registration_count: int) -> EventOut:
    return EventOut.model_validate(event).model_copy(update={"registration_count": registration_count})


def create_event(db: Session, company_id: int, payload: EventCreate) -> EventOut:
    event = Event(company_id=company_id, **payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return _to_out(event, 0)


def get_owned_event(db: Session, company_id: int, event_id: int) -> Event:
    event = db.get(Event, event_id)
    if event is None or event.company_id != company_id:
        raise NotFoundError("Event not found")
    return event


def get_event_out(db: Session, company_id: int, event_id: int) -> EventOut:
    event = get_owned_event(db, company_id, event_id)
    count = db.scalar(select(func.count(Registration.id)).where(Registration.event_id == event.id))
    return _to_out(event, count)


def list_company_events(db: Session, company_id: int) -> list[EventOut]:
    counts = (
        select(Registration.event_id, func.count(Registration.id).label("n"))
        .group_by(Registration.event_id)
        .subquery()
    )
    rows = db.execute(
        select(Event, func.coalesce(counts.c.n, 0))
        .outerjoin(counts, counts.c.event_id == Event.id)
        .where(Event.company_id == company_id)
        .order_by(Event.event_date, Event.event_time)
    ).all()
    return [_to_out(event, count) for event, count in rows]


def list_registrations(db: Session, company_id: int, event_id: int) -> list[RegistrationOut]:
    get_owned_event(db, company_id, event_id)
    rows = db.scalars(
        select(Registration)
        .options(joinedload(Registration.student))
        .where(Registration.event_id == event_id)
        .order_by(Registration.registered_at.desc())
    ).all()
    return [
        RegistrationOut(
            id=row.id,
            registered_at=row.registered_at,
            student=StudentSummary.model_validate(row.student),
        )
        for row in rows
    ]


def count_upcoming_events(db: Session, company_id: int) -> int:
    return db.scalar(
        select(func.count(Event.id)).where(Event.company_id == company_id, Event.event_date >= date.today())
    )


def count_registrations(db: Session, company_id: int) -> int:
    return db.scalar(
        select(func.count(Registration.id))
        .join(Event, Event.id == Registration.event_id)
        .where(Event.company_id == company_id)
    )
