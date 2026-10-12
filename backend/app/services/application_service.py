from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.models.application import APPLICATION_STATUSES, Application
from app.models.job import Job
from app.models.student import Student
from app.schemas.application import ApplicationDetailOut, ApplicationOut
from app.schemas.student import StudentSummary
from app.services import file_service, student_service
from app.services.job_service import get_owned_job


def _to_out(application: Application) -> ApplicationOut:
    return ApplicationOut(
        id=application.id,
        job_id=application.job_id,
        job_title=application.job.title,
        status=application.status,
        applied_at=application.applied_at,
        updated_at=application.updated_at,
        student=StudentSummary.model_validate(application.student),
    )


def _company_applications(company_id: int):
    return (
        select(Application)
        .join(Job, Job.id == Application.job_id)
        .options(joinedload(Application.job), joinedload(Application.student))
        .where(Job.company_id == company_id)
    )


def list_company_applications(
    db: Session,
    company_id: int,
    *,
    job_id: int | None = None,
    status: str | None = None,
) -> list[ApplicationOut]:
    if job_id is not None:
        get_owned_job(db, company_id, job_id)

    query = _company_applications(company_id)
    if job_id is not None:
        query = query.where(Application.job_id == job_id)
    if status:
        query = query.where(Application.status == status)

    rows = db.scalars(query.order_by(Application.applied_at.desc(), Application.id.desc())).all()
    return [_to_out(row) for row in rows]


def get_owned_application(db: Session, company_id: int, application_id: int) -> Application:
    application = db.scalar(
        _company_applications(company_id)
        .options(joinedload(Application.student).joinedload(Student.account))
        .where(Application.id == application_id)
    )
    if application is None:
        raise NotFoundError("Application not found")
    return application


def get_application_detail(db: Session, company_id: int, application_id: int) -> ApplicationDetailOut:
    application = get_owned_application(db, company_id, application_id)
    summary = _to_out(application)
    return ApplicationDetailOut(
        **summary.model_dump(exclude={"student"}),
        student=student_service.to_profile(application.student),
    )


def update_status(db: Session, company_id: int, application_id: int, status: str) -> ApplicationOut:
    application = get_owned_application(db, company_id, application_id)
    application.status = status
    db.commit()
    db.refresh(application)
    return _to_out(application)


def resume_file(db: Session, company_id: int, application_id: int) -> Path:
    application = get_owned_application(db, company_id, application_id)
    return file_service.resolve_resume(application.resume_path)


def status_counts(db: Session, company_id: int) -> dict[str, int]:
    rows = db.execute(
        select(Application.status, func.count(Application.id))
        .join(Job, Job.id == Application.job_id)
        .where(Job.company_id == company_id)
        .group_by(Application.status)
    ).all()
    counts = {status: 0 for status in APPLICATION_STATUSES}
    counts.update({status: count for status, count in rows})
    return counts


def recent_applications(db: Session, company_id: int, limit: int = 5) -> list[ApplicationOut]:
    rows = db.scalars(
        _company_applications(company_id)
        .order_by(Application.applied_at.desc(), Application.id.desc())
        .limit(limit)
    ).all()
    return [_to_out(row) for row in rows]
