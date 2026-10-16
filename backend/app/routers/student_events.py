from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_student
from app.models.account import Account
from app.schemas.student_event import StudentEventOut, StudentRegistrationOut
from app.services import student_event_service


router = APIRouter(prefix="/student/events", tags=["student events"])


@router.get("", response_model=list[StudentEventOut])
def list_student_events(
    db: Session = Depends(get_db), account: Account = Depends(require_student)
) -> list[StudentEventOut]:
    return student_event_service.list_events(db, account.id)


@router.get("/registrations", response_model=list[StudentRegistrationOut])
def list_my_registrations(
    db: Session = Depends(get_db), account: Account = Depends(require_student)
) -> list[StudentRegistrationOut]:
    return student_event_service.list_registrations(db, account.id)


@router.post("/{event_id}/register", response_model=StudentRegistrationOut, status_code=201)
def register_for_event(
    event_id: int, db: Session = Depends(get_db), account: Account = Depends(require_student)
) -> StudentRegistrationOut:
    return student_event_service.register_for_event(db, account.id, event_id)


@router.get("/{event_id}", response_model=StudentEventOut)
def get_student_event(
    event_id: int, db: Session = Depends(get_db), account: Account = Depends(require_student)
) -> StudentEventOut:
    return student_event_service.get_event(db, account.id, event_id)
