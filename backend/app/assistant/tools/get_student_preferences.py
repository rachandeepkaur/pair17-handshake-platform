"""Read the current student's saved job and event preferences."""

from typing import Any

from app.assistant.tools.schemas import AssistantContext, ToolDefinition
from app.models.preference import Preference


def get_student_preferences(context: AssistantContext, _arguments: dict[str, Any]) -> str:
    if context.db is None:
        return "Student preferences are unavailable."

    try:
        preference = context.db.get(Preference, context.account_id)
    except Exception:
        return "Student preferences are unavailable."

    if preference is None or not _has_saved_values(preference):
        return "No saved job or event preferences are available for this student."

    parts = []
    if preference.preferred_categories:
        parts.append(f"categories: {preference.preferred_categories}")
    if preference.preferred_cities:
        parts.append(f"cities: {preference.preferred_cities}")
    if preference.min_salary is not None:
        parts.append(f"minimum salary: ${preference.min_salary:,.0f}")
    if preference.preferred_skills:
        parts.append(f"skills: {preference.preferred_skills}")
    if preference.remote_ok:
        parts.append("remote work: accepted")
    return "Saved preferences — " + "; ".join(parts) + "."


def _has_saved_values(preference: Preference) -> bool:
    return any(
        (
            preference.preferred_categories,
            preference.preferred_cities,
            preference.min_salary is not None,
            preference.preferred_skills,
            preference.remote_ok,
        )
    )


TOOL = ToolDefinition(
    name="get_student_preferences",
    description="Use first when the student asks for recommendations based on their saved job or event preferences.",
    parameters={"type": "object", "properties": {}},
    handler=get_student_preferences,
)
