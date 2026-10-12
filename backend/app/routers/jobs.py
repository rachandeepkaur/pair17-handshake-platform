from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_company
from app.models.account import Account
from app.schemas.job import JobCreate, JobOut
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobOut, status_code=201)
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    company: Account = Depends(require_company),
) -> JobOut:
    return job_service.create_job(db, company_id=company.id, payload=payload)


@router.get("/mine", response_model=list[JobOut])
def list_my_jobs(
    db: Session = Depends(get_db),
    company: Account = Depends(require_company),
) -> list[JobOut]:
    return job_service.list_company_jobs(db, company_id=company.id)
