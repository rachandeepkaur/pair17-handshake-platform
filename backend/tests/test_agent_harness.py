import json

from evaluation.agent_harness import run_harness


def test_harness_writes_all_required_cases(tmp_path) -> None:
    output_path = tmp_path / "agent_harness.jsonl"

    results = run_harness(output_path)
    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]

    assert len(results) == 11
    assert len(rows) == 11
    assert all(row["passed"] for row in rows)
    assert {"read_only_search", "approved_save", "declined_save", "malformed_arguments", "unknown_tool", "no_match", "conversation_follow_up", "injection_before_defense", "injection_after_defense", "iteration_ceiling", "recovery_retry"} == {
        row["case"] for row in rows
    }
    assert all({"input", "assistant_messages", "tool_calls", "tool_results", "final_answer", "guardrail_outcome", "errors", "retries", "iterations", "tool_call_count", "elapsed_ms"} <= row.keys() for row in rows)
