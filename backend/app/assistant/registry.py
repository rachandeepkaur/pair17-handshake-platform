"""Select the assistant tools allowed for an authenticated account role."""

from app.assistant.tools.company import company_tool_registry
from app.assistant.tools.schemas import ToolRegistry
from app.assistant.tools.student import student_tool_registry


def tool_registry_for_role(role: str) -> ToolRegistry:
    role_value = getattr(role, "value", role)
    if role_value == "student":
        return student_tool_registry()
    if role_value == "company":
        return company_tool_registry()
    raise ValueError("Unsupported assistant role")
