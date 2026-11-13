from fastapi import UploadFile
from pymongo.database import Database

from app.core.activity import log_activity
from app.core.exceptions import NotFoundError
from app.mongo import Doc, doc, encode, utcnow
from app.schemas.company import CompanyProfileOut, CompanyProfileUpdate
from app.services import file_service

# Fields counted toward the dashboard's profile-completion meter.
_PROFILE_FIELDS = ("company_name", "location", "description", "contact_info", "profile_picture_path")


def get_company(db: Database, company_id: int) -> Doc:
    company = doc(db.companies.find_one({"_id": company_id}))
    if company is None:
        raise NotFoundError("Company profile not found")
    account = db.accounts.find_one({"_id": company_id}, {"email": 1})
    company["email"] = account["email"] if account else ""
    return company


def to_profile(company: Doc) -> CompanyProfileOut:
    return CompanyProfileOut(
        account_id=company.account_id,
        company_name=company.company_name,
        email=company.email,
        location=company.location,
        description=company.description,
        contact_info=company.contact_info,
        profile_picture_url=file_service.picture_url(company.profile_picture_path),
    )


def profile_completion(company: Doc) -> int:
    filled = sum(1 for field in _PROFILE_FIELDS if company.get(field))
    return round(filled * 100 / len(_PROFILE_FIELDS))


def update_profile(db: Database, company_id: int, payload: CompanyProfileUpdate) -> CompanyProfileOut:
    company = get_company(db, company_id)
    values = payload.model_dump()
    db.companies.update_one({"_id": company_id}, {"$set": {**encode(values), "updated_at": utcnow()}})
    if values.get("company_name") and values["company_name"] != company.company_name:
        # Jobs and events carry a copy of the company name for search; keep it in step.
        for collection in (db.jobs, db.events):
            collection.update_many({"company_id": company_id}, {"$set": {"company_name": values["company_name"]}})
    log_activity(db, company_id, "company.profile_updated", role="company", entity_type="company", entity_id=company_id)
    return to_profile(get_company(db, company_id))


async def update_picture(db: Database, company_id: int, upload: UploadFile) -> CompanyProfileOut:
    company = get_company(db, company_id)
    new_path = await file_service.save_profile_picture(upload)
    db.companies.update_one({"_id": company_id}, {"$set": {"profile_picture_path": new_path, "updated_at": utcnow()}})
    file_service.delete_upload(company.profile_picture_path)
    return to_profile(get_company(db, company_id))
