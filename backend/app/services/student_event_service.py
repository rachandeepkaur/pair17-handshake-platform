from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.company import Company
from app.models.event import Event
from app.models.registration import Registration
from app.schemas.student_event import StudentEventOut, StudentRegistrationOut


def _event_out(event: Event, company: Company, registration_id: int | None) -> StudentEventOut:
    return StudentEventOut(
        id=event.id,
        name=event.name,
        description=event.description,
        event_date=event.event_date,
        event_time=event.event_time,
        location=event.location,
        eligibility=event.eligibility,
        company_name=company.company_name,
        company_location=company.location,
        registered=registration_id is not None,
    )


def _event_query(student_id: int):
    return (
        select(Event, Company, Registration.id)
        .join(Company, Company.account_id == Event.company_id)
        .outerjoin(
            Registration,
            and_(Registration.event_id == Event.id, Registration.student_id == student_id),
        )
    )


def list_events(db: Session, student_id: int) -> list[StudentEventOut]:
    rows = db.execute(
        _event_query(student_id)
        .where(Event.event_date >= date.today())
        .order_by(Event.event_date, Event.event_time, Event.id)
    ).all()
    return [_event_out(event, company, registration_id) for event, company, registration_id in rows]


def get_event(db: Session, student_id: int, event_id: int) -> StudentEventOut:
    row = db.execute(
        _event_query(student_id).where(Event.id == event_id, Event.event_date >= date.today())
    ).one_or_none()
    if row is None:
        raise NotFoundError("Event not found")
    event, company, registration_id = row
    return _event_out(event, company, registration_id)


def register_for_event(db: Session, student_id: int, event_id: int) -> StudentRegistrationOut:
    event = db.scalar(select(Event).where(Event.id == event_id, Event.event_date >= date.today()))
    if event is None:
        raise NotFoundError("Event not found")
    existing = db.scalar(
        select(Registration.id).where(Registration.event_id == event_id, Registration.student_id == student_id)
    )
    if existing is not None:
        raise ConflictError("You are already registered for this event")

    registration = Registration(student_id=student_id, event_id=event_id)
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return _registration_out(db, student_id, registration)


def _registration_out(db: Session, student_id: int, registration: Registration) -> StudentRegistrationOut:
    row = db.execute(_event_query(student_id).where(Event.id == registration.event_id)).one()
    event, company, registration_id = row
    return StudentRegistrationOut(
        id=registration.id,
        registered_at=registration.registered_at,
        event=_event_out(event, company, registration_id),
    )


def list_registrations(db: Session, student_id: int) -> list[StudentRegistrationOut]:
    rows = db.execute(
        select(Registration, Event, Company)
        .join(Event, Event.id == Registration.event_id)
        .join(Company, Company.account_id == Event.company_id)
        .where(Registration.student_id == student_id)
        .order_by(Event.event_date, Event.event_time, Registration.id)
    ).all()
    return [
        StudentRegistrationOut(
            id=registration.id,
            registered_at=registration.registered_at,
            event=_event_out(event, company, registration.id),
        )
        for registration, event, company in rows
    ]
