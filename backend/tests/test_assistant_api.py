from collections.abc import Sequence

from fastapi.testclient import TestClient

from app.assistant.llm_client import get_model_client
from app.assistant.tools.schemas import AssistantMessage, Message, ToolDefinition
from app.database import get_db
from app.dependencies import get_current_user
from app.main import app
from app.models.account import Account, AccountRole


class FakeClient:
    def __init__(self, response: AssistantMessage) -> None:
        self.response = response
        self.calls: list[list[Message]] = []

    def complete(self, messages: Sequence[Message], tools: Sequence[ToolDefinition]) -> AssistantMessage:
        self.calls.append(list(messages))
        return self.response


def _configure_dependencies(account: Account, client: FakeClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: account
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[get_model_client] = lambda: client


def test_chat_endpoint_runs_the_assistant_for_a_student() -> None:
    client = FakeClient(AssistantMessage(content="I can help with that."))
    account = Account(id=1, email="student@example.com", password_hash="unused", role=AccountRole.STUDENT)
    _configure_dependencies(account, client)

    try:
        response = TestClient(app).post(
            "/assistant/chat",
            json={"message": "Find an internship", "conversation": []},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "I can help with that."
    assert body["tool_call_count"] == 0
    assert body["conversation"][-1] == {"role": "assistant", "content": "I can help with that.", "tool_name": None, "tool_calls": []}
    assert client.calls[0][0]["role"] == "system"


def test_chat_endpoint_rejects_blank_messages() -> None:
    client = FakeClient(AssistantMessage(content="This should not be used."))
    account = Account(id=1, email="student@example.com", password_hash="unused", role=AccountRole.STUDENT)
    _configure_dependencies(account, client)

    try:
        response = TestClient(app).post("/assistant/chat", json={"message": "   "})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_company_chat_returns_controlled_placeholder_without_model_call() -> None:
    client = FakeClient(AssistantMessage(content="This should not be used."))
    account = Account(id=2, email="company@example.com", password_hash="unused", role=AccountRole.COMPANY)
    _configure_dependencies(account, client)

    try:
        response = TestClient(app).post("/assistant/chat", json={"message": "Show my jobs"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["answer"] == "Company assistant tools are not available yet."
    assert client.calls == []
