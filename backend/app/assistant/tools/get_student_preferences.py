"""Read the current student's saved job and event preferences."""

from typing import Any

from app.assistant.tools.schemas import AssistantContext, ToolDefinition
from app.models.preference import Preference
from app.models.student import Student


def get_student_preferences(context: AssistantContext, _arguments: dict[str, Any]) -> str:
    if context.db is None:
        return "Student preferences are unavailable."

    try:
        preference = context.db.get(Preference, context.account_id)
        student = context.db.get(Student, context.account_id)
    except Exception:
        return "Student preferences are unavailable."

    if preference is None or not _has_saved_values(preference):
        result = "No saved job or event preferences are available for this student."
    else:
        result = "Saved preferences — " + "; ".join(_preference_parts(preference)) + "."

    # The profile is not a preference, but "my city" or "my major" requests
    # need it, so it is reported separately and labelled as profile data.
    profile = _profile_parts(student)
    if profile:
        result += " Student profile — " + "; ".join(profile) + "."
    return result


def _preference_parts(preference: Preference) -> list[str]:
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
    return parts


def _profile_parts(student: Student | None) -> list[str]:
    if student is None:
        return []
    parts = []
    if student.city:
        parts.append(f"city: {student.city}")
    if student.major:
        parts.append(f"major: {student.major}")
    if student.skills:
        parts.append(f"skills: {student.skills}")
    return parts


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
    description=(
        "Return the current student's saved job and event preferences (categories, cities, minimum "
        "salary, skills, remote) plus their profile city, major, and skills. Use this FIRST whenever "
        "the student says 'my city', 'my major', 'for me', or asks for recommendations. Takes no arguments. "
        "States clearly when no preferences are saved."
    ),
    parameters={"type": "object", "properties": {}},
    handler=get_student_preferences,
)
