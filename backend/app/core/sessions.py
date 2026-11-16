"""Server-side login sessions stored in MongoDB.

A login creates a `sessions` document; the JWT carries only a random session id
(`sid`), and the database stores the SHA-256 of it, so a leaked database cannot be
replayed as tokens. A request is authenticated only while its session exists, is
not revoked, and has not expired. `expires_at` has a TTL index, so MongoDB deletes
expired sessions on its own; logout and password changes revoke them immediately.
Passwords stay bcrypt hashes (app.core.security).
"""

import hashlib
import secrets
from datetime import timedelta
from typing import Any

from pymongo.database import Database

from app.config import settings
from app.core.security import create_access_token
from app.mongo import Doc, doc, utcnow

_TOUCH_INTERVAL = timedelta(minutes=1)


def _hash(session_id: str) -> str:
    return hashlib.sha256(session_id.encode()).hexdigest()


def create_session(db: Database, account: Doc, *, user_agent: str | None = None, ip: str | None = None) -> str:
    """Start a session and return the signed access token for it."""

    session_id = secrets.token_urlsafe(32)
    now = utcnow()
    lifetime = timedelta(minutes=settings.jwt_expire_minutes)
    db.sessions.insert_one(
        {
            "_id": _hash(session_id),
            "account_id": account.id,
            "role": account.role,
            "created_at": now,
            "last_seen_at": now,
            "expires_at": now + lifetime,
            "revoked_at": None,
            "user_agent": (user_agent or "")[:300],
            "ip": ip,
        }
    )
    return create_access_token(subject=str(account.id), role=account.role, session_id=session_id, expires_delta=lifetime)


def validate_session(db: Database, payload: dict[str, Any]) -> Doc | None:
    """The live session behind a decoded token, or None if it ended."""

    session_id = payload.get("sid")
    if not session_id:
        return None
    session = doc(db.sessions.find_one({"_id": _hash(session_id)}))
    now = utcnow()
    if (
        session is None
        or session.revoked_at is not None
        or session.expires_at <= now
        or str(session.account_id) != str(payload.get("sub"))
    ):
        return None
    if now - session.last_seen_at > _TOUCH_INTERVAL:
        db.sessions.update_one({"_id": session.id}, {"$set": {"last_seen_at": now}})
    return session


def revoke_session(db: Database, session: Doc) -> None:
    now = utcnow()
    # Expiring it now also lets the TTL monitor remove the document.
    db.sessions.update_one({"_id": session.id}, {"$set": {"revoked_at": now, "expires_at": now}})


def revoke_other_sessions(db: Database, account_id: int, keep_session_id: str | None) -> int:
    now = utcnow()
    query: dict[str, Any] = {"account_id": account_id, "revoked_at": None}
    if keep_session_id:
        query["_id"] = {"$ne": keep_session_id}
    return db.sessions.update_many(query, {"$set": {"revoked_at": now, "expires_at": now}}).modified_count
