"""The only module that communicates with the local Ollama service."""

from collections.abc import Sequence
from functools import lru_cache
from typing import Protocol

import httpx

from app.assistant.tools.schemas import AssistantMessage, Message, ToolCall, ToolDefinition, message_history
from app.config import settings


class ModelClientError(RuntimeError):
    """A safe error for unavailable or malformed model responses."""


class ModelTimeoutError(ModelClientError):
    """The model did not answer within the configured timeout."""


class MalformedToolCallError(ModelClientError):
    """The model requested a tool call that could not be parsed."""


class ModelClient(Protocol):
    """Interface used by the agent loop and deterministic test clients."""

    def complete(self, messages: Sequence[Message], tools: Sequence[ToolDefinition]) -> AssistantMessage:
        """Return the next assistant message for this conversation."""


class OllamaClient:
    """Synchronous client for Ollama's `/api/chat` endpoint."""

    def __init__(
        self,
        *,
        host: str | None = None,
        model: str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.host = (host or settings.ollama_host).rstrip("/")
        self.model = model or settings.ollama_model
        self._http_client = http_client or httpx.Client(timeout=settings.ollama_timeout_seconds)

    def complete(self, messages: Sequence[Message], tools: Sequence[ToolDefinition]) -> AssistantMessage:
        payload = {
            "model": self.model,
            "messages": message_history(messages),
            "tools": [tool.as_ollama_tool() for tool in tools],
            "stream": False,
            # The agent loop, rather than the model's reasoning mode, handles
            # multi-step work. This keeps Qwen's tool calls within the timeout.
            "think": False,
            "options": {"num_ctx": settings.ollama_num_ctx},
        }
        try:
            response = self._http_client.post(f"{self.host}/api/chat", json=payload)
            response.raise_for_status()
            body = response.json()
        except httpx.TimeoutException as exc:
            raise ModelTimeoutError("The local model did not respond in time.") from exc
        except httpx.HTTPError as exc:
            raise ModelClientError("The local Ollama service is unavailable.") from exc
        except ValueError as exc:
            raise ModelClientError("Ollama returned an invalid response.") from exc

        raw_message = body.get("message") if isinstance(body, dict) else None
        if not isinstance(raw_message, dict):
            raise ModelClientError("Ollama returned a response without a message.")

        return AssistantMessage(
            content=str(raw_message.get("content") or ""),
            tool_calls=tuple(self._parse_tool_calls(raw_message.get("tool_calls", []))),
        )

    @staticmethod
    def _parse_tool_calls(raw_calls: object) -> list[ToolCall]:
        if raw_calls is None:
            return []
        if not isinstance(raw_calls, list):
            raise MalformedToolCallError("tool_calls was not a list.")

        tool_calls = []
        for raw_call in raw_calls:
            if not isinstance(raw_call, dict):
                raise MalformedToolCallError("a tool call was not a JSON object.")
            function = raw_call.get("function")
            if not isinstance(function, dict) or not isinstance(function.get("name"), str):
                raise MalformedToolCallError("a tool call had no function name.")
            arguments = function.get("arguments", {})
            if not isinstance(arguments, dict):
                raise MalformedToolCallError("tool arguments were not a JSON object.")
            index = function.get("index")
            tool_calls.append(
                ToolCall(
                    name=function["name"],
                    arguments=arguments,
                    index=index if isinstance(index, int) else None,
                )
            )
        return tool_calls


@lru_cache
def get_model_client() -> OllamaClient:
    """Provide one reusable local-model client to assistant API requests."""

    return OllamaClient()
