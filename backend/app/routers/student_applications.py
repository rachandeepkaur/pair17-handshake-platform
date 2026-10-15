from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_student
from app.models.account import Account
from app.schemas.student_application import ApplicationStatus, StudentApplicationOut
from app.services import student_application_service


router = APIRouter(prefix="/student", tags=["student applications"])


@router.post("/jobs/{job_id}/apply", response_model=StudentApplicationOut, status_code=201)
async def apply_to_job(
    job_id: int,
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
    account: Account = Depends(require_student),
) -> StudentApplicationOut:
    return await student_application_service.create_application(db, account.id, job_id, resume)


@router.get("/applications", response_model=list[StudentApplicationOut])
def list_my_applications(
    status: ApplicationStatus | None = Query(default=None),
    db: Session = Depends(get_db),
    account: Account = Depends(require_student),
) -> list[StudentApplicationOut]:
    return student_application_service.list_applications(db, account.id, status)
