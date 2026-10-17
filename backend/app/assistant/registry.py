"""Select the assistant tools allowed for an authenticated account role."""

from app.assistant.tools.company import company_tool_registry
from app.assistant.tools.schemas import ToolRegistry


STUDENT_ASSISTANT_UNAVAILABLE = "Student assistant tools are not available yet."


def student_tool_registry() -> ToolRegistry:
    """Temporary empty registry; Part B student tools are added in a later slice."""

    return ToolRegistry(role="student", unavailable_message=STUDENT_ASSISTANT_UNAVAILABLE)


def tool_registry_for_role(role: str) -> ToolRegistry:
    role_value = getattr(role, "value", role)
    if role_value == "student":
        return student_tool_registry()
    if role_value == "company":
        return company_tool_registry()
    raise ValueError("Unsupported assistant role")
