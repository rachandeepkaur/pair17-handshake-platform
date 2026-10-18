"""Search visible jobs for the authenticated student."""

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from app.assistant.tools.schemas import AssistantContext, ToolDefinition
from app.services import student_job_service


def search_jobs(context: AssistantContext, arguments: dict[str, Any]) -> str:
    if context.db is None:
        return "Job search is unavailable."

    min_salary, salary_error = _decimal_argument(arguments, "min_salary")
    if salary_error:
        return salary_error
    deadline, deadline_error = _date_argument(arguments, "deadline_on_or_before")
    if deadline_error:
        return deadline_error
    remote, remote_error = _boolean_argument(arguments, "remote")
    if remote_error:
        return remote_error

    try:
        jobs = student_job_service.list_jobs(
            context.db,
            title=_text_argument(arguments, "title"),
            company=_text_argument(arguments, "company"),
            category=_text_argument(arguments, "category"),
            city=_text_argument(arguments, "city"),
            min_salary=min_salary,
            skills=_text_argument(arguments, "skills"),
            deadline_on_or_before=deadline,
            remote=remote,
            limit=10,
        ).items
    except Exception:
        return "Job search could not be completed."

    if not jobs:
        return "No matching jobs found."

    return "Matching jobs:\n" + "\n".join(
        f"- ID {job.id}: {job.title} at {job.company_name} | {job.location or job.city} | "
        f"{job.category} | {_salary(job.salary)} | deadline {job.deadline.isoformat()}"
        for job in jobs
    )


def _text_argument(arguments: dict[str, Any], name: str) -> str | None:
    value = arguments.get(name)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _decimal_argument(arguments: dict[str, Any], name: str) -> tuple[Decimal | None, str | None]:
    value = arguments.get(name)
    if value is None:
        return None, None
    if isinstance(value, bool):
        return None, f"{name} must be a number."
    try:
        return Decimal(str(value)), None
    except (InvalidOperation, ValueError):
        return None, f"{name} must be a number."


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


def _salary(value: Decimal | None) -> str:
    return f"${value:,.0f}" if value is not None else "salary not listed"


TOOL = ToolDefinition(
    name="search_jobs",
    description=(
        "Search open job postings. Use whenever the student asks for jobs or internships, including "
        "follow-ups that narrow a previous search (closer, higher paying, different skill). Returns up to "
        "10 jobs with id, title, company, location, category, salary, and deadline, or a plain "
        "no-match message. Only report jobs this tool returns."
    ),
    parameters={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Words that must appear in the job title, e.g. 'data science'."},
            "company": {"type": "string", "description": "Words that must appear in the company name, e.g. 'Google'."},
            "category": {
                "type": "string",
                "enum": ["full_time", "part_time", "on_campus", "internship"],
                "description": "Employment type. Use 'internship' for internships.",
            },
            "city": {"type": "string", "description": "City the job is in, e.g. the student's own city for 'near me'."},
            "min_salary": {"type": "number", "description": "Lowest acceptable listed salary in US dollars; use for 'higher paying'."},
            "skills": {"type": "string", "description": "Comma-separated skills; a job matches only if it requires all of them, so pass one or two key skills."},
            "deadline_on_or_before": {
                "type": "string",
                "format": "date",
                "description": "Only jobs whose application deadline is on or before this date (YYYY-MM-DD).",
            },
            "remote": {"type": "boolean", "description": "true for remote jobs only, false for on-site only; omit if not specified."},
        },
    },
    handler=search_jobs,
)
