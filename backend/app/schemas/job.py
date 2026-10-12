from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.job import JOB_CATEGORIES


class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=190)
    description: str | None = None
    category: str
    city: str = Field(min_length=1, max_length=100)
    location: str | None = Field(default=None, max_length=190)
    is_remote: bool = False
    salary: Decimal | None = None
    skills_required: str | None = None
    deadline: date

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        if value not in JOB_CATEGORIES:
            raise ValueError(f"category must be one of {JOB_CATEGORIES}")
        return value


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
