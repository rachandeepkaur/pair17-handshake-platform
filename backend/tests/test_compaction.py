from app.assistant.compaction import compact_conversation, compacted_history
from app.assistant.agent import run_assistant
from app.assistant.tools.schemas import AssistantContext, AssistantMessage, ToolRegistry


class FakeClient:
    def complete(self, _messages, _tools):
        return AssistantMessage(
            content="Student preferences: Python.\nJobs: Data Intern.\nCompanies: Acme.\nEvents: None recorded.\nApplications: None recorded.\nCurrent request: Find internships.",
            prompt_tokens=6000,
            completion_tokens=40,
        )


def test_compaction_records_counts_and_keeps_latest_turn() -> None:
    conversation = [
        {"role": "user", "content": "Find internships"},
        {"role": "assistant", "content": "Data Intern is available."},
    ]

    result = compact_conversation(conversation, FakeClient())
    history = compacted_history(result.summary, conversation, include_latest_turn=True)

    assert result.before_prompt_tokens == 6000
    assert result.after_estimated_tokens > 0
    assert history[0]["content"].startswith("[Context summary]")
    assert history[1:] == conversation


def test_compacted_summary_is_available_to_the_next_turn() -> None:
    history = compacted_history(
        "Student preferences: Python.\nJobs: None recorded.\nCompanies: None recorded.\nEvents: None recorded.\nApplications: None recorded.\nCurrent request: Find internships.",
        [],
        include_latest_turn=False,
    )

    class RecallClient:
        def complete(self, messages, _tools):
            assert "Student preferences: Python." in messages[1]["content"]
            return AssistantMessage(content="Your recorded preference is Python.")

    run = run_assistant(
        "What language do I prefer?",
        history,
        AssistantContext(account_id=1, role="student"),
        RecallClient(),
        registry=ToolRegistry(role="student"),
    )

    assert run.answer == "Your recorded preference is Python."
