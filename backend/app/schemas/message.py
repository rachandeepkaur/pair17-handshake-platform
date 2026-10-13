from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.student import StudentSummary


class CompanyBrief(BaseModel):
    account_id: int
    company_name: str
    profile_picture_url: str | None


class JobRef(BaseModel):
    id: int
    title: str


class EventRef(BaseModel):
    id: int
    name: str
    event_date: date


class MessageOut(BaseModel):
    id: int
    body: str
    created_at: datetime
    read_at: datetime | None
    sender_side: Literal["company", "student"]
    sender_name: str
    from_me: bool
    job: JobRef | None
    event: EventRef | None


class LastMessage(BaseModel):
    body: str
    created_at: datetime
    sender_side: Literal["company", "student"]


class ConversationOut(BaseModel):
    id: int
    student: StudentSummary
    company: CompanyBrief
    last_message: LastMessage | None
    unread_count: int


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut]


class ConversationStart(BaseModel):
    student_id: int


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    job_id: int | None = None
    event_id: int | None = None

    @field_validator("body")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be empty")
        return value
