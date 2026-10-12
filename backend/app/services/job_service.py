from datetime import date

from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.job import JobCreate


def create_job(db: Session, company_id: int, payload: JobCreate) -> Job:
    job = Job(
        company_id=company_id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        city=payload.city,
        location=payload.location,
        is_remote=payload.is_remote,
        salary=payload.salary,
        skills_required=payload.skills_required,
        posting_date=date.today(),
        deadline=payload.deadline,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def list_company_jobs(db: Session, company_id: int) -> list[Job]:
    return (
        db.query(Job)
        .filter(Job.company_id == company_id)
        .order_by(Job.created_at.desc())
        .all()
    )


def count_company_jobs(db: Session, company_id: int) -> int:
    return db.query(Job).filter(Job.company_id == company_id).count()
