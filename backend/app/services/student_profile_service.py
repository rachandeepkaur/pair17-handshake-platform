from fastapi import UploadFile
from pymongo.database import Database

from app.core.activity import log_activity
from app.core.exceptions import ConflictError, NotFoundError
from app.mongo import Doc, doc, encode, utcnow
from app.schemas.student import StudentProfileOut
from app.schemas.student_profile import StudentProfileUpdate
from app.services import file_service, student_service


def get_profile(db: Database, account_id: int) -> Doc:
    student = doc(db.students.find_one({"_id": account_id}))
    if student is None:
        raise NotFoundError("Student profile not found")
    return student


def _email(db: Database, account_id: int) -> str:
    account = db.accounts.find_one({"_id": account_id}, {"email": 1})
    return account["email"] if account else ""


def get_profile_out(db: Database, account_id: int) -> StudentProfileOut:
    return student_service.to_profile(get_profile(db, account_id), _email(db, account_id))


def update_profile(
    db: Database,
    account_id: int,
    payload: StudentProfileUpdate,
) -> StudentProfileOut:
    get_profile(db, account_id)
    values = payload.model_dump()
    email = str(values.pop("email"))

    if db.accounts.find_one({"email": email, "_id": {"$ne": account_id}}, {"_id": 1}):
        raise ConflictError("An account with this email already exists")

    db.accounts.update_one({"_id": account_id}, {"$set": {"email": email}})
    db.students.update_one({"_id": account_id}, {"$set": {**encode(values), "updated_at": utcnow()}})
    log_activity(db, account_id, "profile.updated", role="student", entity_type="student", entity_id=account_id)
    return get_profile_out(db, account_id)


async def update_picture(db: Database, account_id: int, upload: UploadFile) -> StudentProfileOut:
    student = get_profile(db, account_id)
    new_path = await file_service.save_profile_picture(upload)
    db.students.update_one({"_id": account_id}, {"$set": {"profile_picture_path": new_path, "updated_at": utcnow()}})
    file_service.delete_upload(student.profile_picture_path)
    return get_profile_out(db, account_id)
