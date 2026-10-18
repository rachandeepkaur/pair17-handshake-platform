"""Save one visible job or event for the authenticated student."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.assistant.tools.schemas import AssistantContext, ToolDefinition
from app.core.exceptions import AppError
from app.models.saved_item import SavedItem
from app.services import student_event_service, student_job_service


def save_job_or_event(context: AssistantContext, arguments: dict[str, Any]) -> str:
    """Persist a saved item. Part C adds confirmation before this handler runs."""

    if context.db is None:
        return "Saving is unavailable."

    item_type = arguments.get("item_type")
    item_id = arguments.get("item_id")
    if item_type not in {"job", "event"}:
        return "item_type must be either 'job' or 'event'."
    if not isinstance(item_id, int) or isinstance(item_id, bool) or item_id < 1:
        return "item_id must be a positive integer."

    try:
        existing = context.db.scalar(
            select(SavedItem.id).where(
                SavedItem.student_id == context.account_id,
                SavedItem.item_type == item_type,
                SavedItem.item_id == item_id,
            )
        )
        if existing is not None:
            return f"{item_type.capitalize()} {item_id} is already saved."
        visibility_error = _visibility_error(context, item_type, item_id)
        if visibility_error:
            return visibility_error

        context.db.add(SavedItem(student_id=context.account_id, item_type=item_type, item_id=item_id))
        context.db.commit()
    except IntegrityError:
        _rollback_safely(context)
        return f"{item_type.capitalize()} {item_id} is already saved."
    except Exception:
        _rollback_safely(context)
        return f"{item_type.capitalize()} {item_id} could not be saved."

    return f"Saved {item_type} {item_id} for this student."


def _visibility_error(context: AssistantContext, item_type: str, item_id: int) -> str | None:
    try:
        if item_type == "job":
            student_job_service.get_job(context.db, item_id)
        else:
            student_event_service.get_event(context.db, context.account_id, item_id)
    except AppError:
        return f"{item_type.capitalize()} {item_id} was not found."
    return None


def _rollback_safely(context: AssistantContext) -> None:
    try:
        context.db.rollback()
    except Exception:
        pass


TOOL = ToolDefinition(
    name="save_job_or_event",
    description=(
        "Save one job or event to the student's saved list. This changes data, so use it ONLY when the "
        "student explicitly asks to save a specific job or event ID. Returns a confirmation or a clear error."
    ),
    parameters={
        "type": "object",
        "required": ["item_type", "item_id"],
        "properties": {
            "item_type": {"type": "string", "enum": ["job", "event"], "description": "'job' or 'event'."},
            "item_id": {"type": "integer", "description": "The numeric ID shown by search_jobs or search_events."},
        },
    },
    handler=save_job_or_event,
)
