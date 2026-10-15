from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_student
from app.models.account import Account
from app.schemas.student import StudentProfileOut
from app.schemas.student_profile import StudentProfileUpdate
from app.services import student_profile_service


router = APIRouter(prefix="/students", tags=["student profile"])


@router.get("/me", response_model=StudentProfileOut, summary="Get the signed-in student's profile")
def get_my_profile(
    db: Session = Depends(get_db),
    account: Account = Depends(require_student),
) -> StudentProfileOut:
    return student_profile_service.get_profile_out(db, account.id)


@router.put("/me", response_model=StudentProfileOut, summary="Update the signed-in student's profile")
def update_my_profile(
    payload: StudentProfileUpdate,
    db: Session = Depends(get_db),
    account: Account = Depends(require_student),
) -> StudentProfileOut:
    return student_profile_service.update_profile(db, account.id, payload)


@router.post(
    "/me/picture",
    response_model=StudentProfileOut,
    summary="Upload the signed-in student's profile picture",
)
async def upload_my_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    account: Account = Depends(require_student),
) -> StudentProfileOut:
    return await student_profile_service.update_picture(db, account.id, file)
