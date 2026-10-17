"""Bounded, hand-built model-and-tool loop for the Lab 1 assistant."""

from collections.abc import Sequence
from dataclasses import dataclass
import re

from app.assistant.llm_client import ModelClient, ModelClientError
from app.assistant.prompts import system_prompt_for_role
from app.assistant.registry import tool_registry_for_role
from app.assistant.tools.schemas import AssistantContext, Message, ToolRegistry, message_history


MAX_ASSISTANT_ITERATIONS = 5
ITERATION_LIMIT_MESSAGE = "I couldn't complete that request within the assistant's tool-call limit."
MODEL_UNAVAILABLE_MESSAGE = "The assistant is unavailable right now. Please make sure Ollama is running and try again."
# A final response cannot promise another lookup. Allow ordinary filler words
# ("let me try searching", "I'll go ahead and check") between the promise
# and the action verb instead of matching only one exact phrasing.
FUTURE_ACTION_PATTERN = re.compile(
    r"\b(?:let me|i(?:'ll| will)|i can)\b[^.!?]{0,80}\b(?:check|search(?:ing)?|look(?:ing)?(?: up)?|find(?:ing)?|try(?:ing)?)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AssistantRun:
    """The final answer and the updated, caller-owned conversation history."""

    answer: str
    conversation: list[Message]
    tool_call_count: int
    stopped_at_iteration_limit: bool = False
    pending_confirmation: dict | None = None


def run_assistant(
    user_message: str,
    conversation: Sequence[Message],
    context: AssistantContext,
    client: ModelClient,
    *,
    registry: ToolRegistry | None = None,
    max_iterations: int = MAX_ASSISTANT_ITERATIONS,
) -> AssistantRun:
    """Run tools requested by the model until it produces a final answer.

    The system prompt is used for model calls only; returned conversation
    history contains user, assistant, and tool messages suitable for reuse.
    """

    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")

    selected_registry = registry or tool_registry_for_role(context.role)
    updated_conversation = message_history(conversation)
    updated_conversation.append({"role": "user", "content": user_message})
    tool_call_count = 0
    followup_repair_used = False

    if not selected_registry.tools and selected_registry.unavailable_message:
        return _finish(
            selected_registry.unavailable_message,
            updated_conversation,
            tool_call_count,
        )

    for _ in range(max_iterations):
        model_messages = [
            {"role": "system", "content": system_prompt_for_role(context.role)},
            *message_history(updated_conversation),
        ]
        try:
            assistant_message = client.complete(model_messages, selected_registry.tools)
        except ModelClientError:
            return _finish(MODEL_UNAVAILABLE_MESSAGE, updated_conversation, tool_call_count)

        updated_conversation.append(assistant_message.as_ollama_message())
        if not assistant_message.tool_calls:
            if _promises_unfinished_action(assistant_message.content) and not followup_repair_used:
                followup_repair_used = True
                updated_conversation.append(
                    {
                        "role": "user",
                        "content": (
                            "Do not promise a future search or check. If another lookup is needed, call the "
                            "appropriate tool now; otherwise give a complete final answer."
                        ),
                    }
                )
                continue
            return _finish(assistant_message.content, updated_conversation, tool_call_count)

        for tool_call in assistant_message.tool_calls:
            tool_call_count += 1
            print(f"Assistant tool call: {tool_call.name} arguments={tool_call.arguments}")
            tool = selected_registry.find(tool_call.name)
            if tool and tool.requires_confirmation:
                return AssistantRun(
                    answer="Please confirm before I save that item.",
                    conversation=updated_conversation,
                    tool_call_count=tool_call_count,
                    pending_confirmation={
                        "tool_name": tool_call.name,
                        "arguments": tool_call.arguments,
                        "prompt": f"Save this {tool_call.arguments.get('item_type', 'item')}?",
                    },
                )
            result = selected_registry.run(tool_call.name, context, tool_call.arguments)
            updated_conversation.append(
                {
                    "role": "tool",
                    "tool_name": tool_call.name,
                    "content": result,
                }
            )

    return _finish(
        ITERATION_LIMIT_MESSAGE,
        updated_conversation,
        tool_call_count,
        stopped_at_iteration_limit=True,
    )


def _promises_unfinished_action(content: str) -> bool:
    """Detect a non-final assistant reply that claims it will perform a lookup."""
    return bool(FUTURE_ACTION_PATTERN.search(content or ""))


def _finish(
    answer: str,
    conversation: list[Message],
    tool_call_count: int,
    *,
    stopped_at_iteration_limit: bool = False,
) -> AssistantRun:
    print(f"Assistant tool calls: {tool_call_count}")
    return AssistantRun(
        answer=answer,
        conversation=conversation,
        tool_call_count=tool_call_count,
        stopped_at_iteration_limit=stopped_at_iteration_limit,
    )
