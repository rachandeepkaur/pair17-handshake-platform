from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_company
from app.models.account import Account
from app.schemas.company import CompanyProfileOut, CompanyProfileUpdate
from app.services import company_service

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/me", response_model=CompanyProfileOut, summary="Get the signed-in company's profile")
def get_my_profile(
    db: Session = Depends(get_db),
    account: Account = Depends(require_company),
) -> CompanyProfileOut:
    return company_service.to_profile(company_service.get_company(db, account.id), account)


@router.put("/me", response_model=CompanyProfileOut, summary="Update the company profile")
def update_my_profile(
    payload: CompanyProfileUpdate,
    db: Session = Depends(get_db),
    account: Account = Depends(require_company),
) -> CompanyProfileOut:
    return company_service.update_profile(db, account, payload)


@router.post(
    "/me/picture",
    response_model=CompanyProfileOut,
    summary="Upload a profile picture (JPEG, PNG, or WebP, max 2 MB)",
)
async def upload_my_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    account: Account = Depends(require_company),
) -> CompanyProfileOut:
    return await company_service.update_picture(db, account, file)
