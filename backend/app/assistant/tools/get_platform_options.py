"""Return stable platform metadata that is not stored in a single job/event row."""

from typing import Any

from app.assistant.tools.schemas import AssistantContext, ToolDefinition
from app.config import settings


JOB_CATEGORIES = ("full_time", "part_time", "on_campus", "internship")


def get_platform_options(_context: AssistantContext, _arguments: dict[str, Any]) -> str:
    """Expose the configured search vocabulary to the assistant as data."""
    cities = ", ".join(settings.cities) or "No cities are configured."
    categories = ", ".join(JOB_CATEGORIES)
    return f"Available cities: {cities}. Job categories: {categories}."


TOOL = ToolDefinition(
    name="get_platform_options",
    description="Use for available cities, supported job categories, or other platform search options.",
    parameters={"type": "object", "properties": {}},
    handler=get_platform_options,
)
