"""Tool-call reliability: detect failed calls and build one repair reprompt.

The agent loop checks every model response. A malformed call, a call to an
unknown tool, or a text answer to a request that needed a tool is reported to
the model once with the specific error. If the next response fails again the
loop stops cleanly with REPAIR_FAILED_MESSAGE instead of guessing.
"""

import re
from datetime import date
from enum import Enum
from typing import Any

from app.assistant.tools.schemas import ToolCall, ToolRegistry


# Total reprompts in one run; each failure gets exactly one.
MAX_REPAIR_ATTEMPTS = 2
REPAIR_FAILED_MESSAGE = (
    "I couldn't complete that request reliably, so I stopped instead of guessing. "
    "Please try rephrasing it."
)


class FailureKind(str, Enum):
    MALFORMED_ARGUMENTS = "malformed_arguments"
    UNKNOWN_TOOL = "unknown_tool"
    TEXT_INSTEAD_OF_TOOL = "text_instead_of_tool"


_JSON_TYPES: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "integer": (int,),
    "number": (int, float),
    "boolean": (bool,),
}

# A request for Hirely data: a data noun plus a request cue ("find", "?").
_DATA_NOUN = re.compile(
    r"\b(jobs?|internships?|positions?|roles?|openings?|postings?|events?|fairs?|info sessions?|"
    r"salar(y|ies)|paying|employers?|compan(y|ies)|preferences?|saved?)\b",
    re.IGNORECASE,
)
_REQUEST_CUE = re.compile(
    r"\?|\b(find|show|search|list|look|get|give|tell|recommend|suggest|compare|save|which|what|any|are there)\b",
    re.IGNORECASE,
)


def clean_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    """Drop optional arguments the model sent as null or blank (it means 'not set')."""

    return {
        key: value
        for key, value in arguments.items()
        if value is not None and not (isinstance(value, str) and not value.strip())
    }


def check_tool_call(call: ToolCall, registry: ToolRegistry) -> tuple[FailureKind, str] | None:
    """Validate one call against the registry and the tool's JSON schema."""

    tool = registry.find(call.name)
    if tool is None:
        available = ", ".join(t.name for t in registry.tools)
        return FailureKind.UNKNOWN_TOOL, f"'{call.name}' is not a tool. Available tools: {available}."

    schema = tool.parameters
    properties: dict[str, Any] = schema.get("properties", {})
    arguments = clean_arguments(call.arguments)
    problems = []

    for name in schema.get("required", []):
        if name not in arguments:
            problems.append(f"missing required argument '{name}'")
    for name, value in arguments.items():
        spec = properties.get(name)
        if spec is None:
            allowed = ", ".join(properties) or "none"
            problems.append(f"unknown argument '{name}' (allowed: {allowed})")
            continue
        problem = _value_problem(name, value, spec)
        if problem:
            problems.append(problem)

    if problems:
        return FailureKind.MALFORMED_ARGUMENTS, f"{call.name}: " + "; ".join(problems) + "."
    return None


def _value_problem(name: str, value: Any, spec: dict[str, Any]) -> str | None:
    expected = spec.get("type")
    types = _JSON_TYPES.get(expected)
    # bool is a subclass of int in Python, so it is checked explicitly.
    if types and (not isinstance(value, types) or (expected != "boolean" and isinstance(value, bool))):
        return f"'{name}' must be a {expected}, got {value!r}"
    if "enum" in spec and value not in spec["enum"]:
        return f"'{name}' must be one of {', '.join(spec['enum'])}, got {value!r}"
    if spec.get("format") == "date":
        try:
            date.fromisoformat(value)
        except ValueError:
            return f"'{name}' must be a date in YYYY-MM-DD format, got {value!r}"
    return None


def needs_tool(user_message: str) -> bool:
    """Whether a student message asks for Hirely data, so a tool must be called."""

    return bool(_DATA_NOUN.search(user_message) and _REQUEST_CUE.search(user_message))


def tool_error_reprompt(error: str) -> str:
    """Tool result sent instead of running a failed call."""

    return (
        f"TOOL CALL ERROR: {error} The tool was not run. Correct the call using only the "
        "tools and arguments in your tool list and call it again (one retry allowed)."
    )


def text_instead_of_tool_reprompt() -> str:
    """Runtime message sent when the model answered a data request without a tool."""

    return (
        "[Runtime check] Your previous reply answered without calling a tool, but this request needs "
        "Hirely data. Call the appropriate tool now (search_jobs, get_job_details, search_events, or "
        "get_student_preferences) and answer only from its result (one retry allowed)."
    )


def unparsable_call_reprompt(error: str) -> str:
    return (
        f"[Runtime check] Your previous tool call could not be parsed: {error} "
        "Call the tool again with a JSON object of arguments (one retry allowed)."
    )
