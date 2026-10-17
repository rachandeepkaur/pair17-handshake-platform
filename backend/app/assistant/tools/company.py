"""Company-role assistant placeholder.

This registry intentionally contains no callable tools until company tool
handlers are implemented.
"""

from app.assistant.tools.schemas import ToolRegistry


COMPANY_ASSISTANT_UNAVAILABLE = "Company assistant tools are not available yet."


def company_tool_registry() -> ToolRegistry:
    return ToolRegistry(role="company", unavailable_message=COMPANY_ASSISTANT_UNAVAILABLE)
