from datetime import date
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import clean_optional_text, clean_required_text


class StudentProfileUpdate(BaseModel):
    """The complete editable profile for the signed-in student."""

    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    college_name: str = Field(min_length=1, max_length=190)
    date_of_birth: date | None = None
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    career_objective: str | None = Field(default=None, max_length=3000)
    degree: str | None = Field(default=None, max_length=100)
    major: str | None = Field(default=None, max_length=100)
    graduation_year: int | None = Field(default=None, ge=1900, le=9999)
    cgpa: Decimal | None = Field(default=None, ge=0, max_digits=3, decimal_places=2)
    experience: str | None = Field(default=None, max_length=10000)
    phone: str | None = Field(default=None, max_length=30)
    skills: str | None = Field(default=None, max_length=2000)

    _required = field_validator("name", "college_name")(clean_required_text)
    _optional = field_validator(
        "city",
        "state",
        "country",
        "career_objective",
        "degree",
        "major",
        "experience",
        "phone",
        "skills",
    )(clean_optional_text)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()
