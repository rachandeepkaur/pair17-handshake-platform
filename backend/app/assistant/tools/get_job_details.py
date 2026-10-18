"""Return complete details for one visible job."""

from typing import Any

from app.assistant.tools.schemas import AssistantContext, ToolDefinition
from app.core.exceptions import AppError
from app.services import student_job_service


def get_job_details(context: AssistantContext, arguments: dict[str, Any]) -> str:
    if context.db is None:
        return "Job details are unavailable."
    job_id = arguments.get("job_id")
    if not isinstance(job_id, int) or isinstance(job_id, bool) or job_id < 1:
        return "job_id must be a positive integer."

    try:
        job = student_job_service.get_job(context.db, job_id)
    except AppError as exc:
        return f"Job {job_id} was not found: {exc.message}."
    except Exception:
        return "Job details could not be retrieved."

    salary = f"${job.salary:,.0f}" if job.salary is not None else "not listed"
    return (
        f"Job {job.id}: {job.title} at {job.company_name}\n"
        f"Location: {job.location or job.city} ({'remote' if job.is_remote else 'on-site'})\n"
        f"Category: {job.category}; salary: {salary}; deadline: {job.deadline.isoformat()}\n"
        f"Required skills: {job.skills_required or 'not listed'}\n"
        f"Description: {job.description or 'not listed'}\n"
        f"Company: {job.company_name}; {job.company_description or 'description not listed'}\n"
        f"Contact: {job.company_contact_info or 'not listed'}\n"
        f"Posted: {job.posting_date.isoformat()}"
    )


TOOL = ToolDefinition(
    name="get_job_details",
    description=(
        "Return full details for one job: description, skills, salary, deadline, company details, contact, "
        "and posting date. Use after search_jobs when the student asks about a specific job ID. Returns "
        "an error message if the ID does not exist."
    ),
    parameters={
        "type": "object",
        "required": ["job_id"],
        "properties": {"job_id": {"type": "integer", "description": "The numeric job ID shown by search_jobs."}},
    },
    handler=get_job_details,
)
