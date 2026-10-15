from datetime import date

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.application import Application
from app.models.company import Company
from app.models.job import Job
from app.schemas.student_application import StudentApplicationOut
from app.services import file_service


def _to_out(application: Application) -> StudentApplicationOut:
    return StudentApplicationOut(
        id=application.id,
        job_id=application.job_id,
        job_title=application.job.title,
        company_name=application.job.company.company_name,
        status=application.status,
        applied_at=application.applied_at,
        updated_at=application.updated_at,
    )


def _visible_job(db: Session, job_id: int) -> Job:
    job = db.scalar(
        select(Job).where(Job.id == job_id, Job.posting_date <= date.today(), Job.deadline >= date.today())
    )
    if job is None:
        raise NotFoundError("Job not found")
    return job


async def create_application(db: Session, student_id: int, job_id: int, resume: UploadFile) -> StudentApplicationOut:
    _visible_job(db, job_id)
    exists = db.scalar(select(Application.id).where(Application.student_id == student_id, Application.job_id == job_id))
    if exists is not None:
        raise ConflictError("You have already applied to this job")

    resume_path = await file_service.save_resume(resume)
    application = Application(student_id=student_id, job_id=job_id, resume_path=resume_path)
    db.add(application)
    try:
        db.commit()
    except Exception:
        db.rollback()
        file_service.delete_upload(resume_path)
        raise
    db.refresh(application)
    application = db.scalar(
        select(Application)
        .options(joinedload(Application.job).joinedload(Job.company))
        .where(Application.id == application.id)
    )
    return _to_out(application)


def list_applications(db: Session, student_id: int, status: str | None = None) -> list[StudentApplicationOut]:
    query = (
        select(Application)
        .join(Job, Job.id == Application.job_id)
        .join(Company, Company.account_id == Job.company_id)
        .options(joinedload(Application.job).joinedload(Job.company))
        .where(Application.student_id == student_id)
    )
    if status:
        query = query.where(Application.status == status)
    rows = db.scalars(query.order_by(Application.applied_at.desc(), Application.id.desc())).all()
    return [_to_out(application) for application in rows]
