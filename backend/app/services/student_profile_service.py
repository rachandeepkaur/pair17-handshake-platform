from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflictError, NotFoundError
from app.models.account import Account
from app.models.student import Student
from app.schemas.student import StudentProfileOut
from app.schemas.student_profile import StudentProfileUpdate
from app.services import file_service, student_service


def get_profile(db: Session, account_id: int) -> Student:
    student = db.scalar(
        select(Student).options(joinedload(Student.account)).where(Student.account_id == account_id)
    )
    if student is None:
        raise NotFoundError("Student profile not found")
    return student


def get_profile_out(db: Session, account_id: int) -> StudentProfileOut:
    return student_service.to_profile(get_profile(db, account_id))


def update_profile(
    db: Session,
    account_id: int,
    payload: StudentProfileUpdate,
) -> StudentProfileOut:
    student = get_profile(db, account_id)
    email = str(payload.email)

    existing_account = db.scalar(select(Account).where(Account.email == email, Account.id != account_id))
    if existing_account is not None:
        raise ConflictError("An account with this email already exists")

    values = payload.model_dump()
    student.account.email = values.pop("email")
    for field, value in values.items():
        setattr(student, field, value)

    db.commit()
    db.refresh(student)
    return student_service.to_profile(student)


async def update_picture(db: Session, account_id: int, upload: UploadFile) -> StudentProfileOut:
    student = get_profile(db, account_id)
    new_path = await file_service.save_profile_picture(upload)
    old_path = student.profile_picture_path
    student.profile_picture_path = new_path
    db.commit()
    file_service.delete_upload(old_path)
    db.refresh(student)
    return student_service.to_profile(student)
