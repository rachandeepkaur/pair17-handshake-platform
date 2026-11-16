"""Append-only activity log in MongoDB (`activity_logs`).

Logging never fails the request it describes.
"""

import logging
from typing import Any

from pymongo.database import Database

from app.mongo import encode, utcnow

logger = logging.getLogger("p17.activity")


def log_activity(
    db: Database,
    account_id: int | None,
    action: str,
    *,
    role: str | None = None,
    entity_type: str | None = None,
    entity_id: int | str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    try:
        db.activity_logs.insert_one(
            {
                "account_id": account_id,
                "role": role,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "details": encode(details or {}),
                "at": utcnow(),
            }
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("could not record activity %s: %s", action, exc)
