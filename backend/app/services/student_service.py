from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.models.student import Student
from app.schemas.common import Page
from app.schemas.student import StudentProfileOut, StudentSummary
from app.services.file_service import picture_url


def _like(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def to_profile(student: Student) -> StudentProfileOut:
    return StudentProfileOut(
        **StudentSummary.model_validate(student).model_dump(),
        email=student.account.email,
        date_of_birth=student.date_of_birth,
        state=student.state,
        country=student.country,
        career_objective=student.career_objective,
        cgpa=student.cgpa,
        experience=student.experience,
        phone=student.phone,
        profile_picture_url=picture_url(student.profile_picture_path),
    )


def search_students(
    db: Session,
    *,
    q: str | None = None,
    college: str | None = None,
    skills: str | None = None,
    major: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> Page[StudentSummary]:
    query = select(Student)
    if q:
        query = query.where(Student.name.ilike(_like(q)))
    if college:
        query = query.where(Student.college_name.ilike(_like(college)))
    if major:
        query = query.where(Student.major.ilike(_like(major)))
    if skills:
        # Comma-separated input matches students who have ANY of the skills.
        terms = [term.strip() for term in skills.split(",") if term.strip()]
        if terms:
            query = query.where(or_(*(Student.skills.ilike(_like(term)) for term in terms)))

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(Student.name).limit(limit).offset(offset)).all()
    return Page[StudentSummary](
        items=[StudentSummary.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_student_profile(db: Session, student_id: int) -> StudentProfileOut:
    student = db.scalar(
        select(Student).options(joinedload(Student.account)).where(Student.account_id == student_id)
    )
    if student is None:
        raise NotFoundError("Student not found")
    return to_profile(student)
