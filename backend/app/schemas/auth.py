import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StudentSignupRequest(BaseModel):
    """Data required to create a student account and profile."""

    name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=5, max_length=190)
    password: str = Field(min_length=8, max_length=128)
    college_name: str = Field(min_length=1, max_length=190)

    @field_validator("name", "college_name")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=190)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
