from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.account import Account
from app.schemas.common import Page
from app.schemas.student import StudentProfileOut, StudentSummary
from app.services import student_service

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=Page[StudentSummary], summary="Search students")
def search_students(
    q: str | None = Query(default=None, max_length=150, description="Matches student name"),
    college: str | None = Query(default=None, max_length=190),
    skills: str | None = Query(default=None, max_length=300, description="Comma-separated; matches any"),
    major: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: Account = Depends(get_current_user),
) -> Page[StudentSummary]:
    return student_service.search_students(
        db, q=q, college=college, skills=skills, major=major, limit=limit, offset=offset
    )


@router.get("/{student_id}", response_model=StudentProfileOut, summary="View a student's profile")
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    _: Account = Depends(get_current_user),
) -> StudentProfileOut:
    return student_service.get_student_profile(db, student_id)
