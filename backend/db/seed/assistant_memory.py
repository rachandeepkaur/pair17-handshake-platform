"""Seed the assistant's instruction layer and the consolidation demo memory.

student001 gets 60 learned-memory entries with planted problems:
- 4 exact duplicate pairs (DUPLICATES)
- 5 contradictions, an older and a newer statement of the same fact (CONTRADICTIONS)
- 8 groups of paraphrases of one fact, and 15 small interaction notes to summarize
A correct consolidation must end below 40 entries, keep one line per duplicate,
and keep only the newer side of each contradiction (scripts/memory_demo.py checks).
"""

from typing import Any

from app.assistant.memory import seed_rules
from app.mongo import utcnow

DEMO_STUDENT_EMAIL = "student001@seed.p17.example"


def _e(day: str, category: str, description: str) -> dict[str, str]:
    return {"date": f"2026-{day}", "category": category, "description": description}


# key phrase (case-insensitive) that must appear in at most one entry afterwards
DUPLICATES = {
    "python and sql": [_e("08-05", "skill", "Knows Python and SQL"), _e("09-12", "skill", "Knows Python and SQL")],
    "kafka": [
        _e("08-22", "preference", "Interested in Kafka and streaming data pipelines"),
        _e("10-05", "preference", "Interested in Kafka and streaming data pipelines"),
    ],
    "graduate": [
        _e("08-02", "background", "Expected to graduate in May 2027"),
        _e("09-30", "background", "Expected to graduate in May 2027"),
    ],
    "mentorship": [
        _e("08-18", "preference", "Prefers companies with formal mentorship programs"),
        _e("10-12", "preference", "Prefers companies with formal mentorship programs"),
    ],
}

# (older entry, newer entry, phrase that must be gone, phrase that must remain)
CONTRADICTIONS = [
    (_e("08-03", "location", "Lives in San Jose and commutes to campus by train"),
     _e("10-21", "location", "Moved to Palo Alto; no longer commutes from San Jose"),
     "lives in san jose", "palo alto"),
    (_e("08-10", "preference", "Prefers on-site roles and dislikes remote work"),
     _e("10-28", "preference", "Now prefers fully remote roles"),
     "on-site", "remote"),
    (_e("08-15", "constraint", "Only available for internships starting in summer 2027"),
     _e("11-02", "constraint", "Can start a part-time internship immediately, in fall 2026"),
     "summer 2027", "immediately"),
    (_e("08-20", "goal", "Wants to become a frontend engineer"),
     _e("10-30", "goal", "Switched career focus from frontend to data engineering"),
     "become a frontend engineer", "data engineering"),
    (_e("09-01", "constraint", "Minimum acceptable internship salary is $30,000"),
     _e("10-15", "constraint", "Will not consider internships paying under $45,000"),
     "$30,000", "$45,000"),
]

PARAPHRASES = [
    [_e("09-03", "goal", "Wants a data engineering internship"),
     _e("09-20", "goal", "Looking for data engineering internships"),
     _e("10-18", "goal", "Main goal: land a data engineering internship")],
    [_e("08-25", "skill", "Comfortable with pandas for data analysis"), _e("09-15", "skill", "Uses pandas regularly")],
    [_e("09-08", "skill", "Learning Apache Spark"), _e("10-02", "skill", "Taking an online Spark course"),
     _e("10-20", "skill", "Has started learning Spark")],
    [_e("08-28", "preference", "Likes small startups"),
     _e("10-08", "preference", "Prefers startup environments over big companies")],
    [_e("09-05", "location", "Willing to work in Mountain View or Menlo Park"),
     _e("10-11", "location", "Open to jobs in Mountain View and Menlo Park")],
    [_e("08-01", "background", "Computer Science major"), _e("09-10", "background", "Studies Computer Science")],
    [_e("09-18", "skill", "Built a class project with Docker"), _e("10-14", "skill", "Has used Docker in coursework")],
    [_e("09-09", "constraint", "Can work up to 20 hours a week during the semester"),
     _e("10-24", "constraint", "Max 20 hours per week while in school")],
]

INTERACTIONS = [
    _e("08-06", "interaction", "Searched for data internships in Palo Alto"),
    _e("08-19", "interaction", "Ran a search for data engineering internships in Palo Alto"),
    _e("09-02", "interaction", "Searched internships in Palo Alto again"),
    _e("09-11", "interaction", "Saved job 28 (Business Analyst Intern at EY)"),
    _e("09-16", "interaction", "Searched for data internships in Mountain View"),
    _e("09-25", "interaction", "Asked which events are open to Computer Science majors"),
    _e("10-01", "interaction", "Searched for Python internships in Palo Alto"),
    _e("10-03", "interaction", "Asked about the fall career fair"),
    _e("10-09", "interaction", "Saved job 169 (Agentic AI Intern at Block)"),
    _e("10-16", "interaction", "Searched for internships paying over $45,000"),
    _e("10-22", "interaction", "Asked how to apply to job 253"),
    _e("10-27", "interaction", "Asked the assistant to compare two internships"),
    _e("11-01", "interaction", "Searched for data internships in Menlo Park"),
    _e("11-03", "interaction", "Searched for remote data engineering roles"),
    _e("11-05", "interaction", "Asked for events next month"),
]

UNIQUE = [
    _e("08-12", "skill", "Knows Git and GitHub pull-request workflows"),
    _e("10-26", "skill", "Basic knowledge of AWS S3 and EC2"),
    _e("08-14", "background", "Completed a data structures course"),
    _e("09-22", "background", "Works as a teaching assistant for intro programming"),
    _e("09-28", "goal", "Wants to earn an AWS certification by spring 2027"),
    _e("09-13", "preference", "Interested in fintech and climate-tech companies"),
    _e("08-30", "constraint", "Does not have a car; needs a transit-accessible office"),
    _e("09-27", "location", "Prefers offices near Caltrain stations"),
    _e("10-19", "preference", "Prefers teams that use Python over Java"),
]


def demo_entries() -> list[dict[str, Any]]:
    entries = [e for pair in DUPLICATES.values() for e in pair]
    entries += [e for older, newer, _, _ in CONTRADICTIONS for e in (older, newer)]
    entries += [e for group in PARAPHRASES for e in group]
    entries += INTERACTIONS + UNIQUE
    return sorted(entries, key=lambda e: e["date"])


def seed_assistant_rules(db) -> None:
    seed_rules(db)


def seed_demo_memory(db) -> int:
    account = db.accounts.find_one({"email": DEMO_STUDENT_EMAIL}, {"_id": 1})
    if account is None:
        return 0
    entries = [{**e, "source": "seed"} for e in demo_entries()]
    db.student_memory.replace_one(
        {"_id": account["_id"]},
        {"_id": account["_id"], "student_id": account["_id"], "entries": entries, "version": 1,
         "updated_at": utcnow(), "consolidation": {}},
        upsert=True,
    )
    db.memory_consolidations.delete_many({"student_id": account["_id"]})
    return len(entries)


if __name__ == "__main__":  # re-seed only the memory: python -m db.seed.assistant_memory (from backend/)
    from app.mongo import get_database

    database = get_database()
    seed_assistant_rules(database)
    print("seeded", seed_demo_memory(database), "memory entries for", DEMO_STUDENT_EMAIL)
