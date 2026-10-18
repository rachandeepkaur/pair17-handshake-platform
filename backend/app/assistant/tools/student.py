"""Student tool registry for the Lab 1 assistant."""

from app.assistant.tools.get_job_details import TOOL as GET_JOB_DETAILS
from app.assistant.tools.get_student_preferences import TOOL as GET_STUDENT_PREFERENCES
from app.assistant.tools.get_platform_options import TOOL as GET_PLATFORM_OPTIONS
from app.assistant.tools.search_events import TOOL as SEARCH_EVENTS
from app.assistant.tools.search_jobs import TOOL as SEARCH_JOBS
from app.assistant.tools.save_job_or_event import TOOL as SAVE_JOB_OR_EVENT
from app.assistant.tools.schemas import ToolRegistry


def student_tool_registry() -> ToolRegistry:
    return ToolRegistry(
        role="student",
        tools=(GET_STUDENT_PREFERENCES, GET_PLATFORM_OPTIONS, SEARCH_JOBS, GET_JOB_DETAILS, SEARCH_EVENTS, SAVE_JOB_OR_EVENT),
    )
