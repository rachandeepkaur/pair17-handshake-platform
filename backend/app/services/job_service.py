from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.application import Application
from app.models.job import Job
from app.schemas.job import JobCreate, JobOut


def _to_out(job: Job, applicant_count: int) -> JobOut:
    return JobOut.model_validate(job).model_copy(update={"applicant_count": applicant_count})


def create_job(db: Session, company_id: int, payload: JobCreate) -> JobOut:
    job = Job(company_id=company_id, **payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return _to_out(job, 0)


def get_owned_job(db: Session, company_id: int, job_id: int) -> Job:
    """Return the job only if it belongs to the company; 404 otherwise, so
    the response never reveals whether another company's job exists."""

    job = db.get(Job, job_id)
    if job is None or job.company_id != company_id:
        raise NotFoundError("Job not found")
    return job


def get_job_out(db: Session, company_id: int, job_id: int) -> JobOut:
    job = get_owned_job(db, company_id, job_id)
    count = db.scalar(select(func.count(Application.id)).where(Application.job_id == job.id))
    return _to_out(job, count)


def list_company_jobs(db: Session, company_id: int) -> list[JobOut]:
    counts = (
        select(Application.job_id, func.count(Application.id).label("n"))
        .group_by(Application.job_id)
        .subquery()
    )
    rows = db.execute(
        select(Job, func.coalesce(counts.c.n, 0))
        .outerjoin(counts, counts.c.job_id == Job.id)
        .where(Job.company_id == company_id)
        .order_by(Job.posting_date.desc(), Job.id.desc())
    ).all()
    return [_to_out(job, count) for job, count in rows]


def count_company_jobs(db: Session, company_id: int) -> int:
    return db.scalar(select(func.count(Job.id)).where(Job.company_id == company_id))


def count_active_jobs(db: Session, company_id: int) -> int:
    return db.scalar(
        select(func.count(Job.id)).where(Job.company_id == company_id, Job.deadline >= date.today())
    )
