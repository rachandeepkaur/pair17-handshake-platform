from pymongo.database import Database

from app.core.activity import log_activity
from app.core.exceptions import NotFoundError
from app.events import producer as events, topics
from app.mongo import Doc, doc, docs, encode, next_id, today_iso, utcnow
from app.schemas.job import JobCreate, JobOut


def _to_out(job: Doc, applicant_count: int) -> JobOut:
    return JobOut.model_validate(job).model_copy(update={"applicant_count": applicant_count})


def applicant_counts(db: Database, job_ids: list[int]) -> dict[int, int]:
    rows = db.applications.aggregate(
        [{"$match": {"job_id": {"$in": job_ids}}}, {"$group": {"_id": "$job_id", "n": {"$sum": 1}}}]
    )
    return {row["_id"]: row["n"] for row in rows}


def create_job(db: Database, company_id: int, payload: JobCreate) -> JobOut:
    company = db.companies.find_one({"_id": company_id}, {"company_name": 1})
    job_id = next_id(db, "jobs")
    values = payload.model_dump()
    db.jobs.insert_one(
        {
            "_id": job_id,
            "company_id": company_id,
            # Copied for search ("title or company"); company_service keeps it in step on rename.
            "company_name": company["company_name"] if company else None,
            **encode(values),
            "created_at": utcnow(),
        }
    )
    job = get_owned_job(db, company_id, job_id)
    events.publish(
        topics.JOB_CREATED,
        job.id,
        {
            "job_id": job.id,
            "company_id": company_id,
            "title": job.title,
            "description": job.description,
            "category": job.category,
            "city": job.city,
            "location": job.location,
            "is_remote": job.is_remote,
            "salary": str(job.salary) if job.salary is not None else None,
            "skills_required": job.skills_required,
            "posting_date": job.posting_date,
            "deadline": job.deadline,
        },
    )
    log_activity(db, company_id, "job.created", role="company", entity_type="job", entity_id=job_id)
    return _to_out(job, 0)


def get_owned_job(db: Database, company_id: int, job_id: int) -> Doc:
    """Return the job only if it belongs to the company; 404 otherwise, so
    the response never reveals whether another company's job exists."""

    job = doc(db.jobs.find_one({"_id": job_id}))
    if job is None or job.company_id != company_id:
        raise NotFoundError("Job not found")
    return job


def get_job_out(db: Database, company_id: int, job_id: int) -> JobOut:
    job = get_owned_job(db, company_id, job_id)
    return _to_out(job, db.applications.count_documents({"job_id": job.id}))


def list_company_jobs(db: Database, company_id: int) -> list[JobOut]:
    jobs = docs(db.jobs.find({"company_id": company_id}).sort([("posting_date", -1), ("_id", -1)]))
    counts = applicant_counts(db, [job.id for job in jobs])
    return [_to_out(job, counts.get(job.id, 0)) for job in jobs]


def count_company_jobs(db: Database, company_id: int) -> int:
    return db.jobs.count_documents({"company_id": company_id})


def count_active_jobs(db: Database, company_id: int) -> int:
    return db.jobs.count_documents({"company_id": company_id, "deadline": {"$gte": today_iso()}})
