from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_company
from app.models.account import Account
from app.models.company import Company
from app.schemas.company import CompanyDashboardOut
from app.services import job_service

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.get("/company", response_model=CompanyDashboardOut)
def company_dashboard(
    db: Session = Depends(get_db),
    account: Account = Depends(require_company),
) -> CompanyDashboardOut:
    company = db.get(Company, account.id)
    return CompanyDashboardOut(
        company_name=company.company_name,
        location=company.location,
        email=account.email,
        total_jobs=job_service.count_company_jobs(db, company_id=account.id),
    )
