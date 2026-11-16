"""Verify the consolidated demo memory against the planted duplicates and contradictions.

    python -m db.seed.check_memory          (from backend/, or in the p17-db-seed image)

Prints each check, the consolidation decisions the worker recorded, and exits 1 on failure.
"""

import sys

from app.mongo import get_database
from db.seed.assistant_memory import CONTRADICTIONS, DEMO_STUDENT_EMAIL, DUPLICATES, UNIQUE


def main() -> int:
    db = get_database()
    student_id = db.accounts.find_one({"email": DEMO_STUDENT_EMAIL})["_id"]
    memory = db.student_memory.find_one({"_id": student_id})
    audit = db.memory_consolidations.find_one({"student_id": student_id}, sort=[("finished_at", -1)])
    entries = memory["entries"]
    text = [f"{e['category']} {e['description']}".casefold() for e in entries]
    failures = 0

    def check(ok: bool, label: str) -> None:
        nonlocal failures
        failures += not ok
        print(f"  {'PASS' if ok else 'FAIL'} {label}")

    before = audit.get("before") if audit else None  # count (the entry lists are before_entries / after_entries)
    if isinstance(before, list):
        before = len(before)
    print(f"Entries: before={before} after={len(entries)}  (model calls={audit and audit.get('model_calls')}, "
          f"fallbacks={audit and audit.get('model_failures')})")
    check(before is not None and before >= 60, f"seeded memory had at least 60 entries ({before})")
    check(len(entries) < 40, f"consolidated memory is below 40 entries ({len(entries)})")

    print("Duplicates merged (key phrase appears in at most one entry):")
    for phrase in DUPLICATES:
        hits = [e["description"] for e, t in zip(entries, text) if phrase in t]
        check(len(hits) <= 1, f"'{phrase}': {len(hits)} entr{'y' if len(hits) == 1 else 'ies'} {hits}")

    print("Contradictions resolved (older fact gone, newer fact kept):")
    for older, newer, gone, kept in CONTRADICTIONS:
        cat = older["category"]
        same_cat = [t for e, t in zip(entries, text) if e["category"] == cat]
        stale = [t for t in same_cat if gone.casefold() in t]
        fresh = [t for t in same_cat if kept.casefold() in t]
        check(not stale and bool(fresh),
              f"{cat}: '{older['description']}' -> '{newer['description']}'"
              + (f"  [stale: {stale}]" if stale else "") + ("" if fresh else "  [newer fact missing]"))

    print("Unique facts kept (informational: the model may merge or lose these):")
    for fact in UNIQUE:
        key = " ".join(fact["description"].casefold().split()[:3])
        kept = any(key in t for t in text)
        print(f"  {'KEPT' if kept else 'WARN lost'} {fact['category']}: {fact['description']}")

    if audit:
        print("\nConsolidation decisions recorded by p17-memory-worker:")
        for d in audit["decisions"]:
            dropped = "; ".join(d.get("dropped") or [])
            print(f"  [{d.get('step')}/{d.get('type') or '-'}] {d.get('category')}: kept '{d.get('kept')}'"
                  + (f" | dropped: {dropped}" if dropped else "") + (f" | {d.get('reason')}" if d.get("reason") else ""))
    print(f"\n{'All memory checks passed.' if not failures else f'{failures} memory check(s) failed.'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
