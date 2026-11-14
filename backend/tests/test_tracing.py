import logging

from app.assistant.agent import run_assistant
from app.assistant.tools.schemas import AssistantContext, AssistantMessage, ToolCall, ToolDefinition, ToolRegistry


class FakeClient:
    def complete(self, _messages, _tools):
        return AssistantMessage(tool_calls=(ToolCall(name="lookup", arguments={}),))


def test_assistant_trace_logs_model_and_tool_timings(caplog) -> None:
    registry = ToolRegistry(
        role="student",
        tools=(ToolDefinition("lookup", "", {}, lambda _context, _arguments: "result"),),
    )
    with caplog.at_level(logging.INFO, logger="p17.assistant.trace"):
        run_assistant(
            "Look this up",
            [],
            AssistantContext(account_id=1, role="student"),
            FakeClient(),
            registry=registry,
            max_iterations=1,
            trace_id="trace-1",
        )

    assert "trace_id=trace-1 operation=model" in caplog.text
    assert "trace_id=trace-1 operation=tool" in caplog.text
