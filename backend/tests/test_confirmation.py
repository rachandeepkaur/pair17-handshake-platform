from collections.abc import Sequence

from fastapi.testclient import TestClient

from app.assistant.agent import resume_assistant, run_assistant
from app.assistant.confirmation import CANCELLED_PREFIX, Decision, confirm_action
from app.assistant.llm_client import get_model_client
from app.assistant.tools.schemas import AssistantContext, AssistantMessage, Message, ToolCall, ToolDefinition, ToolRegistry
from app.database import get_db
from app.dependencies import get_current_user
from app.main import app
from app.models.account import Account, AccountRole


SAVE_CALL = ToolCall(name="save_job_or_event", arguments={"item_type": "job", "item_id": 7})
CONTEXT = AssistantContext(account_id=1, role="student")


class FakeClient:
    def __init__(self, responses: list[AssistantMessage]) -> None:
        self.responses = responses
        self.calls: list[list[Message]] = []

    def complete(self, messages: Sequence[Message], tools: Sequence[ToolDefinition]) -> AssistantMessage:
        self.calls.append(list(messages))
        return self.responses.pop(0)


def make_registry(saved: list[dict]) -> ToolRegistry:
    def save(_context: AssistantContext, arguments: dict) -> str:
        saved.append(arguments)
        return f"Saved {arguments['item_type']} {arguments['item_id']} for this student."

    return ToolRegistry(
        role="student",
        tools=(
            ToolDefinition(
                name="search_jobs",
                description="Search jobs.",
                parameters={"type": "object", "properties": {"title": {"type": "string"}}},
                handler=lambda _context, _arguments: "Matching jobs:\n- ID 7: Data Intern at Acme",
            ),
            ToolDefinition(
                name="save_job_or_event",
                description="Save a job or event.",
                parameters={
                    "type": "object",
                    "required": ["item_type", "item_id"],
                    "properties": {
                        "item_type": {"type": "string", "enum": ["job", "event"]},
                        "item_id": {"type": "integer"},
                    },
                },
                handler=save,
            ),
        ),
    )


def test_confirm_action_gates_only_write_tools() -> None:
    assert confirm_action("search_jobs", {}) is Decision.APPROVED
    assert confirm_action("get_job_details", {"job_id": 1}) is Decision.APPROVED
    assert confirm_action("save_job_or_event", {"item_type": "job", "item_id": 7}) is Decision.PENDING
    assert confirm_action("save_job_or_event", {}, auto_approve=True) is Decision.APPROVED
    assert confirm_action("save_job_or_event", {}, student_decision=True) is Decision.APPROVED
    assert confirm_action("save_job_or_event", {}, student_decision=False) is Decision.DECLINED


def test_gated_tool_pauses_without_running() -> None:
    saved: list[dict] = []
    client = FakeClient([AssistantMessage(tool_calls=(SAVE_CALL,))])

    run = run_assistant("Save job 7", [], CONTEXT, client, registry=make_registry(saved))

    assert saved == []
    assert run.pending_action is not None
    assert run.pending_action.tool_name == "save_job_or_event"
    assert run.pending_action.summary == "Save job 7 to your saved jobs"
    assert run.conversation[-1]["tool_calls"][0]["function"]["name"] == "save_job_or_event"
    assert len(client.calls) == 1


def test_read_only_tools_are_not_gated() -> None:
    client = FakeClient(
        [
            AssistantMessage(tool_calls=(ToolCall(name="search_jobs", arguments={"title": "data"}),)),
            AssistantMessage(content="Job 7 is a Data Intern role at Acme."),
        ]
    )

    run = run_assistant("Find data jobs", [], CONTEXT, client, registry=make_registry([]))

    assert run.pending_action is None
    assert run.answer == "Job 7 is a Data Intern role at Acme."


def test_decline_returns_cancellation_and_model_acknowledges_without_retrying(capsys) -> None:
    saved: list[dict] = []
    registry = make_registry(saved)
    paused = run_assistant("Save job 7", [], CONTEXT, FakeClient([AssistantMessage(tool_calls=(SAVE_CALL,))]), registry=registry)
    client = FakeClient([AssistantMessage(content="Okay, I cancelled that. Job 7 was not saved.")])

    run = resume_assistant(paused.conversation, False, CONTEXT, client, registry=registry)

    assert saved == []
    tool_result = client.calls[0][-1]
    assert tool_result["role"] == "tool" and tool_result["content"].startswith(CANCELLED_PREFIX)
    assert "Do not call this tool again" in tool_result["content"]
    assert run.answer == "Okay, I cancelled that. Job 7 was not saved."
    assert [record.status for record in run.tool_calls] == ["declined"]
    assert len(client.calls) == 1


def test_retry_after_decline_is_blocked_without_asking_again() -> None:
    saved: list[dict] = []
    registry = make_registry(saved)
    paused = run_assistant("Save job 7", [], CONTEXT, FakeClient([AssistantMessage(tool_calls=(SAVE_CALL,))]), registry=registry)
    client = FakeClient(
        [
            AssistantMessage(tool_calls=(SAVE_CALL,)),
            AssistantMessage(content="Understood, I won't save it."),
        ]
    )

    run = resume_assistant(paused.conversation, False, CONTEXT, client, registry=registry)

    assert saved == []
    assert run.pending_action is None
    assert run.answer == "Understood, I won't save it."
    assert [record.status for record in run.tool_calls] == ["declined", "declined"]


def test_approve_runs_the_tool_once() -> None:
    saved: list[dict] = []
    registry = make_registry(saved)
    paused = run_assistant("Save job 7", [], CONTEXT, FakeClient([AssistantMessage(tool_calls=(SAVE_CALL,))]), registry=registry)
    client = FakeClient([AssistantMessage(content="Saved job 7.")])

    run = resume_assistant(paused.conversation, True, CONTEXT, client, registry=registry)

    assert saved == [{"item_type": "job", "item_id": 7}]
    assert run.answer == "Saved job 7."
    assert client.calls[0][-1]["content"] == "Saved job 7 for this student."


def test_auto_approve_runs_without_pausing() -> None:
    saved: list[dict] = []
    client = FakeClient([AssistantMessage(tool_calls=(SAVE_CALL,)), AssistantMessage(content="Saved job 7.")])

    run = run_assistant("Save job 7", [], CONTEXT, client, registry=make_registry(saved), auto_approve=True)

    assert saved == [{"item_type": "job", "item_id": 7}]
    assert run.pending_action is None


def test_new_message_while_pending_counts_as_decline() -> None:
    saved: list[dict] = []
    registry = make_registry(saved)
    paused = run_assistant("Save job 7", [], CONTEXT, FakeClient([AssistantMessage(tool_calls=(SAVE_CALL,))]), registry=registry)
    client = FakeClient([AssistantMessage(content="Sure, here is something else.")])

    run_assistant("Never mind, hello", paused.conversation, CONTEXT, client, registry=registry)

    assert saved == []
    sent = client.calls[0]
    assert sent[-2]["role"] == "tool" and sent[-2]["content"].startswith(CANCELLED_PREFIX)
    assert sent[-1] == {"role": "user", "content": "Never mind, hello"}


def test_confirm_endpoint_resumes_and_rejects_when_nothing_is_pending() -> None:
    account = Account(id=1, email="student@example.com", password_hash="unused", role=AccountRole.STUDENT)
    client = FakeClient([AssistantMessage(content="Cancelled, nothing was saved.")])
    app.dependency_overrides[get_current_user] = lambda: account
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[get_model_client] = lambda: client
    pending_conversation = [
        {"role": "user", "content": "Save job 7"},
        {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "save_job_or_event", "arguments": {"item_type": "job", "item_id": 7}}}]},
    ]

    try:
        http = TestClient(app)
        declined = http.post("/assistant/confirm", json={"conversation": pending_conversation, "approved": False})
        nothing = http.post(
            "/assistant/confirm",
            json={"conversation": [{"role": "user", "content": "hi"}], "approved": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert declined.status_code == 200
    body = declined.json()
    assert body["answer"] == "Cancelled, nothing was saved."
    assert body["pending_action"] is None
    assert body["conversation"][2]["content"].startswith(CANCELLED_PREFIX)
    assert nothing.status_code == 409
