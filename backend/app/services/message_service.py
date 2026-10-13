from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.company import Company
from app.models.company_member import CompanyMember
from app.models.event import Event
from app.models.job import Job
from app.models.message import Conversation, Message
from app.models.student import Student
from app.schemas.message import (
    CompanyBrief,
    ConversationDetailOut,
    ConversationOut,
    EventRef,
    JobRef,
    LastMessage,
    MessageCreate,
    MessageOut,
)
from app.schemas.student import StudentSummary
from app.services.file_service import picture_url
from app.services.student_service import like_pattern


@dataclass
class Participant:
    """One side of a conversation: a company (any of its members) or a student."""

    side: str  # "company" | "student"
    account_id: int
    company_id: int | None = None
    student_id: int | None = None

    def owns(self, conversation: Conversation) -> bool:
        if self.side == "company":
            return conversation.company_id == self.company_id
        return conversation.student_id == self.student_id


def _from_other_side(participant: Participant, conversation_student_id):
    """SQL condition: message was sent by the *other* side of the thread."""

    if participant.side == "company":
        return Message.sender_account_id == conversation_student_id
    return or_(Message.sender_account_id.is_(None), Message.sender_account_id != conversation_student_id)


def _scope(participant: Participant):
    if participant.side == "company":
        return Conversation.company_id == participant.company_id
    return Conversation.student_id == participant.student_id


def _company_brief(company: Company) -> CompanyBrief:
    return CompanyBrief(
        account_id=company.account_id,
        company_name=company.company_name,
        profile_picture_url=picture_url(company.profile_picture_path),
    )


def _conversation_out(db: Session, participant: Participant, conversation: Conversation) -> ConversationOut:
    last = db.scalar(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(1)
    )
    unread = db.scalar(
        select(func.count(Message.id)).where(
            Message.conversation_id == conversation.id,
            Message.read_at.is_(None),
            _from_other_side(participant, conversation.student_id),
        )
    )
    return ConversationOut(
        id=conversation.id,
        student=StudentSummary.model_validate(conversation.student),
        company=_company_brief(conversation.company),
        last_message=LastMessage(
            body=last.body,
            created_at=last.created_at,
            sender_side="student" if last.sender_account_id == conversation.student_id else "company",
        )
        if last
        else None,
        unread_count=unread,
    )


def _get_conversation(db: Session, participant: Participant, conversation_id: int) -> Conversation:
    conversation = db.scalar(
        select(Conversation)
        .options(joinedload(Conversation.student), joinedload(Conversation.company))
        .where(Conversation.id == conversation_id)
    )
    if conversation is None or not participant.owns(conversation):
        raise NotFoundError("Conversation not found")
    return conversation


def list_conversations(
    db: Session, participant: Participant, *, q: str | None = None, unread_only: bool = False
) -> list[ConversationOut]:
    query = (
        select(Conversation)
        .options(joinedload(Conversation.student), joinedload(Conversation.company))
        .join(Student, Student.account_id == Conversation.student_id)
        .join(Company, Company.account_id == Conversation.company_id)
        .where(_scope(participant))
    )
    if q:
        name_column = Student.name if participant.side == "company" else Company.company_name
        query = query.where(name_column.ilike(like_pattern(q)))

    # NULL last_message_at (a thread with no messages yet) sorts last.
    rows = db.scalars(
        query.order_by(Conversation.last_message_at.is_(None), Conversation.last_message_at.desc())
    ).unique().all()
    conversations = [_conversation_out(db, participant, row) for row in rows]
    if unread_only:
        conversations = [item for item in conversations if item.unread_count > 0]
    return conversations


def start_conversation(db: Session, participant: Participant, student_id: int) -> ConversationOut:
    if participant.side != "company":
        raise ForbiddenError("Only companies can start conversations")
    if db.get(Student, student_id) is None:
        raise NotFoundError("Student not found")

    conversation = db.scalar(
        select(Conversation).where(
            Conversation.company_id == participant.company_id, Conversation.student_id == student_id
        )
    )
    if conversation is None:
        conversation = Conversation(company_id=participant.company_id, student_id=student_id)
        db.add(conversation)
        db.commit()
    return _conversation_out(db, participant, _get_conversation(db, participant, conversation.id))


def _sender_names(db: Session, conversation: Conversation, messages: list[Message]) -> dict[int, str]:
    company_senders = {
        m.sender_account_id for m in messages if m.sender_account_id not in (None, conversation.student_id)
    }
    names = {conversation.student_id: conversation.student.name}
    if company_senders:
        rows = db.execute(
            select(CompanyMember.account_id, CompanyMember.name).where(
                CompanyMember.account_id.in_(company_senders)
            )
        ).all()
        company_name = conversation.company.company_name
        names.update(
            {
                account_id: name if name == company_name else f"{name} · {company_name}"
                for account_id, name in rows
            }
        )
    return names


def _message_out(message: Message, conversation: Conversation, participant: Participant, names) -> MessageOut:
    side = "student" if message.sender_account_id == conversation.student_id else "company"
    if message.sender_account_id is None:
        name = f"Former teammate · {conversation.company.company_name}"
    else:
        name = names.get(message.sender_account_id, conversation.company.company_name)
    return MessageOut(
        id=message.id,
        body=message.body,
        created_at=message.created_at,
        read_at=message.read_at,
        sender_side=side,
        sender_name=name,
        from_me=side == participant.side,
        job=JobRef(id=message.job.id, title=message.job.title) if message.job else None,
        event=EventRef(id=message.event.id, name=message.event.name, event_date=message.event.event_date)
        if message.event
        else None,
    )


def get_conversation(db: Session, participant: Participant, conversation_id: int) -> ConversationDetailOut:
    conversation = _get_conversation(db, participant, conversation_id)
    messages = db.scalars(
        select(Message)
        .options(joinedload(Message.job), joinedload(Message.event))
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at, Message.id)
    ).all()
    names = _sender_names(db, conversation, messages)
    return ConversationDetailOut(
        **_conversation_out(db, participant, conversation).model_dump(),
        messages=[_message_out(m, conversation, participant, names) for m in messages],
    )


def send_message(
    db: Session, participant: Participant, conversation_id: int, payload: MessageCreate
) -> MessageOut:
    conversation = _get_conversation(db, participant, conversation_id)

    if (payload.job_id or payload.event_id) and participant.side != "company":
        raise ForbiddenError("Only companies can attach jobs or events")
    if payload.job_id is not None:
        job = db.get(Job, payload.job_id)
        if job is None or job.company_id != conversation.company_id:
            raise BadRequestError("That job doesn't belong to your company")
    if payload.event_id is not None:
        event = db.get(Event, payload.event_id)
        if event is None or event.company_id != conversation.company_id:
            raise BadRequestError("That event doesn't belong to your company")

    message = Message(
        conversation_id=conversation.id,
        sender_account_id=participant.account_id,
        body=payload.body,
        job_id=payload.job_id,
        event_id=payload.event_id,
    )
    db.add(message)
    db.flush()
    db.refresh(message)
    conversation.last_message_at = message.created_at
    db.commit()
    db.refresh(message)
    names = _sender_names(db, conversation, [message])
    return _message_out(message, conversation, participant, names)


def mark_read(db: Session, participant: Participant, conversation_id: int) -> int:
    conversation = _get_conversation(db, participant, conversation_id)
    result = db.execute(
        update(Message)
        .where(
            Message.conversation_id == conversation.id,
            Message.read_at.is_(None),
            _from_other_side(participant, conversation.student_id),
        )
        .values(read_at=datetime.now())
    )
    db.commit()
    return result.rowcount


def unread_total(db: Session, company_id: int) -> int:
    return db.scalar(
        select(func.count(Message.id))
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(
            Conversation.company_id == company_id,
            Message.read_at.is_(None),
            Message.sender_account_id == Conversation.student_id,
        )
    )
