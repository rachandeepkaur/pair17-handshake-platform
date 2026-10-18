from collections.abc import Sequence

from app.assistant.agent import run_assistant
from app.assistant.llm_client import MalformedToolCallError
from app.assistant.repair import REPAIR_FAILED_MESSAGE, check_tool_call, needs_tool
from app.assistant.tools.schemas import AssistantContext, AssistantMessage, Message, ToolCall, ToolDefinition, ToolRegistry


CONTEXT = AssistantContext(account_id=1, role="student")


class FakeClient:
    def __init__(self, responses: list[AssistantMessage | Exception]) -> None:
        self.responses = responses
        self.calls: list[list[Message]] = []

    def complete(self, messages: Sequence[Message], tools: Sequence[ToolDefinition]) -> AssistantMessage:
        self.calls.append(list(messages))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def make_registry(ran: list[dict]) -> ToolRegistry:
    def search(_context: AssistantContext, arguments: dict) -> str:
        ran.append(arguments)
        return "Matching jobs:\n- ID 3: Analyst at Acme"

    return ToolRegistry(
        role="student",
        tools=(
            ToolDefinition(
                name="search_jobs",
                description="Search jobs.",
                parameters={
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "enum": ["internship", "full_time"]},
                        "min_salary": {"type": "number"},
                        "remote": {"type": "boolean"},
                        "deadline_on_or_before": {"type": "string", "format": "date"},
                    },
                },
                handler=search,
            ),
        ),
    )


def call(name: str = "search_jobs", **arguments) -> AssistantMessage:
    return AssistantMessage(tool_calls=(ToolCall(name=name, arguments=arguments),))


def test_schema_check_reports_specific_errors() -> None:
    registry = make_registry([])

    kind, error = check_tool_call(ToolCall("search_jobs", {"min_salary": "high", "level": "senior"}), registry)
    assert kind.value == "malformed_arguments"
    assert "'min_salary' must be a number, got 'high'" in error
    assert "unknown argument 'level'" in error

    kind, error = check_tool_call(ToolCall("find_internships", {}), registry)
    assert kind.value == "unknown_tool"
    assert "Available tools: search_jobs" in error

    assert check_tool_call(ToolCall("search_jobs", {"remote": True, "category": None, "min_salary": 5}), registry) is None
    assert check_tool_call(ToolCall("search_jobs", {"remote": "yes"}), registry)[0].value == "malformed_arguments"
    assert check_tool_call(ToolCall("search_jobs", {"deadline_on_or_before": "next week"}), registry) is not None


def test_malformed_call_is_reprompted_once_then_repaired() -> None:
    ran: list[dict] = []
    client = FakeClient([call(min_salary="high"), call(min_salary=90000), AssistantMessage(content="Job 3 pays well.")])

    run = run_assistant("Find higher paying jobs", [], CONTEXT, client, registry=make_registry(ran))

    assert ran == [{"min_salary": 90000}]
    reprompt = client.calls[1][-1]["content"]
    assert reprompt.startswith("TOOL CALL ERROR: search_jobs: 'min_salary' must be a number")
    assert run.answer == "Job 3 pays well."
    assert run.failures == ("malformed_arguments",)
    assert run.repair_attempts == 1
    assert [record.status for record in run.tool_calls] == ["malformed_arguments", "ok"]


def test_second_failure_stops_cleanly() -> None:
    ran: list[dict] = []
    client = FakeClient([call(min_salary="high"), call("find_internships"), AssistantMessage(content="unused")])

    run = run_assistant("Find higher paying jobs", [], CONTEXT, client, registry=make_registry(ran))

    assert ran == []
    assert run.answer == REPAIR_FAILED_MESSAGE
    assert run.stopped_after_failed_repair is True
    assert len(client.calls) == 2
    # Every requested call still has a tool result, so the history stays valid.
    assert [m["role"] for m in run.conversation] == ["user", "assistant", "tool", "assistant", "tool", "assistant"]


def test_unknown_tool_is_reprompted_with_the_tool_list() -> None:
    client = FakeClient([call("find_internships", city="Palo Alto"), call(category="internship"), AssistantMessage(content="Found job 3.")])

    run = run_assistant("Find internships", [], CONTEXT, client, registry=make_registry([]))

    assert "'find_internships' is not a tool. Available tools: search_jobs." in client.calls[1][-1]["content"]
    assert run.answer == "Found job 3."
    assert run.failures == ("unknown_tool",)


def test_text_answer_to_a_data_request_is_reprompted() -> None:
    client = FakeClient(
        [AssistantMessage(content="Google has a great internship."), call(category="internship"), AssistantMessage(content="Found job 3.")]
    )

    run = run_assistant("Find me an internship", [], CONTEXT, client, registry=make_registry([]))

    retry_messages = client.calls[1]
    assert retry_messages[-2] == {"role": "assistant", "content": "Google has a great internship."}
    assert retry_messages[-1]["content"].startswith("[Runtime check]")
    assert run.answer == "Found job 3."
    assert run.failures == ("text_instead_of_tool",)
    # The ungrounded first answer is not kept in the saved history.
    assert all(m.get("content") != "Google has a great internship." for m in run.conversation)


def test_unparsable_tool_call_is_reprompted() -> None:
    client = FakeClient([MalformedToolCallError("tool arguments were not a JSON object."), call(), AssistantMessage(content="Found job 3.")])

    run = run_assistant("Find jobs", [], CONTEXT, client, registry=make_registry([]))

    assert "could not be parsed: tool arguments were not a JSON object." in client.calls[1][-1]["content"]
    assert run.answer == "Found job 3."


def test_small_talk_does_not_need_a_tool() -> None:
    assert needs_tool("Find me a remote data science internship")
    assert needs_tool("Are there any events next month?")
    assert not needs_tool("Thanks for the jobs!")
    assert not needs_tool("Hello there")


def test_repair_disabled_keeps_the_baseline_behaviour() -> None:
    ran: list[dict] = []
    client = FakeClient([call(min_salary="high"), AssistantMessage(content="Here are jobs.")])

    run = run_assistant("Find higher paying jobs", [], CONTEXT, client, registry=make_registry(ran), repair=False)

    assert ran == [{"min_salary": "high"}]
    assert run.answer == "Here are jobs."
    assert run.failures == ("malformed_arguments",)
    assert run.repair_attempts == 0
