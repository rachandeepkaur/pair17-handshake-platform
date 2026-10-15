from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class StudentJobOut(BaseModel):
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
    company_id: int
    company_name: str
    company_location: str
    company_description: str | None
    company_contact_info: str | None
