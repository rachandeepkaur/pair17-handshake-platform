"""Company <-> student messaging. Threads live in `message_threads` (the name
`conversations` belongs to the assistant's session memory); messages in `messages`."""

from dataclasses import dataclass
from typing import Any

from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.mongo import Doc, contains, doc, docs, next_id, utcnow
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


@dataclass
class Participant:
    """One side of a conversation: a company (any of its members) or a student."""

    side: str  # "company" | "student"
    account_id: int
    company_id: int | None = None
    student_id: int | None = None

    def owns(self, thread: Doc) -> bool:
        if self.side == "company":
            return thread.company_id == self.company_id
        return thread.student_id == self.student_id


def _from_other_side(participant: Participant, thread: Doc) -> dict[str, Any]:
    """Mongo filter: message was sent by the *other* side of the thread."""

    if participant.side == "company":
        return {"sender_account_id": thread.student_id}
    return {"sender_account_id": {"$ne": thread.student_id}}


def _scope(participant: Participant) -> dict[str, Any]:
    if participant.side == "company":
        return {"company_id": participant.company_id}
    return {"student_id": participant.student_id}


def _load(db: Database, thread: Doc) -> Doc:
    """Attach the student and company documents the API shapes need."""

    thread["student"] = doc(db.students.find_one({"_id": thread.student_id})) or Doc({})
    thread["company"] = doc(db.companies.find_one({"_id": thread.company_id})) or Doc({})
    return thread


def _company_brief(company: Doc) -> CompanyBrief:
    return CompanyBrief(
        account_id=company.account_id,
        company_name=company.company_name,
        profile_picture_url=picture_url(company.profile_picture_path),
    )


def _conversation_out(db: Database, participant: Participant, thread: Doc) -> ConversationOut:
    last = doc(db.messages.find_one({"thread_id": thread.id}, sort=[("created_at", -1), ("_id", -1)]))
    unread = db.messages.count_documents(
        {"thread_id": thread.id, "read_at": None, **_from_other_side(participant, thread)}
    )
    return ConversationOut(
        id=thread.id,
        student=StudentSummary.model_validate(thread.student),
        company=_company_brief(thread.company),
        last_message=LastMessage(
            body=last.body,
            created_at=last.created_at,
            sender_side="student" if last.sender_account_id == thread.student_id else "company",
        )
        if last
        else None,
        unread_count=unread,
    )


def _get_thread(db: Database, participant: Participant, thread_id: int) -> Doc:
    thread = doc(db.message_threads.find_one({"_id": thread_id}))
    if thread is None or not participant.owns(thread):
        raise NotFoundError("Conversation not found")
    return _load(db, thread)


def list_conversations(
    db: Database, participant: Participant, *, q: str | None = None, unread_only: bool = False
) -> list[ConversationOut]:
    query = _scope(participant)
    if q:
        if participant.side == "company":
            ids = [row["_id"] for row in db.students.find({"name": contains(q)}, {"_id": 1})]
            query["student_id"] = {"$in": ids}
        else:
            ids = [row["_id"] for row in db.companies.find({"company_name": contains(q)}, {"_id": 1})]
            query["company_id"] = {"$in": ids}
    threads = docs(db.message_threads.find(query))
    # Threads with no messages yet (last_message_at None) sort last.
    threads.sort(key=lambda t: (t.last_message_at is None, -(t.last_message_at.timestamp() if t.last_message_at else 0)))
    conversations = [_conversation_out(db, participant, _load(db, thread)) for thread in threads]
    if unread_only:
        conversations = [item for item in conversations if item.unread_count > 0]
    return conversations


def start_conversation(db: Database, participant: Participant, student_id: int) -> ConversationOut:
    if participant.side != "company":
        raise ForbiddenError("Only companies can start conversations")
    if db.students.find_one({"_id": student_id}, {"_id": 1}) is None:
        raise NotFoundError("Student not found")
    thread = db.message_threads.find_one({"company_id": participant.company_id, "student_id": student_id})
    if thread is None:
        thread = {
            "_id": next_id(db, "message_threads"),
            "company_id": participant.company_id,
            "student_id": student_id,
            "created_at": utcnow(),
            "last_message_at": None,
        }
        try:
            db.message_threads.insert_one(thread)
        except DuplicateKeyError:  # started concurrently by a teammate
            thread = db.message_threads.find_one({"company_id": participant.company_id, "student_id": student_id})
    return _conversation_out(db, participant, _get_thread(db, participant, thread["_id"]))


def _sender_names(db: Database, thread: Doc, messages: list[Doc]) -> dict[int, str]:
    company_senders = {m.sender_account_id for m in messages if m.sender_account_id not in (None, thread.student_id)}
    names = {thread.student_id: thread.student.name}
    if company_senders:
        company_name = thread.company.company_name
        for row in db.company_members.find({"account_id": {"$in": list(company_senders)}}, {"account_id": 1, "name": 1}):
            name = row["name"]
            names[row["account_id"]] = name if name == company_name else f"{name} · {company_name}"
    return names


def _message_out(db: Database, message: Doc, thread: Doc, participant: Participant, names) -> MessageOut:
    side = "student" if message.sender_account_id == thread.student_id else "company"
    if message.sender_account_id is None:
        name = f"Former teammate · {thread.company.company_name}"
    else:
        name = names.get(message.sender_account_id, thread.company.company_name)
    job = doc(db.jobs.find_one({"_id": message.job_id}, {"title": 1})) if message.job_id else None
    event = doc(db.events.find_one({"_id": message.event_id}, {"name": 1, "event_date": 1})) if message.event_id else None
    return MessageOut(
        id=message.id,
        body=message.body,
        created_at=message.created_at,
        read_at=message.read_at,
        sender_side=side,
        sender_name=name,
        from_me=side == participant.side,
        job=JobRef(id=job.id, title=job.title) if job else None,
        event=EventRef(id=event.id, name=event.name, event_date=event.event_date) if event else None,
    )


def get_conversation(db: Database, participant: Participant, conversation_id: int) -> ConversationDetailOut:
    thread = _get_thread(db, participant, conversation_id)
    messages = docs(db.messages.find({"thread_id": thread.id}).sort([("created_at", 1), ("_id", 1)]))
    names = _sender_names(db, thread, messages)
    return ConversationDetailOut(
        **_conversation_out(db, participant, thread).model_dump(),
        messages=[_message_out(db, m, thread, participant, names) for m in messages],
    )


def send_message(
    db: Database, participant: Participant, conversation_id: int, payload: MessageCreate
) -> MessageOut:
    thread = _get_thread(db, participant, conversation_id)
    if (payload.job_id or payload.event_id) and participant.side != "company":
        raise ForbiddenError("Only companies can attach jobs or events")
    if payload.job_id is not None:
        job = db.jobs.find_one({"_id": payload.job_id}, {"company_id": 1})
        if job is None or job["company_id"] != thread.company_id:
            raise BadRequestError("That job doesn't belong to your company")
    if payload.event_id is not None:
        event = db.events.find_one({"_id": payload.event_id}, {"company_id": 1})
        if event is None or event["company_id"] != thread.company_id:
            raise BadRequestError("That event doesn't belong to your company")

    now = utcnow()
    message = {
        "_id": next_id(db, "messages"),
        "thread_id": thread.id,
        "sender_account_id": participant.account_id,
        "body": payload.body,
        "job_id": payload.job_id,
        "event_id": payload.event_id,
        "created_at": now,
        "read_at": None,
    }
    db.messages.insert_one(message)
    db.message_threads.update_one({"_id": thread.id}, {"$set": {"last_message_at": now}})
    message = Doc(message)
    return _message_out(db, message, thread, participant, _sender_names(db, thread, [message]))


def mark_read(db: Database, participant: Participant, conversation_id: int) -> int:
    thread = _get_thread(db, participant, conversation_id)
    result = db.messages.update_many(
        {"thread_id": thread.id, "read_at": None, **_from_other_side(participant, thread)},
        {"$set": {"read_at": utcnow()}},
    )
    return result.modified_count


def unread_total(db: Database, company_id: int) -> int:
    total = 0
    for thread in db.message_threads.find({"company_id": company_id}, {"student_id": 1}):
        total += db.messages.count_documents(
            {"thread_id": thread["_id"], "read_at": None, "sender_account_id": thread["student_id"]}
        )
    return total
