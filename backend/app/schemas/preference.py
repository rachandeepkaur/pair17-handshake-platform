from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import clean_optional_text


class PreferenceUpdate(BaseModel):
    preferred_categories: str | None = Field(default=None, max_length=255)
    preferred_cities: str | None = Field(default=None, max_length=255)
    min_salary: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    preferred_skills: str | None = Field(default=None, max_length=5000)
    remote_ok: bool = False

    _optional = field_validator("preferred_categories", "preferred_cities", "preferred_skills")(clean_optional_text)


class PreferenceOut(PreferenceUpdate):
    pass
