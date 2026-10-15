from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_student
from app.models.account import Account
from app.schemas.common import Page
from app.schemas.student_job import StudentJobOut
from app.services import student_job_service


router = APIRouter(prefix="/student/jobs", tags=["student jobs"])


@router.get("", response_model=Page[StudentJobOut], summary="Search active jobs for students")
def list_student_jobs(
    q: str | None = Query(default=None, max_length=190, description="Matches job title or company name"),
    category: str | None = Query(default=None, max_length=30),
    city: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: Account = Depends(require_student),
) -> Page[StudentJobOut]:
    return student_job_service.list_jobs(
        db,
        q=q,
        category=category,
        city=city,
        limit=limit,
        offset=offset,
    )


@router.get("/{job_id}", response_model=StudentJobOut, summary="View an active job for students")
def get_student_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: Account = Depends(require_student),
) -> StudentJobOut:
    return student_job_service.get_job(db, job_id)
