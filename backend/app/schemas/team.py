import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import clean_required_text

InvitableRole = Literal["admin", "recruiter", "hiring_manager", "viewer"]


def _normalize_email(value: str) -> str:
    value = value.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
        raise ValueError("Enter a valid email address")
    return value


class MembershipOut(BaseModel):
    """The signed-in member's own name, role, and permissions."""

    member_id: int
    name: str
    email: str
    role: str
    role_label: str
    permissions: list[str]


class MemberOut(BaseModel):
    id: int
    account_id: int
    name: str
    email: str
    role: str
    role_label: str
    last_active_at: datetime | None
    created_at: datetime
    is_you: bool


class MemberRoleUpdate(BaseModel):
    role: InvitableRole


class InvitationCreate(BaseModel):
    email: str = Field(min_length=5, max_length=190)
    name: str = Field(min_length=1, max_length=150)
    role: InvitableRole

    _email = field_validator("email")(_normalize_email)
    _name = field_validator("name")(clean_required_text)


class InvitationOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    role_label: str
    expires_at: datetime
    created_at: datetime
    expired: bool


class InvitationWithToken(InvitationOut):
    """Returned only right after creating or regenerating an invite: the raw
    token is never stored, so this is the one chance to build the link."""

    token: str


class InvitationPreview(BaseModel):
    company_name: str
    email: str
    name: str
    role_label: str
    expires_at: datetime


class InvitationAccept(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8, max_length=72)

    _name = field_validator("name")(clean_required_text)


class MyMemberUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=150)

    _name = field_validator("name")(clean_required_text)


class RoleInfo(BaseModel):
    key: str
    label: str
    description: str
    permissions: list[str]


class PermissionInfo(BaseModel):
    key: str
    label: str


class PermissionMatrixOut(BaseModel):
    permissions: list[PermissionInfo]
    roles: list[RoleInfo]
