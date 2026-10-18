"""Shared setup for the Part C evaluation scripts (real Ollama, seeded database)."""

import contextlib
import io
import sys
import time
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.assistant.agent import AssistantRun  # noqa: E402
from app.assistant.tools.schemas import AssistantContext, Message  # noqa: E402
from app.models.account import Account  # noqa: E402

EVALUATION_DIR = REPO_DIR / "docs" / "evaluation"
DEFAULT_STUDENT = "student001@seed.p17.example"


@dataclass
class TimedRun:
    run: AssistantRun
    console: str
    seconds: float


def student_context(db: Session, email: str) -> AssistantContext:
    account_id = db.scalar(select(Account.id).where(Account.email == email))
    if account_id is None:
        raise SystemExit(f"No account {email}. Run the seed first.")
    return AssistantContext(account_id=account_id, role="student", db=db)


def timed(function, *args, **kwargs) -> TimedRun:
    """Run the assistant, capturing the console lines run_assistant prints."""

    buffer = io.StringIO()
    started = time.monotonic()
    with contextlib.redirect_stdout(buffer):
        run = function(*args, **kwargs)
    return TimedRun(run=run, console=buffer.getvalue(), seconds=time.monotonic() - started)


def turn_messages(conversation: list[Message]) -> list[Message]:
    """Messages after the latest user message."""

    last_user = max(i for i, message in enumerate(conversation) if message["role"] == "user")
    return conversation[last_user + 1 :]


def render_run(title: str, timed_run: TimedRun, *, result_chars: int = 700) -> str:
    """Plain-text transcript of one run: tool calls with results, then the answer."""

    run = timed_run.run
    lines = [f"=== {title} ({timed_run.seconds:.0f}s) ==="]
    results = [m for m in turn_messages(run.conversation) if m["role"] == "tool"]
    for index, record in enumerate(run.tool_calls):
        lines.append(f"TOOL CALL {index + 1}: {record.name} {record.arguments}  [{record.status}]")
        if record.error:
            lines.append(f"  error: {record.error}")
        if index < len(results):
            content = results[index]["content"]
            if len(content) > result_chars:
                content = content[:result_chars] + " …"
            lines.append("  result: " + content.replace("\n", "\n          "))
    if run.pending_action:
        lines.append(f"PENDING CONFIRMATION: {run.pending_action.summary}")
    lines.append(f"ANSWER: {run.answer}")
    lines.append("CONSOLE:\n  " + timed_run.console.strip().replace("\n", "\n  "))
    return "\n".join(lines)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {path.relative_to(REPO_DIR)}")
