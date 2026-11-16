#!/usr/bin/env python3
"""One-time migration of the Lab 1 MySQL database into MongoDB.

    python backend/db/migrate_mysql_to_mongo.py            # copy everything (idempotent upserts)
    python backend/db/migrate_mysql_to_mongo.py --verify   # also compare row and document counts

Reads MySQL with DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME and writes
MONGO_URI / MONGO_DB. Integer ids are kept (`id` -> `_id`), so every API URL and
foreign key still points at the same record. Reshaping on the way:

- students / companies / preferences: `_id` = the account id (kept as account_id too)
- jobs, events: copy of the owning company's name for search
- applications: `company_id` for scoping; `resume_path` becomes resume metadata
- registrations: `company_id` for company-wide counts
- conversations -> message_threads, messages.conversation_id -> thread_id
  (the name `conversations` is reserved for the assistant's session memory)
- DATE -> "YYYY-MM-DD", TIME -> "HH:MM:SS", DECIMAL -> Decimal128

Passwords move as their existing bcrypt hashes; nobody has to reset.
"""

import argparse
import sys
from datetime import timedelta
from pathlib import Path

import pymysql
from pymongo import ReplaceOne

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings  # noqa: E402
from app.mongo import encode, ensure_indexes, get_database, set_counter_floor  # noqa: E402

BATCH = 1000


def _time(value):
    """pymysql returns TIME columns as timedelta."""

    if isinstance(value, timedelta):
        seconds = int(value.total_seconds())
        return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"
    return value


def rows(cursor, sql: str):
    cursor.execute(sql)
    while batch := cursor.fetchmany(BATCH):
        yield from batch


def upsert(db, collection: str, documents) -> int:
    ops, total = [], 0
    for document in documents:
        ops.append(ReplaceOne({"_id": document["_id"]}, encode(document), upsert=True))
        if len(ops) == BATCH:
            db[collection].bulk_write(ops, ordered=False)
            total += len(ops)
            ops = []
    if ops:
        db[collection].bulk_write(ops, ordered=False)
        total += len(ops)
    return total


def migrate(cursor, db) -> dict[str, tuple[str, int]]:
    report: dict[str, tuple[str, int]] = {}

    def run(table: str, collection: str, sql: str, transform) -> None:
        report[table] = (collection, upsert(db, collection, (transform(row) for row in rows(cursor, sql))))
        print(f"  {table:<18} -> {collection:<18} {report[table][1]:>6} documents")

    company_names = {}
    cursor.execute("SELECT account_id, company_name FROM companies")
    company_names = {row["account_id"]: row["company_name"] for row in cursor.fetchall()}
    cursor.execute("SELECT id, company_id FROM jobs")
    job_company = {row["id"]: row["company_id"] for row in cursor.fetchall()}
    cursor.execute("SELECT id, company_id FROM events")
    event_company = {row["id"]: row["company_id"] for row in cursor.fetchall()}

    def by_id(row):
        row["_id"] = row.pop("id")
        return row

    def by_account(row):
        row["_id"] = row["account_id"]
        return row

    run("accounts", "accounts", "SELECT * FROM accounts", by_id)
    run("students", "students", "SELECT * FROM students", by_account)
    run("companies", "companies", "SELECT * FROM companies", by_account)
    run("company_members", "company_members", "SELECT * FROM company_members", by_id)
    run("team_invitations", "team_invitations", "SELECT * FROM team_invitations", by_id)

    def preference(row):
        row["_id"] = row["student_id"]
        row["remote_ok"] = bool(row["remote_ok"])
        return row

    run("preferences", "preferences", "SELECT * FROM preferences", preference)

    def job(row):
        row = by_id(row)
        row["is_remote"] = bool(row["is_remote"])
        row["company_name"] = company_names.get(row["company_id"])
        return row

    run("jobs", "jobs", "SELECT * FROM jobs", job)

    def application(row):
        row = by_id(row)
        path = row.pop("resume_path")
        row["company_id"] = job_company.get(row["job_id"])
        row["resume"] = {
            "path": path,
            "original_filename": Path(path).name,
            "size_bytes": None,
            "sha256": None,
            "content_type": "application/pdf",
            "uploaded_at": row["applied_at"],
        }
        return row

    run("applications", "applications", "SELECT * FROM applications", application)

    def event(row):
        row = by_id(row)
        row["event_time"] = _time(row["event_time"])
        row["company_name"] = company_names.get(row["company_id"])
        return row

    run("events", "events", "SELECT * FROM events", event)

    def registration(row):
        row = by_id(row)
        row["company_id"] = event_company.get(row["event_id"])
        return row

    run("registrations", "registrations", "SELECT * FROM registrations", registration)
    run("saved_items", "saved_items", "SELECT * FROM saved_items", by_id)
    run("conversations", "message_threads", "SELECT * FROM conversations", by_id)

    def message(row):
        row = by_id(row)
        row["thread_id"] = row.pop("conversation_id")
        return row

    run("messages", "messages", "SELECT * FROM messages", message)

    for collection in ("accounts", "company_members", "team_invitations", "jobs", "applications", "events",
                       "registrations", "saved_items", "message_threads", "messages"):
        set_counter_floor(db, collection)
    return report


def verify(cursor, db, report) -> bool:
    ok = True
    print("\nVerification (MySQL rows vs MongoDB documents):")
    for table, (collection, _) in report.items():
        cursor.execute(f"SELECT COUNT(*) AS n FROM {table}")
        mysql_count = cursor.fetchone()["n"]
        mongo_count = db[collection].count_documents({})
        status = "OK" if mongo_count >= mysql_count else "MISSING"
        ok &= status == "OK"
        print(f"  {table:<18} {mysql_count:>6}   {collection:<18} {mongo_count:>6}   {status}")
    sample = db.accounts.find_one({"email": "student001@seed.p17.example"}, {"password_hash": 1})
    if sample:
        print(f"\n  bcrypt hash carried over for student001: {sample['password_hash'][:7]}... ({len(sample['password_hash'])} chars)")
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verify", action="store_true", help="compare counts after migrating")
    args = parser.parse_args()

    connection = pymysql.connect(
        host=settings.db_host, port=settings.db_port, user=settings.db_user, password=settings.db_password,
        database=settings.db_name, cursorclass=pymysql.cursors.DictCursor,
    )
    db = get_database()
    ensure_indexes(db)
    print(f"Migrating MySQL {settings.db_host}/{settings.db_name} -> MongoDB {settings.mongo_db}")
    with connection, connection.cursor() as cursor:
        report = migrate(cursor, db)
        if args.verify and not verify(cursor, db, report):
            sys.exit(1)


if __name__ == "__main__":
    main()
