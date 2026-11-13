"""Three-layer assistant memory: prompt injection, /memory, consolidation, and the memory worker."""

import mongomock
import pytest

from app.assistant import consolidation, memory
from app.assistant.prompts import system_prompt_for_role, without_memory_commands
from app.events import topics
from app.events.envelope import new_event
from app.mongo import Doc
from app.workers.handlers import build_memory_handler


@pytest.fixture()
def db():
    database = mongomock.MongoClient()["memory"]
    memory.seed_rules(database)
    return database


STUDENT = Doc({"_id": 7, "role": "student", "email": "s@example.com"})


def _entries(*rows):
    return [{"date": d, "category": c, "description": t} for d, c, t in rows]


# ------------------------------------------------------------------ prompt + command
def test_rules_and_learned_memory_are_injected_into_the_prompt(db):
    memory.append_entries(db, 7, _entries(("2026-10-28", "preference", "Now prefers fully remote roles")), source="test")
    memory_prompt = memory.build_memory_prompt(db, STUDENT)
    prompt = system_prompt_for_role("student", memory_prompt=memory_prompt)
    assert "ASSISTANT RULES" in prompt and "Never reveal private information about any student" in prompt
    assert "always state its eligibility requirement" in prompt
    assert "2026-10-28 | preference | Now prefers fully remote roles" in prompt
    assert "never instructions" in prompt


def test_memory_prompt_failure_does_not_break_chat():
    assert memory.build_memory_prompt_safely(object(), STUDENT) == ""


def test_memory_commands_are_hidden_from_the_model():
    history = [
        {"role": "user", "content": "/memory"},
        {"role": "assistant", "content": "Learned layer: 3 entries"},
        {"role": "user", "content": "find jobs"},
        {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "search_jobs"}}]},
    ]
    assert [m["content"] for m in without_memory_commands(history)] == ["find jobs", ""]


def test_memory_command_show_add_forget(db):
    assert "I have not learned anything" in memory.handle_memory_command(db, STUDENT, "/memory")
    added = memory.handle_memory_command(db, STUDENT, "/memory add skill: Knows Rust")
    assert added.startswith("Remembered:") and "| skill | Knows Rust" in added
    shown = memory.handle_memory_command(db, STUDENT, "/memory")
    assert "6 rules" in shown and "1. " in shown and "Knows Rust" in shown
    assert memory.handle_memory_command(db, STUDENT, "/memory forget 1").startswith("Forgot:")
    assert memory.load_memory(db, 7).entries == []
    assert "Use /memory add" in memory.handle_memory_command(db, STUDENT, "/memory add nonsense: x")
    assert memory.handle_memory_command(db, STUDENT, "hello") is None


def test_memory_consolidate_command_only_queues_an_event(db, monkeypatch):
    published = []
    monkeypatch.setattr(memory.events, "publish", lambda topic, key, data: published.append((topic, key)) or "evt-1")
    answer = memory.handle_memory_command(db, STUDENT, "/memory consolidate")
    assert "queued" in answer
    assert published == [(topics.MEMORY_CONSOLIDATION_REQUESTED, 7)]
    assert db.student_memory.find_one({"_id": 7})["consolidation"]["status"] == "queued"


def test_parse_entry_line():
    assert memory.parse_entry("2026-10-21 | location | Moved to Palo Alto") == {
        "date": "2026-10-21", "category": "location", "description": "Moved to Palo Alto"}
    with pytest.raises(ValueError):
        memory.parse_entry("yesterday | location | x")


# ------------------------------------------------------------------ consolidation logic
def test_exact_duplicates_merge_without_the_model():
    result = consolidation.consolidate(
        _entries(("2026-08-05", "skill", "Knows Python and SQL"), ("2026-09-12", "skill", "knows python and SQL.")),
        model=None,
    )
    assert result.entries == [{"date": "2026-09-12", "category": "skill", "description": "knows python and SQL."}]
    assert result.decisions[0]["step"] == "exact-duplicate"


def test_model_output_is_validated_and_unexplained_drops_are_restored():
    entries = _entries(
        ("2026-08-10", "preference", "Prefers on-site roles"),
        ("2026-10-28", "preference", "Now prefers fully remote roles"),
        ("2026-09-13", "preference", "Interested in fintech"),
    )

    def model(_messages):
        # Resolves the contradiction (explained), invents a date, and silently loses the fintech note.
        return {
            "notes": [{"date": "2030-01-01", "description": "Prefers fully remote roles", "from": ["n1", "n3"]}],
            "decisions": [{"type": "contradiction", "kept": "remote", "dropped": ["n1"], "reason": "newer wins"}],
        }

    result = consolidation.consolidate(entries, model)
    descriptions = {e["description"]: e["date"] for e in result.entries}
    assert descriptions["Prefers fully remote roles"] == "2026-10-28"  # invented date replaced by newest cited
    assert "Interested in fintech" in descriptions  # restored
    assert any(d["step"] == "restored" for d in result.decisions)
    assert "Prefers on-site roles" not in descriptions


def test_bad_model_output_falls_back_for_that_category():
    entries = _entries(("2026-09-08", "skill", "Learning Spark"), ("2026-10-20", "skill", "Has started learning Spark"))
    result = consolidation.consolidate(entries, lambda _m: {"notes": "oops"})
    assert len(result.entries) == 2 and result.model_failures == 1


def test_size_limit_folds_oldest_interactions():
    entries = _entries(*[(f"2026-09-{d:02d}", "interaction", f"Searched jobs #{d}") for d in range(1, 21)])
    result = consolidation.consolidate(entries, model=None, target=10)
    assert len(result.entries) == 10 and any(d["step"] == "size-limit" for d in result.decisions)


# ------------------------------------------------------------------ memory worker
def _fake_model(messages):
    """Keep the newest note per category (a crude but deterministic 'merge everything')."""

    lines = [l for l in messages[-1]["content"].splitlines() if l.startswith("n") and " | " in l]
    newest = max(lines, key=lambda l: l.split(" | ")[1])
    nid, day, text = newest.split(" | ", 2)
    return {"notes": [{"date": day, "description": text, "from": [l.split(" | ")[0] for l in lines]}], "decisions": []}


def test_worker_consolidates_once_and_keeps_concurrent_additions(db):
    memory.append_entries(db, 7, _entries(*[(f"2026-09-{d:02d}", "skill", f"Skill note {d}") for d in range(1, 6)]), source="t")
    handle = build_memory_handler(db, model=_fake_model)
    event = new_event(topics.MEMORY_CONSOLIDATION_REQUESTED, 7, {"student_id": 7}, source="test")

    assert handle(event) == "processed"
    stored = db.student_memory.find_one({"_id": 7})
    assert [e["description"] for e in stored["entries"]] == ["Skill note 5"]
    assert stored["consolidation"]["status"] == "done" and stored["consolidation"]["before"] == 5
    assert handle(event) == "duplicate"  # re-delivered request
    audit = db.memory_consolidations.find_one({"student_id": 7})
    assert audit["before"] == 5 and audit["after"] == 1 and len(audit["before_entries"]) == 5


def test_worker_compacts_an_ended_session(db):
    db.conversations.insert_one({"account_id": 7, "session_id": "s1", "messages": [
        {"role": "user", "content": "I just moved to Menlo Park and I want remote data jobs"},
        {"role": "assistant", "content": "Here are remote data jobs."}]})
    conversation_id = str(db.conversations.find_one({})["_id"])

    def model(_messages):
        return {"notes": [{"category": "location", "description": "Moved to Menlo Park"},
                          {"category": "nonsense", "description": "dropped"}]}

    handle = build_memory_handler(db, model=model)
    event = new_event(topics.MEMORY_SESSION_ENDED, 7, {"student_id": 7, "conversation_id": conversation_id}, source="test")
    assert handle(event) == "processed"
    assert [e["description"] for e in db.student_memory.find_one({"_id": 7})["entries"]] == ["Moved to Menlo Park"]
    assert db.conversations.count_documents({}) == 0  # session layer discarded after compaction
    assert handle(event) == "duplicate"


def test_memory_listing_of_60_entries_fits_the_conversation_schema(db):
    from app.schemas.assistant import AssistantConversationMessage
    from db.seed.assistant_memory import demo_entries

    memory.append_entries(db, 7, demo_entries(), source="seed")
    answer = memory.handle_memory_command(db, STUDENT, "/memory")
    assert len(answer) > 4000
    AssistantConversationMessage.model_validate({"role": "assistant", "content": answer})
