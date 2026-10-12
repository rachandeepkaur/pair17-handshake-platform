from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.job import JOB_CATEGORIES
from app.schemas.common import clean_optional_text, clean_required_text


class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=190)
    description: str | None = Field(default=None, max_length=10000)
    category: str
    city: str = Field(min_length=1, max_length=100)
    location: str | None = Field(default=None, max_length=190)
    is_remote: bool = False
    salary: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    skills_required: str | None = Field(default=None, max_length=2000)
    posting_date: date = Field(default_factory=date.today)
    deadline: date

    _required = field_validator("title", "city")(clean_required_text)
    _optional = field_validator("description", "location", "skills_required")(clean_optional_text)

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        if value not in JOB_CATEGORIES:
            raise ValueError(f"category must be one of {', '.join(JOB_CATEGORIES)}")
        return value

    @model_validator(mode="after")
    def deadline_after_posting(self) -> "JobCreate":
        if self.deadline < self.posting_date:
            raise ValueError("Deadline must be on or after the posting date")
        return self


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    category: str
    city: str
    location: str | None
    is_remote: bool
    salary: Decimal | None
    skills_required: str | None
    posting_date: date
    deadline: date
    applicant_count: int = 0
