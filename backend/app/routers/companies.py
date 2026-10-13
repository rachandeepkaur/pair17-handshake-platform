from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.dependencies import CompanyContext, get_db, require_company, require_permission
from app.schemas.company import CompanyProfileOut, CompanyProfileUpdate
from app.services import company_service

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/me", response_model=CompanyProfileOut, summary="Get your company's profile")
def get_my_profile(
    db: Session = Depends(get_db),
    ctx: CompanyContext = Depends(require_company),
) -> CompanyProfileOut:
    return company_service.to_profile(company_service.get_company(db, ctx.company_id))


@router.put("/me", response_model=CompanyProfileOut, summary="Update the company profile")
def update_my_profile(
    payload: CompanyProfileUpdate,
    db: Session = Depends(get_db),
    ctx: CompanyContext = Depends(require_permission("profile:write")),
) -> CompanyProfileOut:
    return company_service.update_profile(db, ctx.company_id, payload)


@router.post(
    "/me/picture",
    response_model=CompanyProfileOut,
    summary="Upload a profile picture (JPEG, PNG, or WebP, max 2 MB)",
)
async def upload_my_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    ctx: CompanyContext = Depends(require_permission("profile:write")),
) -> CompanyProfileOut:
    return await company_service.update_picture(db, ctx.company_id, file)
