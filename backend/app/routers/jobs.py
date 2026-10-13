from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import CompanyContext, get_db, require_company, require_permission
from app.schemas.application import ApplicationOut, ApplicationStatus
from app.schemas.job import JobCreate, JobOut
from app.services import application_service, job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobOut, status_code=201, summary="Post a new job")
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    ctx: CompanyContext = Depends(require_permission("jobs:write")),
) -> JobOut:
    return job_service.create_job(db, company_id=ctx.company_id, payload=payload)


@router.get("/mine", response_model=list[JobOut], summary="List the company's own job postings")
def list_my_jobs(
    db: Session = Depends(get_db),
    ctx: CompanyContext = Depends(require_company),
) -> list[JobOut]:
    return job_service.list_company_jobs(db, company_id=ctx.company_id)


@router.get("/{job_id}", response_model=JobOut, summary="Get one of the company's job postings")
def get_my_job(
    job_id: int,
    db: Session = Depends(get_db),
    ctx: CompanyContext = Depends(require_company),
) -> JobOut:
    return job_service.get_job_out(db, company_id=ctx.company_id, job_id=job_id)


@router.get(
    "/{job_id}/applications",
    response_model=list[ApplicationOut],
    summary="List students who applied to one of the company's jobs",
)
def list_job_applications(
    job_id: int,
    status: ApplicationStatus | None = None,
    db: Session = Depends(get_db),
    ctx: CompanyContext = Depends(require_company),
) -> list[ApplicationOut]:
    return application_service.list_company_applications(
        db, ctx.company_id, job_id=job_id, status=status
    )
