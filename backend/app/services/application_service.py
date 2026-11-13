from pathlib import Path
from typing import Any

from pymongo.database import Database

from app.constants import APPLICATION_STATUSES
from app.core.activity import log_activity
from app.core.exceptions import NotFoundError
from app.events import producer as events, topics
from app.mongo import Doc, doc, docs, utcnow
from app.schemas.application import ApplicationDetailOut, ApplicationOut
from app.services import file_service, student_service
from app.services.job_service import get_owned_job


def _outs(db: Database, applications: list[Doc]) -> list[ApplicationOut]:
    students = student_service.summaries_by_id(db, {a.student_id for a in applications})
    titles = {
        row["_id"]: row["title"]
        for row in db.jobs.find({"_id": {"$in": list({a.job_id for a in applications})}}, {"title": 1})
    }
    return [
        ApplicationOut(
            id=a.id,
            job_id=a.job_id,
            job_title=titles.get(a.job_id, ""),
            status=a.status,
            applied_at=a.applied_at,
            updated_at=a.updated_at,
            student=students[a.student_id],
        )
        for a in applications
        if a.student_id in students
    ]


def list_company_applications(
    db: Database,
    company_id: int,
    *,
    job_id: int | None = None,
    student_id: int | None = None,
    status: str | None = None,
) -> list[ApplicationOut]:
    if job_id is not None:
        get_owned_job(db, company_id, job_id)
    query: dict[str, Any] = {"company_id": company_id}
    if job_id is not None:
        query["job_id"] = job_id
    if student_id is not None:
        query["student_id"] = student_id
    if status:
        query["status"] = status
    rows = docs(db.applications.find(query).sort([("applied_at", -1), ("_id", -1)]))
    return _outs(db, rows)


def get_owned_application(db: Database, company_id: int, application_id: int) -> Doc:
    application = doc(db.applications.find_one({"_id": application_id, "company_id": company_id}))
    if application is None:
        raise NotFoundError("Application not found")
    return application


def get_application_detail(db: Database, company_id: int, application_id: int) -> ApplicationDetailOut:
    application = get_owned_application(db, company_id, application_id)
    summary = _outs(db, [application])[0]
    return ApplicationDetailOut(
        **summary.model_dump(exclude={"student"}),
        student=student_service.get_student_profile(db, application.student_id),
    )


def update_status(
    db: Database, company_id: int, application_id: int, status: str, *, actor_account_id: int | None = None
) -> ApplicationOut:
    application = get_owned_application(db, company_id, application_id)
    old_status = application.status
    now = utcnow()
    db.applications.update_one({"_id": application.id}, {"$set": {"status": status, "updated_at": now}})
    application = get_owned_application(db, company_id, application_id)
    data = {
        "application_id": application.id,
        "job_id": application.job_id,
        "student_id": application.student_id,
        "company_id": company_id,
        "old_status": old_status,
        "new_status": application.status,
        "updated_at": application.updated_at.isoformat(),
    }
    events.publish(topics.APPLICATION_UPDATED, application.id, {**data, "changed_fields": ["status"]})
    if old_status != application.status:
        events.publish(topics.APPLICATION_STATUS_CHANGED, application.id, data)
    log_activity(
        db, actor_account_id or company_id, "application.status_changed", role="company",
        entity_type="application", entity_id=application.id, details={"from": old_status, "to": status},
    )
    return _outs(db, [application])[0]


def resume_file(db: Database, company_id: int, application_id: int) -> Path:
    application = get_owned_application(db, company_id, application_id)
    return file_service.resolve_resume(application.resume.path)


def status_counts(db: Database, company_id: int) -> dict[str, int]:
    rows = db.applications.aggregate(
        [{"$match": {"company_id": company_id}}, {"$group": {"_id": "$status", "n": {"$sum": 1}}}]
    )
    counts = {status: 0 for status in APPLICATION_STATUSES}
    counts.update({row["_id"]: row["n"] for row in rows})
    return counts


def recent_applications(db: Database, company_id: int, limit: int = 5) -> list[ApplicationOut]:
    rows = docs(db.applications.find({"company_id": company_id}).sort([("applied_at", -1), ("_id", -1)]).limit(limit))
    return _outs(db, rows)
