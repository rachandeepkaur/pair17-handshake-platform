from datetime import date

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.company import Company
from app.models.event import Event
from app.models.registration import Registration
from app.models.student import Student
from app.schemas.student_event import StudentEventOut, StudentRegistrationOut

OPEN_ELIGIBILITY = {"all", "all majors", "everyone"}


def _like_pattern(value: str) -> str:
    # Treat user-provided wildcard characters as literal search text.
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


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


def _student_major(db: Session, student_id: int) -> str | None:
    return db.scalar(select(Student.major).where(Student.account_id == student_id))


def _event_out(
    event: Event,
    company: Company,
    registration_id: int | None,
    eligible: bool,
) -> StudentEventOut:
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
        eligible=eligible,
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


def list_events(
    db: Session,
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
    query = _event_query(student_id).where(Event.event_date >= max(start_date or date.today(), date.today()))
    if q:
        query = query.where(Event.name.ilike(_like_pattern(q)))
    if city:
        query = query.where(Event.location.ilike(_like_pattern(city)))
    if end_date:
        query = query.where(Event.event_date <= end_date)
    if major:
        pattern = _like_pattern(major)
        query = query.where(
            or_(
                Event.eligibility.is_(None),
                Event.eligibility == "",
                Event.eligibility.ilike("%everyone%"),
                Event.eligibility.ilike("%all majors%"),
                Event.eligibility.ilike(pattern),
            )
        )
    if eligibility:
        query = query.where(Event.eligibility.ilike(_like_pattern(eligibility)))
    rows = db.execute(query.order_by(Event.event_date, Event.event_time, Event.id)).all()
    events = [
        _event_out(event, company, registration_id, _is_eligible(event.eligibility, student_major))
        for event, company, registration_id in rows
    ]
    return [event for event in events if event.eligible] if eligible_only else events


def get_event(db: Session, student_id: int, event_id: int) -> StudentEventOut:
    major = _student_major(db, student_id)
    row = db.execute(
        _event_query(student_id).where(Event.id == event_id, Event.event_date >= date.today())
    ).one_or_none()
    if row is None:
        raise NotFoundError("Event not found")
    event, company, registration_id = row
    return _event_out(event, company, registration_id, _is_eligible(event.eligibility, major))


def register_for_event(db: Session, student_id: int, event_id: int) -> StudentRegistrationOut:
    event = db.scalar(select(Event).where(Event.id == event_id, Event.event_date >= date.today()))
    if event is None:
        raise NotFoundError("Event not found")
    existing = db.scalar(
        select(Registration.id).where(Registration.event_id == event_id, Registration.student_id == student_id)
    )
    if existing is not None:
        raise ConflictError("You are already registered for this event")

    major = _student_major(db, student_id)
    if not _is_eligible(event.eligibility, major):
        raise ForbiddenError("Your profile major does not meet this event's eligibility requirement")

    registration = Registration(student_id=student_id, event_id=event_id)
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return _registration_out(db, student_id, registration, major)


def _registration_out(
    db: Session,
    student_id: int,
    registration: Registration,
    major: str | None,
) -> StudentRegistrationOut:
    row = db.execute(_event_query(student_id).where(Event.id == registration.event_id)).one()
    event, company, registration_id = row
    return StudentRegistrationOut(
        id=registration.id,
        registered_at=registration.registered_at,
        event=_event_out(event, company, registration_id, _is_eligible(event.eligibility, major)),
    )


def list_registrations(db: Session, student_id: int) -> list[StudentRegistrationOut]:
    major = _student_major(db, student_id)
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
            event=_event_out(event, company, registration.id, _is_eligible(event.eligibility, major)),
        )
        for registration, event, company in rows
    ]
