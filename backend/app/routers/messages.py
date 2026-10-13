from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError
from app.core.permissions import ROLE_LABELS, has_permission
from app.dependencies import get_current_user, get_db
from app.models.account import Account
from app.models.company_member import CompanyMember
from app.schemas.message import (
    ConversationDetailOut,
    ConversationOut,
    ConversationStart,
    MessageCreate,
    MessageOut,
)
from app.services import message_service
from app.services.message_service import Participant

router = APIRouter(prefix="/messages", tags=["messages"])


class _Caller:
    """Resolves the signed-in account to its side of a conversation. Company
    members act for their company; students act for themselves. Kept
    role-agnostic so the student portal can use the same endpoints."""

    def __init__(self, participant: Participant, member_role: str | None):
        self.participant = participant
        self.member_role = member_role

    def require_write(self) -> None:
        if self.member_role is not None and not has_permission(self.member_role, "messages:write"):
            raise ForbiddenError(f"Your role ({ROLE_LABELS[self.member_role]}) can't send messages")


def get_caller(account: Account = Depends(get_current_user), db: Session = Depends(get_db)) -> _Caller:
    if account.role == "student":
        return _Caller(Participant(side="student", account_id=account.id, student_id=account.id), None)

    member = db.scalar(select(CompanyMember).where(CompanyMember.account_id == account.id))
    if member is None:
        raise ForbiddenError("This account is not a member of any company")
    return _Caller(
        Participant(side="company", account_id=account.id, company_id=member.company_id),
        member.role,
    )


@router.get("/conversations", response_model=list[ConversationOut], summary="List your conversations")
def list_conversations(
    q: str | None = Query(default=None, max_length=150, description="Matches the other side's name"),
    unread_only: bool = False,
    db: Session = Depends(get_db),
    caller: _Caller = Depends(get_caller),
) -> list[ConversationOut]:
    return message_service.list_conversations(db, caller.participant, q=q, unread_only=unread_only)


@router.post(
    "/conversations",
    response_model=ConversationOut,
    summary="Open (or reuse) the conversation with a student — companies only",
)
def start_conversation(
    payload: ConversationStart,
    db: Session = Depends(get_db),
    caller: _Caller = Depends(get_caller),
) -> ConversationOut:
    caller.require_write()
    return message_service.start_conversation(db, caller.participant, payload.student_id)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailOut,
    summary="Get a conversation with all its messages",
)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    caller: _Caller = Depends(get_caller),
) -> ConversationDetailOut:
    return message_service.get_conversation(db, caller.participant, conversation_id)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageOut,
    status_code=201,
    summary="Send a message; companies may attach one of their jobs or events",
)
def send_message(
    conversation_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    caller: _Caller = Depends(get_caller),
) -> MessageOut:
    caller.require_write()
    return message_service.send_message(db, caller.participant, conversation_id, payload)


@router.post(
    "/conversations/{conversation_id}/read",
    summary="Mark the other side's messages in this conversation as read",
)
def mark_read(
    conversation_id: int,
    db: Session = Depends(get_db),
    caller: _Caller = Depends(get_caller),
) -> dict[str, int]:
    return {"marked_read": message_service.mark_read(db, caller.participant, conversation_id)}
