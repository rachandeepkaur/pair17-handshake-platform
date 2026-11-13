from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.core.activity import log_activity
from app.core.exceptions import BadRequestError
from app.mongo import get_db, utcnow
from app.routers.auth import create_account
from app.schemas.auth import AccountResponse, StudentSignupRequest


router = APIRouter(prefix="/auth", tags=["student authentication"])

STUDENT_PROFILE_FIELDS = (
    "date_of_birth", "city", "state", "country", "career_objective", "degree", "major",
    "graduation_year", "cgpa", "experience", "phone", "skills", "profile_picture_path",
)


@router.post("/signup/student", response_model=AccountResponse, status_code=201)
def signup_student(
    payload: StudentSignupRequest,
    db: Database = Depends(get_db),
) -> AccountResponse:
    """Create a student login and its required initial profile together."""

    if len(payload.password.encode("utf-8")) > 72:
        raise BadRequestError("Password must be at most 72 bytes")

    account = create_account(db, payload.email, payload.password, "student")
    db.students.insert_one(
        {
            "_id": account.id,
            "account_id": account.id,
            "name": payload.name,
            "college_name": payload.college_name,
            **{field: None for field in STUDENT_PROFILE_FIELDS},
            "updated_at": utcnow(),
        }
    )
    log_activity(db, account.id, "account.signup", role="student", entity_type="student", entity_id=account.id)
    return AccountResponse(id=account.id, email=account.email, role=account.role)
