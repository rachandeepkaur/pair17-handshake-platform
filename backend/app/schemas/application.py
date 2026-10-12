from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.student import StudentProfileOut, StudentSummary

ApplicationStatus = Literal["Pending", "Reviewed", "Declined"]


class ApplicationOut(BaseModel):
    id: int
    job_id: int
    job_title: str
    status: ApplicationStatus
    applied_at: datetime
    updated_at: datetime
    student: StudentSummary


class ApplicationDetailOut(ApplicationOut):
    student: StudentProfileOut


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
