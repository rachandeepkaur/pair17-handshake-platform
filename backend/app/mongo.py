"""MongoDB access for the platform (replaces the Lab 1 MySQL/SQLAlchemy layer).

Conventions
- Every collection keeps an integer `_id` drawn from the `counters` collection, so
  API ids, frontend routes, and the Postman collection are unchanged from Lab 1.
  Student and company profiles reuse their account id as `_id` (and store it as
  `account_id` too, as the API schemas expect).
- Dates without a time (deadline, event_date, date_of_birth) are ISO strings
  ("2026-11-13"): they sort and range-filter correctly as strings. Times of day are
  "HH:MM:SS". Timestamps are BSON datetimes (naive UTC, like MySQL DATETIME was).
- Money and GPA are Decimal128, so no float rounding creeps in.
- Writes always use `$set` of explicit fields, never whole-document replaces.
"""

import re
from collections.abc import Iterable, Iterator, Mapping
from datetime import date, datetime, time, timezone
from decimal import Decimal
from functools import lru_cache
from typing import Any

from bson.decimal128 import Decimal128
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.database import Database

from app.config import settings


@lru_cache
def get_client() -> MongoClient:
    return MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000, tz_aware=False)


def get_database() -> Database:
    return get_client()[settings.mongo_db]


def get_db() -> Iterator[Database]:
    """FastAPI dependency: the shared database handle (the client pools connections)."""

    yield get_database()


def utcnow() -> datetime:
    """Naive UTC, matching what pymongo returns for stored datetimes."""

    return datetime.now(timezone.utc).replace(tzinfo=None)


# ------------------------------------------------------------------ encoding
def encode(value: Any) -> Any:
    """Python -> BSON-safe value (recursively)."""

    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo is None else value.astimezone(timezone.utc).replace(tzinfo=None)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")
    if isinstance(value, Decimal):
        return Decimal128(value)
    if isinstance(value, Mapping):
        return {key: encode(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(item) for item in value]
    return value


def _decode(value: Any) -> Any:
    if isinstance(value, Decimal128):
        return value.to_decimal()
    if isinstance(value, dict):
        return Doc(value)
    if isinstance(value, list):
        return [_decode(item) for item in value]
    return value


class Doc(dict):
    """A Mongo document with attribute access; `.id` / ["id"] mirror `_id`.

    Lets services and Pydantic (`from_attributes=True`) read documents the way they
    read ORM rows. Missing attributes read as None, like nullable columns.
    """

    def __init__(self, raw: Mapping[str, Any] | None = None):
        super().__init__({key: _decode(value) for key, value in (raw or {}).items()})
        if "_id" in self and "id" not in self:
            self["id"] = self["_id"]

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__"):
            raise AttributeError(name)
        return self.get(name)


def doc(raw: Mapping[str, Any] | None) -> Doc | None:
    return Doc(raw) if raw is not None else None


def docs(cursor: Iterable[Mapping[str, Any]]) -> list[Doc]:
    return [Doc(raw) for raw in cursor]


# ------------------------------------------------------------------ ids
def next_id(db: Database, collection: str) -> int:
    """Atomic auto-increment per collection (counters._id = collection name)."""

    counter = db.counters.find_one_and_update(
        {"_id": collection}, {"$inc": {"seq": 1}}, upsert=True, return_document=ReturnDocument.AFTER
    )
    return int(counter["seq"])


def set_counter_floor(db: Database, collection: str) -> None:
    """After a bulk import, make the counter at least the highest existing _id."""

    top = db[collection].find_one({"_id": {"$type": "int"}}, sort=[("_id", DESCENDING)], projection={"_id": 1})
    if top:
        db.counters.update_one({"_id": collection}, {"$max": {"seq": int(top["_id"])}}, upsert=True)


# ------------------------------------------------------------------ search helpers
def contains(text: str) -> dict[str, Any]:
    """Case-insensitive substring match with the user's text taken literally."""

    return {"$regex": re.escape(text), "$options": "i"}


def today_iso() -> str:
    return date.today().isoformat()


# ------------------------------------------------------------------ indexes
INDEXES: dict[str, list[tuple[list[tuple[str, int]], dict[str, Any]]]] = {
    "accounts": [([("email", ASCENDING)], {"unique": True})],
    "students": [([("name", ASCENDING)], {})],
    "companies": [([("company_name", ASCENDING)], {})],
    "company_members": [
        ([("account_id", ASCENDING)], {"unique": True}),
        ([("company_id", ASCENDING), ("created_at", ASCENDING)], {}),
    ],
    "team_invitations": [
        ([("token_hash", ASCENDING)], {"unique": True}),
        ([("company_id", ASCENDING), ("email", ASCENDING)], {}),
    ],
    "jobs": [
        ([("company_id", ASCENDING), ("posting_date", DESCENDING)], {}),
        ([("deadline", ASCENDING), ("posting_date", DESCENDING)], {}),
        ([("city", ASCENDING), ("category", ASCENDING)], {}),
    ],
    "applications": [
        ([("student_id", ASCENDING), ("job_id", ASCENDING)], {"unique": True}),
        ([("job_id", ASCENDING), ("applied_at", DESCENDING)], {}),
        ([("company_id", ASCENDING), ("applied_at", DESCENDING)], {}),
    ],
    "events": [([("company_id", ASCENDING), ("event_date", ASCENDING)], {}), ([("event_date", ASCENDING)], {})],
    "registrations": [
        ([("student_id", ASCENDING), ("event_id", ASCENDING)], {"unique": True}),
        ([("event_id", ASCENDING)], {}),
        ([("company_id", ASCENDING)], {}),
    ],
    "saved_items": [([("student_id", ASCENDING), ("item_type", ASCENDING), ("item_id", ASCENDING)], {"unique": True})],
    "message_threads": [
        ([("company_id", ASCENDING), ("student_id", ASCENDING)], {"unique": True}),
        ([("student_id", ASCENDING)], {}),
    ],
    "messages": [([("thread_id", ASCENDING), ("created_at", ASCENDING)], {})],
    # Sessions disappear on their own once expires_at passes (TTL monitor runs every ~60 s;
    # the API also rejects expired sessions itself, so the lag never extends a session).
    "sessions": [
        ([("expires_at", ASCENDING)], {"expireAfterSeconds": 0}),
        ([("account_id", ASCENDING)], {}),
    ],
    "activity_logs": [
        ([("account_id", ASCENDING), ("at", DESCENDING)], {}),
        ([("action", ASCENDING), ("at", DESCENDING)], {}),
    ],
    # Assistant memory (three layers).
    "assistant_rules": [([("active", ASCENDING), ("priority", ASCENDING)], {})],
    "conversations": [
        ([("account_id", ASCENDING), ("session_id", ASCENDING)], {"unique": True}),
        ([("expires_at", ASCENDING)], {"expireAfterSeconds": 0}),
    ],
}


def ensure_indexes(db: Database) -> None:
    """Idempotent; called at service start-up and by the seed/migration scripts."""

    for collection, specs in INDEXES.items():
        for keys, options in specs:
            db[collection].create_index(keys, **options)
