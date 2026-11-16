from fastapi import UploadFile
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.core.activity import log_activity
from app.core.exceptions import ConflictError, NotFoundError
from app.events import producer as events, topics
from app.mongo import Doc, doc, docs, next_id, today_iso, utcnow
from app.schemas.student_application import StudentApplicationOut
from app.services import file_service


def _outs(db: Database, applications: list[Doc]) -> list[StudentApplicationOut]:
    jobs = {row["_id"]: Doc(row) for row in db.jobs.find(
        {"_id": {"$in": list({a.job_id for a in applications})}}, {"title": 1, "company_id": 1, "company_name": 1}
    )}
    return [
        StudentApplicationOut(
            id=a.id,
            job_id=a.job_id,
            job_title=jobs[a.job_id].title if a.job_id in jobs else "",
            company_name=jobs[a.job_id].company_name if a.job_id in jobs else "",
            status=a.status,
            applied_at=a.applied_at,
            updated_at=a.updated_at,
        )
        for a in applications
    ]


def _visible_job(db: Database, job_id: int) -> Doc:
    today = today_iso()
    job = doc(db.jobs.find_one({"_id": job_id, "posting_date": {"$lte": today}, "deadline": {"$gte": today}}))
    if job is None:
        raise NotFoundError("Job not found")
    return job


async def create_application(db: Database, student_id: int, job_id: int, resume: UploadFile) -> StudentApplicationOut:
    job = _visible_job(db, job_id)
    if db.applications.find_one({"student_id": student_id, "job_id": job_id}, {"_id": 1}):
        raise ConflictError("You have already applied to this job")

    metadata = await file_service.save_resume(resume)
    now = utcnow()
    application = {
        "_id": next_id(db, "applications"),
        "student_id": student_id,
        "job_id": job_id,
        "company_id": job.company_id,
        "status": "Pending",
        # Resume metadata lives with the application; the PDF itself is on the uploads volume.
        "resume": {**metadata, "uploaded_at": now},
        "applied_at": now,
        "updated_at": now,
    }
    try:
        db.applications.insert_one(application)
    except DuplicateKeyError as exc:  # concurrent double-submit
        file_service.delete_upload(metadata["path"])
        raise ConflictError("You have already applied to this job") from exc
    except Exception:
        file_service.delete_upload(metadata["path"])
        raise

    events.publish(
        topics.APPLICATION_CREATED,
        application["_id"],
        {
            "application_id": application["_id"],
            "job_id": job_id,
            "student_id": student_id,
            "company_id": job.company_id,
            "status": "Pending",
            "applied_at": now.isoformat(),
        },
    )
    log_activity(db, student_id, "application.created", role="student", entity_type="application",
                 entity_id=application["_id"], details={"job_id": job_id})
    return _outs(db, [Doc(application)])[0]


def list_applications(db: Database, student_id: int, status: str | None = None) -> list[StudentApplicationOut]:
    query = {"student_id": student_id}
    if status:
        query["status"] = status
    return _outs(db, docs(db.applications.find(query).sort([("applied_at", -1), ("_id", -1)])))
