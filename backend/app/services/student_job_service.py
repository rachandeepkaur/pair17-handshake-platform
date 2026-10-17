from datetime import date
from decimal import Decimal

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.company import Company
from app.models.job import JOB_CATEGORIES, Job
from app.schemas.common import Page
from app.schemas.student_job import StudentJobOut


def _like_pattern(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _visible_jobs_query():
    return select(Job, Company).join(Company, Company.account_id == Job.company_id).where(
        Job.posting_date <= date.today(),
        Job.deadline >= date.today(),
    )


def _to_out(job: Job, company: Company) -> StudentJobOut:
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
        company_id=company.account_id,
        company_name=company.company_name,
        company_location=company.location,
        company_description=company.description,
        company_contact_info=company.contact_info,
    )


def list_jobs(
    db: Session,
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

    query = _visible_jobs_query()
    if q:
        pattern = _like_pattern(q)
        query = query.where(or_(Job.title.ilike(pattern), Company.company_name.ilike(pattern)))
    if title:
        query = query.where(Job.title.ilike(_like_pattern(title)))
    if company:
        query = query.where(Company.company_name.ilike(_like_pattern(company)))
    if category:
        query = query.where(Job.category == category)
    if city:
        query = query.where(Job.city.ilike(_like_pattern(city)))
    if min_salary is not None:
        query = query.where(Job.salary >= min_salary)
    if skills:
        skill_terms = [term.strip() for term in skills.split(",") if term.strip()]
        if skill_terms:
            query = query.where(and_(*(Job.skills_required.ilike(_like_pattern(term)) for term in skill_terms)))
    if deadline_on_or_before is not None:
        query = query.where(Job.deadline <= deadline_on_or_before)
    if remote is not None:
        query = query.where(Job.is_remote == remote)

    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0
    rows = db.execute(query.order_by(Job.posting_date.desc(), Job.id.desc()).limit(limit).offset(offset)).all()
    return Page(
        items=[_to_out(job, company) for job, company in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_job(db: Session, job_id: int) -> StudentJobOut:
    row = db.execute(_visible_jobs_query().where(Job.id == job_id)).one_or_none()
    if row is None:
        raise NotFoundError("Job not found")
    job, company = row
    return _to_out(job, company)
