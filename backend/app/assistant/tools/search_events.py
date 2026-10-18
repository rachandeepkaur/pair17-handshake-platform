"""Search upcoming recruiting events for the authenticated student."""

from datetime import date
from typing import Any

from app.assistant.tools.schemas import AssistantContext, ToolDefinition
from app.services import student_event_service


def search_events(context: AssistantContext, arguments: dict[str, Any]) -> str:
    if context.db is None:
        return "Event search is unavailable."

    start_date, start_error = _date_argument(arguments, "start_date")
    if start_error:
        return start_error
    end_date, end_error = _date_argument(arguments, "end_date")
    if end_error:
        return end_error
    if start_date and end_date and end_date < start_date:
        return "end_date must be on or after start_date."
    eligible_only, eligibility_error = _boolean_argument(arguments, "eligible_only")
    if eligibility_error:
        return eligibility_error

    try:
        events = student_event_service.list_events(
            context.db,
            context.account_id,
            q=_text_argument(arguments, "name"),
            city=_text_argument(arguments, "city"),
            start_date=start_date,
            end_date=end_date,
            major=_text_argument(arguments, "major"),
            eligibility=_text_argument(arguments, "eligibility"),
            eligible_only=eligible_only or False,
        )[:10]
    except Exception:
        return "Event search could not be completed."

    if not events:
        return "No matching upcoming events found."

    return "Matching upcoming events:\n" + "\n".join(
        f"- ID {event.id}: {event.name} | {event.event_date.isoformat()} {event.event_time or ''} | "
        f"{event.location or 'location not listed'} | {event.company_name} | "
        f"eligibility: {event.eligibility or 'everyone'}"
        for event in events
    )


def _text_argument(arguments: dict[str, Any], name: str) -> str | None:
    value = arguments.get(name)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _date_argument(arguments: dict[str, Any], name: str) -> tuple[date | None, str | None]:
    value = arguments.get(name)
    if value is None:
        return None, None
    if not isinstance(value, str):
        return None, f"{name} must use YYYY-MM-DD."
    try:
        return date.fromisoformat(value), None
    except ValueError:
        return None, f"{name} must use YYYY-MM-DD."


def _boolean_argument(arguments: dict[str, Any], name: str) -> tuple[bool | None, str | None]:
    value = arguments.get(name)
    if value is None:
        return None, None
    if not isinstance(value, bool):
        return None, f"{name} must be true or false."
    return value, None


TOOL = ToolDefinition(
    name="search_events",
    description=(
        "Search upcoming recruiting events. Use whenever the student asks about events, fairs, or info "
        "sessions. Filter by name, city, date range, major, or eligibility; for 'next month' pass that "
        "month's first and last day. Returns a short list or a plain no-match message."
    ),
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Words in the event name."},
            "city": {"type": "string", "description": "Event city."},
            "start_date": {"type": "string", "format": "date", "description": "Earliest event date (YYYY-MM-DD)."},
            "end_date": {"type": "string", "format": "date", "description": "Latest event date (YYYY-MM-DD)."},
            "major": {"type": "string", "description": "Only events open to this major, e.g. 'Computer Science'."},
            "eligibility": {"type": "string", "description": "Text in the event eligibility requirement."},
            "eligible_only": {"type": "boolean", "description": "Return only events eligible for the current student."},
        },
    },
    handler=search_events,
)
