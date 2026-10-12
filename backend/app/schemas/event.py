from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import clean_optional_text, clean_required_text
from app.schemas.student import StudentSummary


class EventCreate(BaseModel):
    name: str = Field(min_length=2, max_length=190)
    description: str | None = Field(default=None, max_length=5000)
    event_date: date
    event_time: time | None = None
    location: str | None = Field(default=None, max_length=190)
    eligibility: str | None = Field(default=None, max_length=255)

    _required = field_validator("name")(clean_required_text)
    _optional = field_validator("description", "location", "eligibility")(clean_optional_text)

    @field_validator("event_date")
    @classmethod
    def not_in_past(cls, value: date) -> date:
        if value < date.today():
            raise ValueError("Event date cannot be in the past")
        return value


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    event_date: date
    event_time: time | None
    location: str | None
    eligibility: str | None
    registration_count: int = 0


class RegistrationOut(BaseModel):
    id: int
    registered_at: datetime
    student: StudentSummary
