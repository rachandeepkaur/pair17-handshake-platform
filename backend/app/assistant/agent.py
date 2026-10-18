"""Bounded, hand-built model-and-tool loop for the Lab 1 assistant.

Each run asks the model for the next step, runs the tools it requests, and
stops at a final answer or after `max_iterations` model calls. Part C adds:

- confirmation: a gated tool (save_job_or_event) pauses the run and returns
  a pending action; resume_assistant continues it with the student's decision.
- injection defense: database-reading tool results are wrapped as untrusted
  data (app.assistant.untrusted).
- repair: a failed tool call or a missing required call is reported to the
  model once; a second failure stops the run cleanly (app.assistant.repair).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.assistant.confirmation import (
    Decision,
    PendingAction,
    already_declined_message,
    cancellation_message,
    confirm_action,
    pending_action,
    requires_confirmation,
)
from app.assistant.llm_client import MalformedToolCallError, ModelClient, ModelClientError, ModelTimeoutError
from app.assistant.prompts import system_prompt_for_role
from app.assistant.registry import tool_registry_for_role
from app.assistant.repair import (
    MAX_REPAIR_ATTEMPTS,
    REPAIR_FAILED_MESSAGE,
    FailureKind,
    check_tool_call,
    clean_arguments,
    needs_tool,
    text_instead_of_tool_reprompt,
    tool_error_reprompt,
    unparsable_call_reprompt,
)
from app.assistant.tools.schemas import AssistantContext, Message, ToolCall, ToolRegistry, message_history
from app.assistant.untrusted import wrap_untrusted


MAX_ASSISTANT_ITERATIONS = 5
ITERATION_LIMIT_MESSAGE = "I couldn't complete that request within the assistant's tool-call limit."
MODEL_UNAVAILABLE_MESSAGE = "The assistant is unavailable right now. Please make sure Ollama is running and try again."
MODEL_TIMEOUT_MESSAGE = "The assistant took too long to respond. Please try again in a moment."
EMPTY_ANSWER_MESSAGE = "I wasn't able to put together an answer to that. Could you rephrase your question?"
NOT_RUN_MESSAGE = "Not run: the student sent a new message before deciding."
STOPPED_MESSAGE = "Not run: the assistant stopped after a failed repair."


class NoPendingActionError(ValueError):
    """resume_assistant was called on a conversation with nothing to confirm."""


@dataclass(frozen=True)
class ToolCallRecord:
    """One tool call the model requested and what the loop did with it."""

    name: str
    arguments: dict[str, Any]
    status: str  # "ok", "pending", "declined", or a FailureKind value
    error: str | None = None


@dataclass(frozen=True)
class AssistantRun:
    """The final answer and the updated, caller-owned conversation history."""

    answer: str
    conversation: list[Message]
    tool_call_count: int
    stopped_at_iteration_limit: bool = False
    pending_action: PendingAction | None = None
    tool_calls: tuple[ToolCallRecord, ...] = ()
    failures: tuple[str, ...] = ()
    repair_attempts: int = 0
    stopped_after_failed_repair: bool = False


def run_assistant(
    user_message: str,
    conversation: Sequence[Message],
    context: AssistantContext,
    client: ModelClient,
    *,
    registry: ToolRegistry | None = None,
    max_iterations: int = MAX_ASSISTANT_ITERATIONS,
    auto_approve: bool = False,
    injection_defense: bool = True,
    repair: bool = True,
) -> AssistantRun:
    """Run tools requested by the model until it produces a final answer.

    The system prompt is used for model calls only; returned conversation
    history contains user, assistant, and tool messages suitable for reuse.
    """

    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")

    selected_registry = registry or tool_registry_for_role(context.role)
    history = message_history(conversation)
    _close_unanswered_calls(history)
    history.append({"role": "user", "content": user_message})
    run = _Run(
        history, context, client, selected_registry,
        user_message=user_message, max_iterations=max_iterations,
        auto_approve=auto_approve, injection_defense=injection_defense, repair=repair,
    )

    if not selected_registry.tools and selected_registry.unavailable_message:
        return run.finish(selected_registry.unavailable_message)
    return run.loop()


def resume_assistant(
    conversation: Sequence[Message],
    approved: bool,
    context: AssistantContext,
    client: ModelClient,
    *,
    registry: ToolRegistry | None = None,
    max_iterations: int = MAX_ASSISTANT_ITERATIONS,
    injection_defense: bool = True,
    repair: bool = True,
) -> AssistantRun:
    """Continue a run that paused on a gated tool, using the student's decision."""

    selected_registry = registry or tool_registry_for_role(context.role)
    history = message_history(conversation)
    unresolved = unresolved_tool_calls(history)
    if not unresolved or not requires_confirmation(unresolved[0].name):
        raise NoPendingActionError("There is no action waiting for confirmation.")

    run = _Run(
        history, context, client, selected_registry,
        user_message=None, max_iterations=max_iterations,
        auto_approve=False, injection_defense=injection_defense, repair=repair,
    )
    pending = run.run_tool_calls(unresolved, student_decision=approved)
    if pending:
        return run.pause(pending)
    if run.stopped:
        return run.finish(REPAIR_FAILED_MESSAGE, record=True, failed_repair=True)
    return run.loop()


def unresolved_tool_calls(conversation: Sequence[Message]) -> list[ToolCall]:
    """Tool calls in the last assistant message that have no tool result yet."""

    for index in range(len(conversation) - 1, -1, -1):
        message = conversation[index]
        if message.get("role") == "user":
            return []
        if message.get("role") == "assistant" and message.get("tool_calls"):
            answered = sum(1 for later in conversation[index + 1 :] if later.get("role") == "tool")
            calls = [_tool_call_from_history(call) for call in message["tool_calls"]]
            return calls[answered:]
    return []


def _tool_call_from_history(call: Message) -> ToolCall:
    function = call.get("function", call)
    arguments = function.get("arguments")
    return ToolCall(name=str(function.get("name", "")), arguments=arguments if isinstance(arguments, dict) else {})


def _close_unanswered_calls(history: list[Message]) -> None:
    # The student typed a new message instead of answering a confirmation, so
    # the waiting action is treated as declined and the history stays paired.
    for call in unresolved_tool_calls(history):
        content = cancellation_message(call.name, call.arguments) if requires_confirmation(call.name) else NOT_RUN_MESSAGE
        history.append({"role": "tool", "tool_name": call.name, "content": content})


class _Run:
    """Mutable state for one request: history, counters, and repair budget."""

    def __init__(
        self,
        history: list[Message],
        context: AssistantContext,
        client: ModelClient,
        registry: ToolRegistry,
        *,
        user_message: str | None,
        max_iterations: int,
        auto_approve: bool,
        injection_defense: bool,
        repair: bool,
    ) -> None:
        self.history = history
        self.context = context
        self.client = client
        self.registry = registry
        self.user_message = user_message
        self.max_iterations = max_iterations
        self.auto_approve = auto_approve
        self.injection_defense = injection_defense
        self.repair = repair

        self.iterations = 0
        self.tool_call_count = 0
        self.records: list[ToolCallRecord] = []
        self.failures: list[str] = []
        self.repair_attempts = 0
        self.awaiting_repair = False
        self.stopped = False
        self.declined = False
        # Repair prompts sent with the next model call only, never saved.
        self.transient: list[Message] = []

    def loop(self) -> AssistantRun:
        while self.iterations < self.max_iterations:
            self.iterations += 1
            model_messages = [
                {"role": "system", "content": system_prompt_for_role(self.context.role, self.injection_defense)},
                *message_history(self.history),
                *self.transient,
            ]
            self.transient = []
            try:
                assistant_message = self.client.complete(model_messages, self.registry.tools)
            except ModelTimeoutError:
                return self.finish(MODEL_TIMEOUT_MESSAGE, record=True)
            except MalformedToolCallError as exc:
                if self.start_repair(FailureKind.MALFORMED_ARGUMENTS):
                    self.transient = [{"role": "user", "content": unparsable_call_reprompt(str(exc))}]
                    continue
                if self.repair:
                    return self.finish(REPAIR_FAILED_MESSAGE, record=True, failed_repair=True)
                return self.finish(MODEL_UNAVAILABLE_MESSAGE, record=True)
            except ModelClientError:
                return self.finish(MODEL_UNAVAILABLE_MESSAGE, record=True)

            if not assistant_message.tool_calls:
                if self.skipped_required_tool():
                    if self.start_repair(FailureKind.TEXT_INSTEAD_OF_TOOL):
                        self.transient = [
                            assistant_message.as_ollama_message(),
                            {"role": "user", "content": text_instead_of_tool_reprompt()},
                        ]
                        continue
                    if self.repair:
                        return self.finish(REPAIR_FAILED_MESSAGE, record=True, failed_repair=True)
                self.awaiting_repair = False
                if not assistant_message.content.strip():
                    return self.finish(EMPTY_ANSWER_MESSAGE, record=True)
                self.history.append(assistant_message.as_ollama_message())
                return self.finish(assistant_message.content)

            self.history.append(assistant_message.as_ollama_message())
            pending = self.run_tool_calls(assistant_message.tool_calls)
            if pending:
                return self.pause(pending)
            if self.stopped:
                return self.finish(REPAIR_FAILED_MESSAGE, record=True, failed_repair=True)

        return self.finish(ITERATION_LIMIT_MESSAGE, record=True, iteration_limit=True)

    def skipped_required_tool(self) -> bool:
        """A text answer to a data request before any tool ran in this run."""

        return (
            self.user_message is not None
            and not self.records
            and bool(self.registry.tools)
            and needs_tool(self.user_message)
        )

    def run_tool_calls(self, calls: Sequence[ToolCall], *, student_decision: bool | None = None) -> PendingAction | None:
        response_failed = False
        repair_allowed: bool | None = None

        for position, call in enumerate(calls):
            if self.stopped:
                self.add_tool_result(call.name, STOPPED_MESSAGE)
                continue

            problem = check_tool_call(call, self.registry)
            if problem:
                kind, error = problem
                response_failed = True
                self.record(call, kind.value, error)
                if not self.repair:
                    # Baseline: run the call as requested, as the loop did before repair.
                    self.execute(call.name, call.arguments)
                    continue
                if repair_allowed is None:
                    repair_allowed = self.start_repair(kind, already_recorded=True)
                if repair_allowed:
                    self.add_tool_result(call.name, tool_error_reprompt(error))
                else:
                    self.stopped = True
                    self.add_tool_result(call.name, f"Not run: {error}")
                continue

            arguments = clean_arguments(call.arguments) if self.repair else call.arguments
            if requires_confirmation(call.name) and self.declined:
                self.record(call, "declined")
                self.add_tool_result(call.name, already_declined_message(call.name))
                continue

            decision = confirm_action(
                call.name,
                arguments,
                self.auto_approve,
                student_decision=student_decision if position == 0 else None,
            )
            if decision is Decision.PENDING:
                print(f"Assistant tool call awaiting confirmation: {call.name} arguments={arguments}")
                self.records.append(ToolCallRecord(call.name, dict(arguments), "pending"))
                return pending_action(call.name, arguments)
            if decision is Decision.DECLINED:
                self.declined = True
                self.record(call, "declined")
                self.add_tool_result(call.name, cancellation_message(call.name, arguments))
                continue

            self.record(call, "ok")
            self.execute(call.name, arguments)

        if not response_failed:
            self.awaiting_repair = False
        return None

    def start_repair(self, kind: FailureKind, *, already_recorded: bool = False) -> bool:
        """Record a failure; return True if the model gets one reprompt for it."""

        if not already_recorded:
            self.failures.append(kind.value)
        if not self.repair or self.awaiting_repair or self.repair_attempts >= MAX_REPAIR_ATTEMPTS:
            return False
        self.repair_attempts += 1
        self.awaiting_repair = True
        print(f"Assistant repair attempt {self.repair_attempts}: {kind.value}")
        return True

    def record(self, call: ToolCall, status: str, error: str | None = None) -> None:
        self.tool_call_count += 1
        print(f"Assistant tool call: {call.name} arguments={call.arguments}")
        self.records.append(ToolCallRecord(call.name, dict(call.arguments), status, error))
        if error is not None:
            self.failures.append(status)

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> None:
        result = self.registry.run(tool_name, self.context, arguments)
        if self.injection_defense:
            result = wrap_untrusted(tool_name, result)
        self.add_tool_result(tool_name, result)

    def add_tool_result(self, tool_name: str, content: str) -> None:
        self.history.append({"role": "tool", "tool_name": tool_name, "content": content})

    def pause(self, pending: PendingAction) -> AssistantRun:
        print(f"Assistant tool calls: {self.tool_call_count}")
        return self._result(f"Please confirm: {pending.summary}.", pending_action=pending)

    def finish(
        self,
        answer: str,
        *,
        record: bool = False,
        iteration_limit: bool = False,
        failed_repair: bool = False,
    ) -> AssistantRun:
        # `record` adds a fallback answer to the history so the caller (and the
        # chat UI, which renders the history) shows the same reply it returns.
        if record:
            self.history.append({"role": "assistant", "content": answer})
        print(f"Assistant tool calls: {self.tool_call_count}")
        return self._result(answer, iteration_limit=iteration_limit, failed_repair=failed_repair)

    def _result(
        self,
        answer: str,
        *,
        pending_action: PendingAction | None = None,
        iteration_limit: bool = False,
        failed_repair: bool = False,
    ) -> AssistantRun:
        return AssistantRun(
            answer=answer,
            conversation=self.history,
            tool_call_count=self.tool_call_count,
            stopped_at_iteration_limit=iteration_limit,
            pending_action=pending_action,
            tool_calls=tuple(self.records),
            failures=tuple(self.failures),
            repair_attempts=self.repair_attempts,
            stopped_after_failed_repair=failed_repair,
        )
