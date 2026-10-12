from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_company
from app.models.account import Account
from app.schemas.application import (
    ApplicationDetailOut,
    ApplicationOut,
    ApplicationStatus,
    ApplicationStatusUpdate,
)
from app.services import application_service

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get(
    "/company",
    response_model=list[ApplicationOut],
    summary="List all applications to the company's jobs",
)
def list_company_applications(
    job_id: int | None = None,
    status: ApplicationStatus | None = None,
    db: Session = Depends(get_db),
    company: Account = Depends(require_company),
) -> list[ApplicationOut]:
    return application_service.list_company_applications(
        db, company.id, job_id=job_id, status=status
    )


@router.get(
    "/{application_id}",
    response_model=ApplicationDetailOut,
    summary="Get one application with the applicant's full profile",
)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    company: Account = Depends(require_company),
) -> ApplicationDetailOut:
    return application_service.get_application_detail(db, company.id, application_id)


@router.patch(
    "/{application_id}/status",
    response_model=ApplicationOut,
    summary="Set an application's status to Pending, Reviewed, or Declined",
)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    company: Account = Depends(require_company),
) -> ApplicationOut:
    return application_service.update_status(db, company.id, application_id, payload.status)


@router.get(
    "/{application_id}/resume",
    response_class=FileResponse,
    summary="Stream the applicant's PDF resume for inline preview",
)
def get_resume(
    application_id: int,
    db: Session = Depends(get_db),
    company: Account = Depends(require_company),
) -> FileResponse:
    path = application_service.resume_file(db, company.id, application_id)
    return FileResponse(
        path,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="resume-{application_id}.pdf"'},
    )
