"""Student confirmation for assistant tools that change data.

Only tools in GATED_TOOLS wait for the student; read-only tools run directly.
The agent loop calls confirm_action before every tool call. A PENDING result
pauses the loop and returns the action to the chat UI, which asks the student
and resumes the run with their decision.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


GATED_TOOLS = frozenset({"save_job_or_event"})

CANCELLED_PREFIX = "CANCELLED:"


class Decision(str, Enum):
    APPROVED = "approved"
    DECLINED = "declined"
    PENDING = "pending"


@dataclass(frozen=True)
class PendingAction:
    """A gated tool call that is waiting for the student's decision."""

    tool_name: str
    arguments: dict[str, Any]
    summary: str


def requires_confirmation(tool_name: str) -> bool:
    return tool_name in GATED_TOOLS


def confirm_action(
    tool_name: str,
    arguments: dict[str, Any],
    auto_approve: bool = False,
    *,
    student_decision: bool | None = None,
) -> Decision:
    """Decide whether one requested tool call may run.

    Read-only tools are always approved. A gated tool runs only when
    `auto_approve` is set (scripted evaluations) or the student approved this
    action; an explicit decline cancels it. With no decision yet, it is pending.
    """

    if not requires_confirmation(tool_name) or auto_approve:
        return Decision.APPROVED
    if student_decision is None:
        return Decision.PENDING
    return Decision.APPROVED if student_decision else Decision.DECLINED


def describe_action(tool_name: str, arguments: dict[str, Any]) -> str:
    """A short, student-facing description shown in the confirmation dialog."""

    if tool_name == "save_job_or_event":
        item_type = arguments.get("item_type", "item")
        return f"Save {item_type} {arguments.get('item_id', '?')} to your saved {item_type}s"
    return f"Run {tool_name}"


def pending_action(tool_name: str, arguments: dict[str, Any]) -> PendingAction:
    return PendingAction(tool_name=tool_name, arguments=dict(arguments), summary=describe_action(tool_name, arguments))


def cancellation_message(tool_name: str, arguments: dict[str, Any]) -> str:
    """Tool result returned to the model when the student declines."""

    return (
        f"{CANCELLED_PREFIX} the student declined the action \"{describe_action(tool_name, arguments)}\". "
        "Nothing was changed. Do not call this tool again for this request. Tell the student the action "
        "was cancelled and ask whether they need anything else."
    )


def already_declined_message(tool_name: str) -> str:
    """Tool result for a retry of a gated tool after the student declined."""

    return (
        f"{CANCELLED_PREFIX} {tool_name} was not run because the student already declined this action. "
        "Do not retry it. Acknowledge the student's decision in your answer."
    )
