from datetime import datetime
from typing import Literal

from pydantic import BaseModel


ApplicationStatus = Literal["Pending", "Reviewed", "Declined"]


class StudentApplicationOut(BaseModel):
    id: int
    job_id: int
    job_title: str
    company_name: str
    status: ApplicationStatus
    applied_at: datetime
    updated_at: datetime
