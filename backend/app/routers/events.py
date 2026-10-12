from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_company
from app.models.account import Account
from app.schemas.event import EventCreate, EventOut, RegistrationOut
from app.services import event_service

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventOut, status_code=201, summary="Post a new event")
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    company: Account = Depends(require_company),
) -> EventOut:
    return event_service.create_event(db, company.id, payload)


@router.get("/mine", response_model=list[EventOut], summary="List the company's own events")
def list_my_events(
    db: Session = Depends(get_db),
    company: Account = Depends(require_company),
) -> list[EventOut]:
    return event_service.list_company_events(db, company.id)


@router.get("/{event_id}", response_model=EventOut, summary="Get one of the company's events")
def get_my_event(
    event_id: int,
    db: Session = Depends(get_db),
    company: Account = Depends(require_company),
) -> EventOut:
    return event_service.get_event_out(db, company.id, event_id)


@router.get(
    "/{event_id}/registrations",
    response_model=list[RegistrationOut],
    summary="List students registered for one of the company's events",
)
def list_event_registrations(
    event_id: int,
    db: Session = Depends(get_db),
    company: Account = Depends(require_company),
) -> list[RegistrationOut]:
    return event_service.list_registrations(db, company.id, event_id)
