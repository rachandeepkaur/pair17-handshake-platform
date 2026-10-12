from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_company
from app.models.account import Account
from app.schemas.company import CompanyDashboardOut, RecentApplicationOut
from app.services import application_service, company_service, event_service, job_service
from app.services.file_service import picture_url

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.get("/company", response_model=CompanyDashboardOut, summary="Company dashboard summary")
def company_dashboard(
    db: Session = Depends(get_db),
    account: Account = Depends(require_company),
) -> CompanyDashboardOut:
    company = company_service.get_company(db, account.id)
    by_status = application_service.status_counts(db, account.id)
    recent = application_service.recent_applications(db, account.id)

    return CompanyDashboardOut(
        company_name=company.company_name,
        location=company.location,
        email=account.email,
        profile_picture_url=picture_url(company.profile_picture_path),
        profile_completion=company_service.profile_completion(company),
        total_jobs=job_service.count_company_jobs(db, account.id),
        active_jobs=job_service.count_active_jobs(db, account.id),
        total_applicants=sum(by_status.values()),
        pending_applications=by_status["Pending"],
        upcoming_events=event_service.count_upcoming_events(db, account.id),
        total_registrations=event_service.count_registrations(db, account.id),
        applications_by_status=by_status,
        recent_applications=[
            RecentApplicationOut(
                id=item.id,
                student_id=item.student.account_id,
                student_name=item.student.name,
                college_name=item.student.college_name,
                job_id=item.job_id,
                job_title=item.job_title,
                status=item.status,
                applied_at=item.applied_at.isoformat(),
            )
            for item in recent
        ],
    )
