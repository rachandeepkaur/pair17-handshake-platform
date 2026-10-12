from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class StudentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: int
    name: str
    college_name: str
    degree: str | None
    major: str | None
    graduation_year: int | None
    city: str | None
    skills: str | None


class StudentProfileOut(StudentSummary):
    email: str
    date_of_birth: date | None
    state: str | None
    country: str | None
    career_objective: str | None
    cgpa: Decimal | None
    experience: str | None
    phone: str | None
    profile_picture_url: str | None
