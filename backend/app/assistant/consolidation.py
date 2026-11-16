"""Learned-memory consolidation and session compaction (run by p17-memory-worker).

consolidate() shrinks a student's memory in three steps:

1. Deterministic pre-pass: exact duplicates (same category, same normalized text)
   are merged, keeping the newest date. This never needs the model.
2. Model pass, one call per category (small prompts suit an 8B CPU model): the
   model merges paraphrases, resolves contradictions (newer date wins), and
   summarizes runs of small interaction notes. It must cite the source note ids
   for every note it returns, and list what it dropped and why.
3. Validation: dates must come from the cited sources, categories are fixed by
   the call, and any input note the model neither kept nor explicitly dropped is
   restored (and reported), so a model mistake can lose a merge but never a fact.
   If the result is still >= 40 entries, the oldest interaction notes are folded
   into one summary line.

Every decision is returned for the audit log (memory_consolidations).
"""

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import httpx

from app.config import settings

CATEGORIES = ("preference", "goal", "skill", "location", "constraint", "background", "interaction")
JsonModel = Callable[[list[dict[str, str]]], dict[str, Any]]


@dataclass
class Result:
    entries: list[dict[str, Any]]
    decisions: list[dict[str, Any]] = field(default_factory=list)
    model_calls: int = 0
    model_failures: int = 0


def normalize(text: str) -> str:
    return " ".join(re.sub(r"[^\w$%+#.]+", " ", text.casefold()).split()).rstrip(".")


# ------------------------------------------------------------------ the model
def ollama_json(messages: list[dict[str, str]]) -> dict[str, Any]:
    """One non-streaming Ollama chat call constrained to JSON output."""

    response = httpx.post(
        f"{settings.ollama_host.rstrip('/')}/api/chat",
        json={
            "model": settings.ollama_model,
            "messages": messages,
            "stream": False,
            "format": "json",
            "think": False,
            "options": {"num_ctx": settings.ollama_num_ctx, "temperature": 0},
        },
        timeout=settings.ollama_timeout_seconds,
    )
    response.raise_for_status()
    return json.loads(response.json()["message"]["content"])


CONSOLIDATE_SYSTEM = (
    "You consolidate memory notes that a career assistant keeps about ONE student. "
    "Reply with JSON only, no prose."
)

CONSOLIDATE_INSTRUCTIONS = """Category: {category}
Notes, one per line as "id | date | description":
{notes}

Rewrite these notes as a shorter list:
1. Duplicates or paraphrases (same fact, different words): keep ONE note, dated with the newest date among them.
2. Contradictions (two notes that cannot both be true now): keep only the NEWER fact; drop the older note.
   Example: older "prefers on-site roles" vs newer "now prefers remote roles" -> keep only "prefers remote roles".
3. Several small related notes (for example repeated searches or saves): combine into one summary note,
   dated with the newest of them, keeping the concrete details (cities, job ids, counts).
4. Keep every other note. Never invent facts, numbers, or dates. Descriptions under 120 characters.

Return exactly:
{{"notes": [{{"date": "YYYY-MM-DD", "description": "...", "from": ["n1", "n4"]}}],
 "decisions": [{{"type": "duplicate" | "contradiction" | "summary", "kept": "...", "dropped": ["n2"], "reason": "..."}}]}}
"from" must list the ids of every input note that a returned note is based on."""


# ------------------------------------------------------------------ consolidation
def _dedupe_exact(entries: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in entries:
        key = (entry["category"], normalize(entry["description"]))
        kept = best.get(key)
        if kept is None:
            best[key] = dict(entry)
            continue
        newer, older = (entry, kept) if entry["date"] >= kept["date"] else (kept, entry)
        best[key] = dict(newer)
        decisions.append(
            {
                "step": "exact-duplicate",
                "category": entry["category"],
                "kept": f"{newer['date']} | {newer['description']}",
                "dropped": [f"{older['date']} | {older['description']}"],
                "reason": "identical text; kept the newest date",
            }
        )
    return list(best.values())


def _model_pass(
    category: str, entries: list[dict[str, Any]], model: JsonModel, result: Result
) -> list[dict[str, Any]]:
    ids = {f"n{i}": entry for i, entry in enumerate(entries, 1)}
    prompt = CONSOLIDATE_INSTRUCTIONS.format(
        category=category, notes="\n".join(f"{nid} | {e['date']} | {e['description']}" for nid, e in ids.items())
    )
    result.model_calls += 1
    try:
        reply = model([{"role": "system", "content": CONSOLIDATE_SYSTEM}, {"role": "user", "content": prompt}])
        notes = reply.get("notes")
        if not isinstance(notes, list) or not notes or len(notes) > len(entries):
            raise ValueError(f"model returned {len(notes) if isinstance(notes, list) else 'no'} notes for {len(entries)}")
    except Exception as exc:  # noqa: BLE001 - fall back to the pre-pass for this category
        result.model_failures += 1
        result.decisions.append({"step": "model-fallback", "category": category, "reason": f"{type(exc).__name__}: {exc}"[:300]})
        return entries

    covered: set[str] = set()
    out: list[dict[str, Any]] = []
    for note in notes:
        description = str(note.get("description", "")).strip()[:200]
        sources = [s for s in note.get("from", []) if isinstance(s, str) and s in ids]
        if not description:
            continue
        covered.update(sources)
        source_dates = [ids[s]["date"] for s in sources] or [max(e["date"] for e in entries)]
        claimed = str(note.get("date", ""))
        # The date must be one of the cited notes' dates; otherwise use the newest cited date.
        day = claimed if claimed in source_dates else max(source_dates)
        out.append({"date": day, "category": category, "description": description, "merged_from": len(sources) or 1})

    dropped: set[str] = set()
    for decision in reply.get("decisions", []) or []:
        if not isinstance(decision, dict):
            continue
        dropped_ids = [d for d in decision.get("dropped", []) if isinstance(d, str) and d in ids]
        dropped.update(dropped_ids)
        result.decisions.append(
            {
                "step": "model",
                "category": category,
                "type": decision.get("type"),
                "kept": decision.get("kept"),
                "dropped": [f"{ids[d]['date']} | {ids[d]['description']}" for d in dropped_ids],
                "reason": decision.get("reason"),
            }
        )

    # A note the model neither used nor explicitly dropped is restored: losing a fact is worse than a missed merge.
    for nid in sorted(set(ids) - covered - dropped, key=lambda n: int(n[1:])):
        out.append({**ids[nid], "merged_from": 1})
        result.decisions.append(
            {
                "step": "restored",
                "category": category,
                "kept": f"{ids[nid]['date']} | {ids[nid]['description']}",
                "reason": "the model dropped this note without citing or explaining it",
            }
        )
    return out


def _fold_interactions(entries: list[dict[str, Any]], target: int, result: Result) -> list[dict[str, Any]]:
    excess = len(entries) - target
    interactions = sorted((e for e in entries if e["category"] == "interaction"), key=lambda e: e["date"])
    if excess <= 0 or len(interactions) < 2:
        return entries
    fold = interactions[: min(len(interactions), excess + 1)]
    summary = {
        "date": fold[-1]["date"],
        "category": "interaction",
        "description": f"{len(fold)} earlier interactions between {fold[0]['date']} and {fold[-1]['date']} "
        f"(e.g. {fold[0]['description'][:60]})",
        "merged_from": len(fold),
    }
    folded = {id(e) for e in fold}
    result.decisions.append(
        {
            "step": "size-limit",
            "category": "interaction",
            "kept": summary["description"],
            "dropped": [f"{e['date']} | {e['description']}" for e in fold],
            "reason": f"still above {target} entries after merging; oldest interaction notes folded into one",
        }
    )
    return [e for e in entries if id(e) not in folded] + [summary]


def consolidate(entries: list[dict[str, Any]], model: JsonModel | None, *, target: int = 39) -> Result:
    result = Result(entries=[])
    clean = [
        {"date": str(e["date"]), "category": e["category"], "description": str(e["description"]).strip()}
        for e in entries
        if e.get("category") in CATEGORIES and str(e.get("description", "")).strip()
    ]
    stage = _dedupe_exact(clean, result.decisions)

    merged: list[dict[str, Any]] = []
    for category in CATEGORIES:
        group = sorted((e for e in stage if e["category"] == category), key=lambda e: e["date"])
        if len(group) >= 2 and model is not None:
            group = _model_pass(category, group, model, result)
        merged.extend(group)

    merged = _fold_interactions(merged, target, result)
    result.entries = sorted(merged, key=lambda e: (e["date"], CATEGORIES.index(e["category"])))
    return result


# ------------------------------------------------------------------ session compaction
EXTRACT_PROMPT = """Below is one conversation between a student and a career assistant.
Write the durable facts the STUDENT stated about themselves that would help next time:
preferences, goals, skills, location, constraints, background. Add at most one "interaction"
note summarizing what they did in this session (searches, saved items).
Do not include: anything about other people, passwords, phone numbers, dates of birth, GPA,
or facts that only the assistant or a tool said. If there is nothing durable, return no notes.

Categories: preference, goal, skill, location, constraint, background, interaction.
Return exactly: {{"notes": [{{"category": "...", "description": "under 120 characters"}}]}}

Conversation:
{transcript}"""


def extract_facts(messages: list[dict[str, Any]], model: JsonModel, today: date | None = None) -> list[dict[str, str]]:
    lines = []
    for message in messages:
        role, content = message.get("role"), str(message.get("content") or "").strip()
        if role in ("user", "assistant") and content and not content.startswith("/memory"):
            lines.append(f"{role.upper()}: {content[:800]}")
    if not lines:
        return []
    reply = model([{"role": "system", "content": CONSOLIDATE_SYSTEM},
                   {"role": "user", "content": EXTRACT_PROMPT.format(transcript="\n".join(lines[-30:]))}])
    day = (today or date.today()).isoformat()
    facts = []
    for note in reply.get("notes", []) or []:
        if isinstance(note, dict) and note.get("category") in CATEGORIES and str(note.get("description", "")).strip():
            facts.append({"date": day, "category": note["category"], "description": str(note["description"]).strip()[:200]})
    return facts[:12]
