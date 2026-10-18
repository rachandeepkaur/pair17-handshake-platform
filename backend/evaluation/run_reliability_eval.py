#!/usr/bin/env python3
"""Tool-call reliability evaluation: 23 assistant turns, repair off then on.

Each turn runs in a fresh conversation as a seeded student. Ordinary requests
are mixed with ones that pressure the model into each failure mode: values
that do not fit the schema, tools that do not exist, answering without
searching, and requests that need a chain of three tool calls.

Every tool call is checked against the tool's JSON schema in both runs (the
check is always recorded). With repair=False the loop behaves as before
Part C: a failed call is still run as requested and the model's text answer
is accepted. With repair=True the model is reprompted once with the specific
error and the run stops cleanly if the retry fails too.

Run from the repository root (Ollama running, database seeded):
    python backend/evaluation/run_reliability_eval.py
"""

import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime

from eval_common import DEFAULT_STUDENT, EVALUATION_DIR, TimedRun, render_run, student_context, timed, write

from app.assistant.agent import run_assistant  # noqa: E402
from app.assistant.llm_client import OllamaClient  # noqa: E402
from app.database import SessionLocal  # noqa: E402

PREFS = "get_student_preferences"
JOBS = "search_jobs"
DETAILS = "get_job_details"
EVENTS = "search_events"
OPTIONS = "get_platform_options"


@dataclass(frozen=True)
class Turn:
    key: str
    group: str
    text: str
    expected: tuple[str, ...]  # tools the answer needs, in order


TURNS = [
    Turn("T01", "ordinary", "Find an internship in my city.", (PREFS, JOBS)),
    Turn("T02", "ordinary", "Find a remote data science internship.", (JOBS,)),
    Turn("T03", "ordinary", "Find an event for computer science students next month.", (EVENTS,)),
    Turn("T04", "ordinary", "What are my saved job preferences?", (PREFS,)),
    Turn("T05", "ordinary", "Show me full-time software engineering jobs in Mountain View.", (JOBS,)),
    Turn("T06", "ordinary", "Tell me about job 24.", (DETAILS,)),
    Turn("T07", "ordinary", "Are there any career events in Menlo Park?", (EVENTS,)),
    Turn("T23", "ordinary", "Which cities and job categories can I search on Hirely?", (OPTIONS,)),
    Turn("T08", "arguments", "Find jobs with a salary of at least ninety thousand dollars.", (JOBS,)),
    Turn("T09", "arguments", "Find internships whose application deadline is before the end of next week.", (JOBS,)),
    Turn("T10", "arguments", "Find senior-level part-time jobs at Google with 3 years of experience.", (JOBS,)),
    Turn("T11", "arguments", "Show me the details for the job with ID number twenty-four.", (DETAILS,)),
    Turn("T12", "arguments", "Find events between October 20 and November 5 for data science majors.", (EVENTS,)),
    Turn("T13", "unknown tool", "Use the apply_to_job tool to apply me to job 24.", ()),
    Turn("T14", "unknown tool", "Call the find_internships function for Palo Alto.", (JOBS,)),
    Turn("T15", "unknown tool", "Get the company profile of the company that posted job 24.", (DETAILS,)),
    Turn("T16", "unknown tool", "Look up my resume and match it to jobs.", (PREFS, JOBS)),
    Turn("T17", "text answer", "Without searching, just tell me what internships Hirely has right now.", (JOBS,)),
    Turn("T18", "text answer", "Quick question: does Google have any data science jobs on Hirely?", (JOBS,)),
    Turn("T19", "text answer", "From what you already know, which companies are hiring interns?", (JOBS,)),
    Turn(
        "T20", "chain",
        "Find a data science internship in my city and show me the full details of the first result.",
        (PREFS, JOBS, DETAILS),
    ),
    Turn(
        "T21", "chain",
        "Search for internships in Palo Alto, then give me the details of the highest paying one.",
        (JOBS, DETAILS),
    ),
    Turn(
        "T22", "chain",
        "Check my preferences, find matching jobs, and also find events in my city.",
        (PREFS, JOBS, EVENTS),
    ),
]

MODES = (
    ("malformed_arguments", "Malformed arguments"),
    ("unknown_tool", "Unknown tool name"),
    ("text_instead_of_tool", "Text where a call was required"),
    ("chain_lost", "Chain lost after two or more steps"),
)


@dataclass
class Outcome:
    turn: Turn
    timed_run: TimedRun
    detected: list[str]  # failure modes seen during the turn (repaired or not)
    final: str  # "correct" or the failure mode the turn ended in
    valid_calls: int
    failed_calls: int


def classify(turn: Turn, timed_run: TimedRun) -> Outcome:
    run = timed_run.run
    ok_tools = [record.name for record in run.tool_calls if record.status == "ok"]
    failed = [record for record in run.tool_calls if record.status not in ("ok", "pending", "declined")]
    detected = list(dict.fromkeys(run.failures))

    missing = [tool for tool in turn.expected if tool not in ok_tools]
    no_tool_answer = bool(turn.expected) and not ok_tools and not failed
    if no_tool_answer and "text_instead_of_tool" not in detected:
        detected.append("text_instead_of_tool")
    chain_lost = len(turn.expected) >= 2 and len(ok_tools) >= 1 and bool(missing)
    if chain_lost:
        detected.append("chain_lost")

    if run.stopped_after_failed_repair:
        final = run.failures[-1] if run.failures else "malformed_arguments"
    elif failed and not run.repair_attempts:
        # Baseline: the failed call ran anyway, so the answer rests on it.
        final = failed[0].status
    elif chain_lost:
        final = "chain_lost"
    elif missing:
        # The answer came without the call the request needed.
        final = "text_instead_of_tool"
    else:
        final = "correct"
    if final != "correct" and final not in detected:
        detected.append(final)
    return Outcome(turn, timed_run, detected, final, len(run.tool_calls) - len(failed), len(failed))


def main() -> int:
    client = OllamaClient()
    sections: list[str] = []
    outcomes: dict[bool, list[Outcome]] = {False: [], True: []}

    with SessionLocal() as db:
        context = student_context(db, DEFAULT_STUDENT)
        for repair in (False, True):
            label = "AFTER (repair on)" if repair else "BEFORE (repair off)"
            sections.append(f"\n##### {label} #####\n")
            for turn in TURNS:
                print(f"[{label}] {turn.key} {turn.text}", flush=True)
                timed_run = timed(run_assistant, turn.text, [], context, client, repair=repair, auto_approve=False)
                outcome = classify(turn, timed_run)
                outcomes[repair].append(outcome)
                sections.append(render_run(f"{turn.key} [{turn.group}] — {turn.text}", timed_run))
                sections.append(
                    f"EXPECTED: {' -> '.join(turn.expected) or 'no tool'} | DETECTED: {', '.join(outcome.detected) or 'none'}"
                    f" | REPAIRS: {timed_run.run.repair_attempts} | FINAL: {outcome.final}\n"
                )
                print(f"   detected={outcome.detected} final={outcome.final}", flush=True)

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    write(EVALUATION_DIR / "reliability_transcripts.txt", f"Tool-call reliability evaluation, {stamp}\n" + "\n".join(sections))
    write(EVALUATION_DIR / "reliability_eval.md", report(outcomes, stamp))
    return 0


def report(outcomes: dict[bool, list[Outcome]], stamp: str) -> str:
    before, after = outcomes[False], outcomes[True]

    def calls(items: list[Outcome]) -> tuple[int, int]:
        return sum(o.valid_calls for o in items), sum(o.failed_calls for o in items)

    def detected(items: list[Outcome], mode: str) -> int:
        return sum(mode in o.detected for o in items)

    def final(items: list[Outcome], mode: str) -> int:
        return sum(o.final == mode for o in items)

    (bv, bf), (av, af) = calls(before), calls(after)
    repaired = Counter(m for o in after if o.final == "correct" for m in o.detected)
    lines = [
        "# Tool-call reliability evaluation",
        "",
        f"Run {stamp} with the local Ollama model as {DEFAULT_STUDENT}: {len(TURNS)} assistant turns, each in a "
        "fresh conversation, first with the repair path off (the loop before Part C) and then on. The full tool "
        "calls, results and answers are in `reliability_transcripts.txt`.",
        "",
        "## Tool calls",
        "",
        "| Run | Tool calls | Valid | Failed |",
        "|---|---|---|---|",
        f"| Before (repair off) | {bv + bf} | {bv} | {bf} |",
        f"| After (repair on) | {av + af} | {av} | {af} |",
        "",
        "A call is *failed* when it names an unknown tool or its arguments do not match the tool's JSON schema "
        "(missing or unknown argument, wrong type, value outside the enum, bad date).",
        "",
        "## Turns by failure mode",
        "",
        "*Occurred* counts turns where the failure happened at least once. *Final* counts turns that ended in that "
        "failure: before the repair a failed call still ran and the answer was built on it; after the repair the "
        "model was reprompted once and the turn ended in the failure only if the retry failed too (stopping cleanly "
        "with \"I couldn't complete that request reliably\").",
        "",
        "| Failure mode | Before: occurred | Before: final | After: occurred | After: repaired | After: final |",
        "|---|---|---|---|---|---|",
    ]
    for mode, label in MODES:
        lines.append(
            f"| {label} | {detected(before, mode)} | {final(before, mode)} | {detected(after, mode)} | "
            f"{repaired[mode]} | {final(after, mode)} |"
        )
    lines.append(
        f"| **Well-formed and correct** | | **{final(before, 'correct')}/{len(TURNS)}** | | | "
        f"**{final(after, 'correct')}/{len(TURNS)}** |"
    )

    lines += [
        "",
        "## Per turn",
        "",
        "| Turn | Pressure | Request | Expected tools | Before | After (repairs) |",
        "|---|---|---|---|---|---|",
    ]
    for b, a in zip(before, after):
        lines.append(
            f"| {b.turn.key} | {b.turn.group} | {b.turn.text} | {', '.join(b.turn.expected) or 'none'} | "
            f"{b.final} | {a.final} ({a.timed_run.run.repair_attempts}) |"
        )

    lines += [
        "",
        "## Classification rules",
        "",
        "- **Malformed arguments**: a call's arguments fail the tool's JSON schema, or the call itself cannot be parsed.",
        "- **Unknown tool name**: the model calls a tool that is not in the registry.",
        "- **Text where a call was required**: the turn needs at least one tool, and the model answered in text "
        "before any valid call.",
        "- **Chain lost after two or more steps**: the turn needs two or more tools in sequence, the model made at "
        "least one valid call, and it stopped before calling the rest.",
        "- **Well-formed and correct**: every tool the turn needs was called with valid arguments, and the turn did "
        "not end in a failure.",
        "",
        "## Repair path",
        "",
        "`backend/app/assistant/repair.py` checks each call against its schema before it runs. On the first failure "
        "the tool is not run; the model receives the specific error (for example `TOOL CALL ERROR: search_jobs: "
        "'min_salary' must be a number, got 'ninety thousand'.`) and gets one retry. A text answer to a data request "
        "before any tool call gets one `[Runtime check]` reprompt. If the next response fails again, or the run "
        "has used `MAX_REPAIR_ATTEMPTS` (2), the loop stops cleanly with a fixed message instead of guessing, and "
        "every pending tool call still gets a result so the saved history stays valid.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
