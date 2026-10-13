from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import clean_optional_text, clean_required_text
from app.schemas.team import MembershipOut


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: int
    company_name: str
    email: str
    location: str


class CompanyProfileOut(BaseModel):
    account_id: int
    company_name: str
    email: str
    location: str
    description: str | None
    contact_info: str | None
    profile_picture_url: str | None


class CompanyProfileUpdate(BaseModel):
    company_name: str = Field(min_length=2, max_length=190)
    location: str = Field(min_length=2, max_length=190)
    description: str | None = Field(default=None, max_length=5000)
    contact_info: str | None = Field(default=None, max_length=255)

    _required = field_validator("company_name", "location")(clean_required_text)
    _optional = field_validator("description", "contact_info")(clean_optional_text)


class RecentApplicationOut(BaseModel):
    id: int
    student_id: int
    student_name: str
    college_name: str
    job_id: int
    job_title: str
    status: str
    applied_at: str


class CompanyDashboardOut(BaseModel):
    company_name: str
    location: str
    email: str
    profile_picture_url: str | None
    profile_completion: int
    total_jobs: int
    active_jobs: int
    total_applicants: int
    pending_applications: int
    upcoming_events: int
    total_registrations: int
    applications_by_status: dict[str, int]
    recent_applications: list[RecentApplicationOut]
    unread_messages: int
    member: MembershipOut
