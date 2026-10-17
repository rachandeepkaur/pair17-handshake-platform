from collections.abc import Sequence

from app.assistant.agent import ITERATION_LIMIT_MESSAGE, run_assistant
from app.assistant.tools.schemas import AssistantContext, AssistantMessage, Message, ToolCall, ToolDefinition, ToolRegistry


class FakeClient:
    def __init__(self, responses: list[AssistantMessage]) -> None:
        self.responses = responses
        self.calls: list[list[Message]] = []

    def complete(self, messages: Sequence[Message], tools: Sequence[ToolDefinition]) -> AssistantMessage:
        self.calls.append(list(messages))
        return self.responses.pop(0)


def search_tool(_context: AssistantContext, arguments: dict[str, object]) -> str:
    return f"Results for {arguments['query']}"


def test_agent_runs_tool_then_returns_final_answer(capsys) -> None:
    client = FakeClient(
        [
            AssistantMessage(tool_calls=(ToolCall(name="search_jobs", arguments={"query": "internship"}),)),
            AssistantMessage(content="I found one internship."),
        ]
    )
    registry = ToolRegistry(
        role="student",
        tools=(
            ToolDefinition(
                name="search_jobs",
                description="Search jobs.",
                parameters={"type": "object", "properties": {}},
                handler=search_tool,
            ),
        ),
    )

    run = run_assistant(
        "Find an internship",
        [],
        AssistantContext(account_id=1, role="student"),
        client,
        registry=registry,
    )

    assert run.answer == "I found one internship."
    assert run.tool_call_count == 1
    assert run.stopped_at_iteration_limit is False
    assert client.calls[1][-1] == {"role": "tool", "tool_name": "search_jobs", "content": "Results for internship"}
    assert "Assistant tool call: search_jobs arguments={'query': 'internship'}" in capsys.readouterr().out


def test_agent_stops_at_the_iteration_ceiling(capsys) -> None:
    client = FakeClient(
        [AssistantMessage(tool_calls=(ToolCall(name="search_jobs", arguments={"query": "internship"}),))]
    )
    registry = ToolRegistry(
        role="student",
        tools=(
            ToolDefinition(
                name="search_jobs",
                description="Search jobs.",
                parameters={"type": "object", "properties": {}},
                handler=search_tool,
            ),
        ),
    )

    run = run_assistant(
        "Find an internship",
        [],
        AssistantContext(account_id=1, role="student"),
        client,
        registry=registry,
        max_iterations=1,
    )

    assert run.answer == ITERATION_LIMIT_MESSAGE
    assert run.stopped_at_iteration_limit is True
    assert run.tool_call_count == 1
    assert "Assistant tool calls: 1" in capsys.readouterr().out


def test_company_placeholder_does_not_call_the_model(capsys) -> None:
    client = FakeClient([])

    run = run_assistant(
        "Show my jobs",
        [],
        AssistantContext(account_id=2, role="company"),
        client,
    )

    assert run.answer == "Company assistant tools are not available yet."
    assert client.calls == []
    assert "Assistant tool calls: 0" in capsys.readouterr().out


def test_agent_repairs_a_promised_search_without_a_tool_call() -> None:
    client = FakeClient(
        [
            AssistantMessage(content="I couldn't find one there. Let me try searching another city."),
            AssistantMessage(tool_calls=(ToolCall(name="search_jobs", arguments={"query": "internship"}),)),
            AssistantMessage(content="There are no matching internships in the other city either."),
        ]
    )
    registry = ToolRegistry(
        role="student",
        tools=(ToolDefinition(name="search_jobs", description="Search jobs.", parameters={}, handler=search_tool),),
    )

    run = run_assistant("Find an internship", [], AssistantContext(account_id=1, role="student"), client, registry=registry)

    assert run.answer == "There are no matching internships in the other city either."
    assert run.tool_call_count == 1
    assert any(message.get("content", "").startswith("Do not promise") for message in client.calls[1])
