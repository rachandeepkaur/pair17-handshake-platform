from app.assistant.agent import run_assistant
from app.assistant.confirmation import confirm_action
from app.assistant.tools.schemas import AssistantContext, AssistantMessage, ToolCall, ToolDefinition, ToolRegistry


def test_save_actions_require_explicit_approval() -> None:
    assert confirm_action("save_job_or_event", {"item_type": "job", "item_id": 4}) is False
    assert confirm_action("save_job_or_event", {"item_type": "job", "item_id": 4}, auto_approve=True) is True


def test_agent_does_not_run_a_write_tool_before_confirmation() -> None:
    calls = []

    class Client:
        def complete(self, *_args):
            return AssistantMessage(tool_calls=(ToolCall(name="save_job_or_event", arguments={"item_type": "job", "item_id": 4}),))

    def save(_context, arguments):
        calls.append(arguments)
        return "Saved."

    registry = ToolRegistry(role="student", tools=(ToolDefinition(name="save_job_or_event", description="Save.", parameters={}, handler=save, requires_confirmation=True),))
    run = run_assistant("Save job 4", [], AssistantContext(account_id=1, role="student"), Client(), registry=registry)

    assert calls == []
    assert run.pending_confirmation == {"tool_name": "save_job_or_event", "arguments": {"item_type": "job", "item_id": 4}, "prompt": "Save this job?"}
