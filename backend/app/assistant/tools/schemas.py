"""Tool contracts shared by the assistant loop and role-specific tools."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session


Message = dict[str, Any]


@dataclass(frozen=True)
class AssistantContext:
    """Authenticated identity supplied to every assistant tool."""

    account_id: int
    role: str
    db: Session | None = None


@dataclass(frozen=True)
class ToolCall:
    """One function call requested by the model."""

    name: str
    arguments: dict[str, Any]
    index: int | None = None


@dataclass(frozen=True)
class AssistantMessage:
    """Normalized model response that can be appended to Ollama history."""

    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()

    def as_ollama_message(self) -> Message:
        message: Message = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            tool_calls = []
            for call in self.tool_calls:
                function: Message = {"name": call.name, "arguments": call.arguments}
                if call.index is not None:
                    function["index"] = call.index
                tool_calls.append({"type": "function", "function": function})
            message["tool_calls"] = tool_calls
        return message


ToolHandler = Callable[[AssistantContext, dict[str, Any]], str]


@dataclass(frozen=True)
class ToolDefinition:
    """A JSON-schema tool definition plus its local string-returning handler."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler
    requires_confirmation: bool = False

    def as_ollama_tool(self) -> Message:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass(frozen=True)
class ToolRegistry:
    """The tools available to one authenticated role."""

    role: str
    tools: tuple[ToolDefinition, ...] = ()
    unavailable_message: str | None = None
    _by_name: Mapping[str, ToolDefinition] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        names = [tool.name for tool in self.tools]
        if len(names) != len(set(names)):
            raise ValueError("Tool names must be unique within a registry")
        object.__setattr__(self, "_by_name", {tool.name: tool for tool in self.tools})

    @property
    def schemas(self) -> list[Message]:
        return [tool.as_ollama_tool() for tool in self.tools]

    def find(self, tool_name: str) -> ToolDefinition | None:
        return self._by_name.get(tool_name)

    def run(self, tool_name: str, context: AssistantContext, arguments: dict[str, Any]) -> str:
        tool = self.find(tool_name)
        if tool is None:
            return f"Unknown tool: {tool_name}."
        try:
            return str(tool.handler(context, arguments))
        except Exception:
            return f"The {tool_name} tool could not complete that request."


def message_history(messages: Sequence[Message]) -> list[Message]:
    """Copy caller-owned history before a model client sends it."""

    return [dict(message) for message in messages]
