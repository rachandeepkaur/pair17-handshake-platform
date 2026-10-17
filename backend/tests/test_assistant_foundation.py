import json

import httpx

from app.assistant.llm_client import OllamaClient
from app.assistant.registry import tool_registry_for_role
from app.assistant.tools.schemas import AssistantContext, ToolDefinition


def test_tool_definition_uses_ollama_function_schema() -> None:
    tool = ToolDefinition(
        name="example_tool",
        description="An example tool.",
        parameters={"type": "object", "properties": {}},
        handler=lambda _context, _arguments: "done",
    )

    assert tool.as_ollama_tool() == {
        "type": "function",
        "function": {
            "name": "example_tool",
            "description": "An example tool.",
            "parameters": {"type": "object", "properties": {}},
        },
    }


def test_company_registry_is_a_controlled_placeholder() -> None:
    registry = tool_registry_for_role("company")

    assert registry.schemas == []
    assert registry.unavailable_message == "Company assistant tools are not available yet."
    assert registry.run("missing", AssistantContext(account_id=1, role="company"), {}) == "Unknown tool: missing."


def test_ollama_client_sends_schemas_and_parses_tool_calls() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("http://ollama.test/api/chat")
        payload = json.loads(request.content)
        assert payload["model"] == "test-model"
        assert payload["stream"] is False
        assert payload["think"] is False
        assert payload["tools"][0]["function"]["name"] == "example_tool"
        return httpx.Response(
            200,
            json={
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "type": "function",
                            "function": {
                                "index": 0,
                                "name": "example_tool",
                                "arguments": {"query": "internship"},
                            },
                        }
                    ],
                }
            },
        )

    tool = ToolDefinition(
        name="example_tool",
        description="An example tool.",
        parameters={"type": "object", "properties": {}},
        handler=lambda _context, _arguments: "done",
    )
    client = OllamaClient(
        host="http://ollama.test",
        model="test-model",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = client.complete([{"role": "user", "content": "Find internships"}], [tool])

    assert response.content == ""
    assert response.tool_calls[0].name == "example_tool"
    assert response.tool_calls[0].arguments == {"query": "internship"}
