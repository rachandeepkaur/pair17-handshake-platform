from typing import Any

from pymongo.database import Database

from app.core.exceptions import NotFoundError
from app.mongo import Doc, contains, doc, docs
from app.schemas.common import Page
from app.schemas.student import StudentProfileOut, StudentSummary
from app.services.file_service import picture_url


def to_profile(student: Doc, email: str) -> StudentProfileOut:
    return StudentProfileOut(
        **StudentSummary.model_validate(student).model_dump(),
        email=email,
        date_of_birth=student.date_of_birth,
        state=student.state,
        country=student.country,
        career_objective=student.career_objective,
        cgpa=student.cgpa,
        experience=student.experience,
        phone=student.phone,
        profile_picture_url=picture_url(student.profile_picture_path),
    )


def summaries_by_id(db: Database, student_ids: set[int]) -> dict[int, StudentSummary]:
    """Batch-load student summaries (replaces the SQL joins)."""

    rows = db.students.find({"_id": {"$in": list(student_ids)}})
    return {row["_id"]: StudentSummary.model_validate(Doc(row)) for row in rows}


def search_students(
    db: Database,
    *,
    q: str | None = None,
    college: str | None = None,
    skills: str | None = None,
    major: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> Page[StudentSummary]:
    query: dict[str, Any] = {}
    if q:
        query["name"] = contains(q)
    if college:
        query["college_name"] = contains(college)
    if major:
        query["major"] = contains(major)
    if skills:
        # Comma-separated input matches students who have ANY of the skills.
        terms = [term.strip() for term in skills.split(",") if term.strip()]
        if terms:
            query["$or"] = [{"skills": contains(term)} for term in terms]

    total = db.students.count_documents(query)
    rows = docs(db.students.find(query).sort([("name", 1), ("_id", 1)]).skip(offset).limit(limit))
    return Page[StudentSummary](
        items=[StudentSummary.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_student_profile(db: Database, student_id: int) -> StudentProfileOut:
    student = doc(db.students.find_one({"_id": student_id}))
    if student is None:
        raise NotFoundError("Student not found")
    account = db.accounts.find_one({"_id": student_id}, {"email": 1})
    return to_profile(student, account["email"] if account else "")
