#!/usr/bin/env python3
"""Uses the real Ollama model and the seeded database, signed in as a seeded
student. Each transcript shows every tool call, its arguments and result,
the console lines printed by run_assistant, and automatic checks for that
test's requirement.

Run from the repository root (Ollama running, database seeded):
    python backend/evaluation/run_transcripts.py
    python backend/evaluation/run_transcripts.py --student student002@seed.p17.example
"""

import argparse
import contextlib
import io
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402

from app.assistant.agent import MAX_ASSISTANT_ITERATIONS, run_assistant  # noqa: E402
from app.assistant.llm_client import OllamaClient  # noqa: E402
from app.assistant.tools.schemas import AssistantContext, Message  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.account import Account  # noqa: E402
from app.models.student import Student  # noqa: E402

TRANSCRIPT_DIR = REPO_DIR / "docs" / "transcripts"


def next_month_range(today: date) -> tuple[date, date]:
    first = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
    last = (first + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    return first, last


def tool_calls_since_last_user(conversation: list[Message]) -> list[dict]:
    """Tool calls the assistant made while answering the latest user message."""
    last_user = max(i for i, message in enumerate(conversation) if message["role"] == "user")
    calls = []
    for message in conversation[last_user + 1 :]:
        for call in message.get("tool_calls", []):
            function = call.get("function", call)
            calls.append({"name": function["name"], "arguments": function.get("arguments", {})})
    return calls


def args_of(calls: list[dict], name: str) -> list[dict]:
    return [call["arguments"] for call in calls if call["name"] == name]


def text_has(value: object, *needles: str) -> bool:
    return isinstance(value, str) and any(needle.lower() in value.lower() for needle in needles)


# --- per-test checks: each returns [(passed, description), ...] ----------------

def check_city_internship(calls, answer, student):
    jobs = args_of(calls, "search_jobs")
    return [
        (bool(calls) and calls[0]["name"] == "get_student_preferences", "get_student_preferences is the first tool call"),
        (any(text_has(a.get("city"), student.city) for a in jobs), f"search_jobs filters by the student's city ({student.city})"),
        (any(a.get("category") == "internship" for a in jobs), "search_jobs filters category = internship"),
    ]


def check_remote_data_science(calls, answer, student):
    jobs = args_of(calls, "search_jobs")
    return [
        (any(a.get("category") == "internship" for a in jobs), "filters category = internship"),
        (any(a.get("remote") is True or a.get("city") for a in jobs), "filters by remote status or location"),
        (any(a.get("skills") for a in jobs), "filters by skills"),
        (any(text_has(a.get("title"), "data") or text_has(a.get("skills"), "python", "sql", "pandas", "data") for a in jobs),
         "targets data science (title or skills)"),
    ]


def check_cs_event(calls, answer, student, month=None):
    events = args_of(calls, "search_events")
    first, last = month
    return [
        (any(a.get("start_date") == first.isoformat() for a in events), f"start_date = {first.isoformat()} (first day of next month)"),
        (any(a.get("end_date") == last.isoformat() for a in events), f"end_date = {last.isoformat()} (last day of next month)"),
        (any(text_has(a.get("major"), "computer science") or text_has(a.get("eligibility"), "computer science") for a in events),
         "filters eligibility/major = Computer Science"),
    ]


def check_followup(calls, answer, student):
    jobs = args_of(calls, "search_jobs")
    return [
        (bool(jobs), "runs a new search_jobs instead of answering from memory"),
        (any(a.get("min_salary") for a in jobs), "adds a min_salary filter (higher paying)"),
        (any(text_has(a.get("city"), student.city) and a.get("category") == "internship" for a in jobs),
         "keeps the earlier city and internship filters from conversation history"),
    ]


def check_absent(calls, answer, student):
    jobs = args_of(calls, "search_jobs")
    return [
        (bool(jobs), "searches before answering"),
        (any(text_has(a.get("company"), "starbucks") or text_has(a.get("title"), "marine") for a in jobs),
         "searches for the absent company/category"),
        (text_has(answer, "no ", "not find", "couldn't", "could not", "none", "no match", "aren't", "are not", "don't"),
         "says no match exists"),
        ("starbucks" not in answer.lower() or "no" in answer.lower(), "does not present a Starbucks job as if it exists"),
    ]


TESTS: list[tuple[str, str, str, Callable]] = [
    ("01_internship_in_my_city", "Find an internship in my city.", "new", check_city_internship),
    ("02_remote_data_science", "Find a remote data science internship.", "new", check_remote_data_science),
    ("03_cs_event_next_month", "Find an event for computer science students next month.", "new", check_cs_event),
    ("04_followup_refinement", "Can you make it higher paying?", "continue:01", check_followup),
    ("05_absent_category", "Find me a marine biology internship at Starbucks.", "new", check_absent),
]


def render(name, prompt_history, conversation, answer, console, checks, student, email, model, tool_count, stopped):
    lines = [
        f"Transcript {name}",
        f"Date: {datetime.now().isoformat(timespec='seconds')}    Model: {model}    Iteration ceiling: {MAX_ASSISTANT_ITERATIONS}",
        f"Student: {student.name} <{email}> | city {student.city} | major {student.major} | skills {student.skills}",
        "=" * 100,
    ]
    for message in conversation:
        role = message["role"]
        if role == "user":
            lines += ["", f"USER: {message['content']}"]
        elif role == "assistant":
            for call in message.get("tool_calls", []):
                function = call.get("function", call)
                lines.append(f"  -> TOOL CALL  {function['name']}({json.dumps(function.get('arguments', {}))})")
            if message.get("content"):
                lines += ["", f"ASSISTANT: {message['content']}"]
        elif role == "tool":
            result = message["content"].replace("\n", "\n                ")
            lines.append(f"  <- TOOL RESULT [{message['tool_name']}]: {result}")
    lines += [
        "",
        "=" * 100,
        "Console output from run_assistant (this run):",
        *(f"  {line}" for line in console.strip().splitlines()),
        f"Tool calls this run: {tool_count}" + ("   (stopped at iteration ceiling)" if stopped else ""),
        "",
        "Requirement checks:",
        *(f"  [{'PASS' if ok else 'FAIL'}] {text}" for ok, text in checks),
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--student", default="student001@seed.p17.example", help="Seeded student email to act as.")
    args = parser.parse_args()

    client = OllamaClient()
    month = next_month_range(date.today())
    conversations: dict[str, list[Message]] = {}
    total_pass = total_checks = 0

    with SessionLocal() as db:
        account = db.scalar(select(Account).where(Account.email == args.student))
        if account is None or account.role != "student":
            print(f"No seeded student with email {args.student}. Run the seed first.")
            return 1
        student = db.get(Student, account.id)
        context = AssistantContext(account_id=account.id, role="student", db=db)
        TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

        for name, prompt, mode, check in TESTS:
            # "continue:01" = follow-up in the same conversation as test 01.
            history = conversations[mode.split(":")[1]] if mode.startswith("continue:") else []
            console = io.StringIO()
            with contextlib.redirect_stdout(console):
                run = run_assistant(prompt, history, context, client)
            conversations[name.split("_")[0]] = run.conversation

            calls = tool_calls_since_last_user(run.conversation)
            checks = check(calls, run.answer, student, month=month) if check is check_cs_event else check(calls, run.answer, student)
            total_pass += sum(ok for ok, _ in checks)
            total_checks += len(checks)

            text = render(name, prompt, run.conversation, run.answer, console.getvalue(), checks, student,
                          args.student, client.model, run.tool_call_count, run.stopped_at_iteration_limit)
            (TRANSCRIPT_DIR / f"{name}.txt").write_text(text)
            status = "all checks pass" if all(ok for ok, _ in checks) else "SOME CHECKS FAIL"
            print(f"{name}: {run.tool_call_count} tool call(s), {status}")
            for ok, desc in checks:
                print(f"    [{'PASS' if ok else 'FAIL'}] {desc}")

    print(f"\n{total_pass}/{total_checks} checks passed. Transcripts written to {TRANSCRIPT_DIR.relative_to(REPO_DIR)}/")
    return 0 if total_pass == total_checks else 2


if __name__ == "__main__":
    sys.exit(main())
