#!/usr/bin/env python3
"""Confirmation-gate demo with the real model: decline once, approve once.

1. "Save job N" pauses on save_job_or_event; the student declines. The model
   receives a CANCELLED tool result and must acknowledge it without retrying.
2. The same request, approved: the job is saved once (then un-saved, so the
   demo leaves the database as it found it).

Run from the repository root (Ollama running, database seeded):
    python backend/evaluation/run_confirmation_demo.py
"""

import re
import sys
from datetime import datetime

from eval_common import DEFAULT_STUDENT, EVALUATION_DIR, render_run, student_context, timed, write

from sqlalchemy import delete, select  # noqa: E402

from app.assistant.agent import resume_assistant, run_assistant  # noqa: E402
from app.assistant.llm_client import OllamaClient  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.saved_item import SavedItem  # noqa: E402

ACKNOWLEDGES = re.compile(r"cancel|not (been )?saved|won't|will not|didn't|did not|declin|okay|no problem", re.IGNORECASE)


def saved_job_ids(db, student_id: int) -> set[int]:
    return set(
        db.scalars(select(SavedItem.item_id).where(SavedItem.student_id == student_id, SavedItem.item_type == "job"))
    )


def main() -> int:
    client = OllamaClient()
    checks: list[tuple[bool, str]] = []
    sections: list[str] = []

    with SessionLocal() as db:
        context = student_context(db, DEFAULT_STUDENT)
        already = saved_job_ids(db, context.account_id)
        job_id = next(candidate for candidate in (24, 57, 90, 123, 156) if candidate not in already)
        request = f"Save job {job_id} to my saved jobs."

        for approved in (False, True):
            label = "approve" if approved else "decline"
            print(f"[{label}] {request}", flush=True)
            first = timed(run_assistant, request, [], context, client)
            sections.append(render_run(f"{label.upper()} step 1 — student: {request}", first))
            pending = first.run.pending_action
            checks.append((pending is not None and pending.tool_name == "save_job_or_event", f"[{label}] save pauses for confirmation"))
            checks.append((job_id not in saved_job_ids(db, context.account_id), f"[{label}] nothing saved before the decision"))
            if pending is None:
                continue

            sections.append(f"STUDENT CLICKS: {'Approve' if approved else 'Decline'} — \"{pending.summary}\"\n")
            second = timed(resume_assistant, first.run.conversation, approved, context, client)
            sections.append(render_run(f"{label.upper()} step 2 — resumed after the student's decision", second))
            statuses = [record.status for record in second.run.tool_calls]
            saved_now = job_id in saved_job_ids(db, context.account_id)

            if approved:
                checks.append((saved_now, f"[approve] job {job_id} is saved"))
                checks.append((statuses.count("ok") == 1 and second.run.pending_action is None, "[approve] the save ran exactly once"))
                db.execute(delete(SavedItem).where(SavedItem.student_id == context.account_id, SavedItem.item_id == job_id, SavedItem.item_type == "job"))
                db.commit()
            else:
                checks.append((not saved_now, f"[decline] job {job_id} is not saved"))
                checks.append((second.run.conversation[len(first.run.conversation)]["content"].startswith("CANCELLED:"), "[decline] model received a cancellation string"))
                checks.append(("ok" not in statuses and second.run.pending_action is None, "[decline] no retry: the save never ran and was not asked again"))
                checks.append((bool(ACKNOWLEDGES.search(second.run.answer)), "[decline] answer acknowledges the refusal"))
            sections.append("")

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary = "\n".join(f"[{'PASS' if ok else 'FAIL'}] {text}" for ok, text in checks)
    write(
        EVALUATION_DIR / "confirmation_demo.txt",
        f"Confirmation gate demo, {stamp}, as {DEFAULT_STUDENT}\n\n" + "\n\n".join(sections) + "\n\nCHECKS\n" + summary + "\n",
    )
    print(summary)
    return 0 if all(ok for ok, _ in checks) else 2


if __name__ == "__main__":
    sys.exit(main())
