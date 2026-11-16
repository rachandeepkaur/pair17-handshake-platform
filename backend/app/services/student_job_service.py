from datetime import date
from decimal import Decimal
from typing import Any

from pymongo.database import Database

from app.core.exceptions import BadRequestError, NotFoundError
from app.mongo import Doc, contains, doc, docs, encode, today_iso
from app.schemas.common import Page
from app.schemas.student_job import StudentJobOut

JOB_CATEGORIES = ("full_time", "part_time", "on_campus", "internship")


def _visible() -> dict[str, Any]:
    today = today_iso()
    return {"posting_date": {"$lte": today}, "deadline": {"$gte": today}}


def _companies(db: Database, company_ids: set[int]) -> dict[int, Doc]:
    return {row.id: row for row in docs(db.companies.find({"_id": {"$in": list(company_ids)}}))}


def _to_out(job: Doc, company: Doc | None) -> StudentJobOut:
    company = company or Doc({})
    return StudentJobOut(
        id=job.id,
        title=job.title,
        description=job.description,
        category=job.category,
        city=job.city,
        location=job.location,
        is_remote=job.is_remote,
        salary=job.salary,
        skills_required=job.skills_required,
        posting_date=job.posting_date,
        deadline=job.deadline,
        company_id=job.company_id,
        company_name=company.company_name or job.company_name,
        company_location=company.location,
        company_description=company.description,
        company_contact_info=company.contact_info,
    )


def list_jobs(
    db: Database,
    *,
    q: str | None = None,
    title: str | None = None,
    company: str | None = None,
    category: str | None = None,
    city: str | None = None,
    min_salary: Decimal | None = None,
    skills: str | None = None,
    deadline_on_or_before: date | None = None,
    remote: bool | None = None,
    limit: int = 20,
    offset: int = 0,
) -> Page[StudentJobOut]:
    if category and category not in JOB_CATEGORIES:
        raise BadRequestError(f"category must be one of {', '.join(JOB_CATEGORIES)}")

    clauses: list[dict[str, Any]] = [_visible()]
    if q:
        clauses.append({"$or": [{"title": contains(q)}, {"company_name": contains(q)}]})
    if title:
        clauses.append({"title": contains(title)})
    if company:
        clauses.append({"company_name": contains(company)})
    if category:
        clauses.append({"category": category})
    if city:
        clauses.append({"city": contains(city)})
    if min_salary is not None:
        clauses.append({"salary": {"$gte": encode(min_salary)}})
    if skills:
        # Every listed skill must appear.
        clauses.extend({"skills_required": contains(term.strip())} for term in skills.split(",") if term.strip())
    if deadline_on_or_before is not None:
        clauses.append({"deadline": {"$lte": deadline_on_or_before.isoformat()}})
    if remote is not None:
        clauses.append({"is_remote": remote})

    query = {"$and": clauses}
    total = db.jobs.count_documents(query)
    jobs = docs(db.jobs.find(query).sort([("posting_date", -1), ("_id", -1)]).skip(offset).limit(limit))
    companies = _companies(db, {job.company_id for job in jobs})
    return Page(
        items=[_to_out(job, companies.get(job.company_id)) for job in jobs],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_job(db: Database, job_id: int) -> StudentJobOut:
    job = doc(db.jobs.find_one({"_id": job_id, **_visible()}))
    if job is None:
        raise NotFoundError("Job not found")
    return _to_out(job, doc(db.companies.find_one({"_id": job.company_id})))
