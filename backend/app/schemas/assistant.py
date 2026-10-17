from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class AssistantToolCallPayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    arguments: dict[str, Any] = Field(default_factory=dict)
    index: int | None = Field(default=None, ge=0)


class AssistantConversationMessage(BaseModel):
    role: Literal["user", "assistant", "tool"]
    content: str = Field(default="", max_length=4_000)
    tool_name: str | None = Field(default=None, min_length=1, max_length=100)
    tool_calls: list[AssistantToolCallPayload] = Field(default_factory=list, max_length=10)

    @field_validator("tool_calls", mode="before")
    @classmethod
    def unwrap_ollama_tool_calls(cls, value: Any) -> Any:
        if not isinstance(value, list):
            return value
        return [call.get("function", call) if isinstance(call, dict) else call for call in value]

    @model_validator(mode="after")
    def validate_tool_fields(self) -> "AssistantConversationMessage":
        if self.role == "tool" and self.tool_name is None:
            raise ValueError("tool_name is required for tool messages")
        if self.role != "tool" and self.tool_name is not None:
            raise ValueError("tool_name is only valid for tool messages")
        if self.role != "assistant" and self.tool_calls:
            raise ValueError("tool_calls are only valid for assistant messages")
        return self

    def as_message(self) -> dict[str, Any]:
        message: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_name:
            message["tool_name"] = self.tool_name
        if self.tool_calls:
            message["tool_calls"] = [
                {
                    "type": "function",
                    "function": call.model_dump(exclude_none=True),
                }
                for call in self.tool_calls
            ]
        return message


class AssistantChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)
    conversation: list[AssistantConversationMessage] = Field(default_factory=list, max_length=50)

    @field_validator("message")
    @classmethod
    def clean_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message cannot be blank")
        return value


class AssistantChatResponse(BaseModel):
    answer: str
    conversation: list[AssistantConversationMessage]
    tool_call_count: int
    stopped_at_iteration_limit: bool
