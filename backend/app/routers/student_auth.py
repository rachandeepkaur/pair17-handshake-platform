from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ConflictError
from app.core.security import hash_password
from app.database import get_db
from app.models.account import Account, AccountRole
from app.models.student import Student
from app.schemas.auth import AccountResponse, StudentSignupRequest


router = APIRouter(prefix="/auth", tags=["student authentication"])


@router.post("/signup/student", response_model=AccountResponse, status_code=201)
def signup_student(
    payload: StudentSignupRequest,
    db: Session = Depends(get_db),
) -> AccountResponse:
    """Create a student login and its required initial profile together."""

    if len(payload.password.encode("utf-8")) > 72:
        raise BadRequestError("Password must be at most 72 bytes")

    if db.query(Account).filter(Account.email == payload.email).first():
        raise ConflictError("An account with this email already exists")

    account = Account(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=AccountRole.STUDENT,
    )
    db.add(account)
    db.flush()

    db.add(
        Student(
            account_id=account.id,
            name=payload.name,
            college_name=payload.college_name,
        )
    )
    db.commit()

    return AccountResponse(id=account.id, email=account.email, role=account.role.value)
