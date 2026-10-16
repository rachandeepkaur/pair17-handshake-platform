from datetime import date, datetime, time

from pydantic import BaseModel


class StudentEventOut(BaseModel):
    id: int
    name: str
    description: str | None
    event_date: date
    event_time: time | None
    location: str | None
    eligibility: str | None
    company_name: str
    company_location: str
    registered: bool


class StudentRegistrationOut(BaseModel):
    id: int
    registered_at: datetime
    event: StudentEventOut
