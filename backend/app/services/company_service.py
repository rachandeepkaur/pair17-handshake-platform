from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.account import Account
from app.models.company import Company
from app.schemas.company import CompanyProfileOut, CompanyProfileUpdate
from app.services import file_service

# Fields counted toward the dashboard's profile-completion meter.
_PROFILE_FIELDS = ("company_name", "location", "description", "contact_info", "profile_picture_path")


def get_company(db: Session, account_id: int) -> Company:
    company = db.get(Company, account_id)
    if company is None:
        raise NotFoundError("Company profile not found")
    return company


def to_profile(company: Company, account: Account) -> CompanyProfileOut:
    return CompanyProfileOut(
        account_id=company.account_id,
        company_name=company.company_name,
        email=account.email,
        location=company.location,
        description=company.description,
        contact_info=company.contact_info,
        profile_picture_url=file_service.picture_url(company.profile_picture_path),
    )


def profile_completion(company: Company) -> int:
    filled = sum(1 for field in _PROFILE_FIELDS if getattr(company, field))
    return round(filled * 100 / len(_PROFILE_FIELDS))


def update_profile(db: Session, account: Account, payload: CompanyProfileUpdate) -> CompanyProfileOut:
    company = get_company(db, account.id)
    for field, value in payload.model_dump().items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return to_profile(company, account)


async def update_picture(db: Session, account: Account, upload: UploadFile) -> CompanyProfileOut:
    company = get_company(db, account.id)
    new_path = await file_service.save_profile_picture(upload)
    old_path = company.profile_picture_path
    company.profile_picture_path = new_path
    db.commit()
    file_service.delete_upload(old_path)
    db.refresh(company)
    return to_profile(company, account)
