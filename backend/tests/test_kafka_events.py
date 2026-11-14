"""Kafka event envelope, worker retry/dead-letter logic, and idempotent handlers (no broker needed)."""

import copy
import json

import pytest
from pymongo.errors import AutoReconnect, DuplicateKeyError

from app.events import producer, topics
from app.events.envelope import decode, encode, new_event
from app.workers.handlers import build_application_handler, build_event_handler, build_job_handler
from app.workers.runtime import process_with_retries


class FakeCollection:
    """The slice of a pymongo collection the handlers use."""

    def __init__(self):
        self.docs: dict = {}

    def create_index(self, *_args, **_kwargs):
        return None

    def insert_one(self, doc):
        if doc["_id"] in self.docs:
            raise DuplicateKeyError("E11000 duplicate key")
        self.docs[doc["_id"]] = copy.deepcopy(doc)

    def find_one(self, query, _projection=None):
        return next((d for d in self.docs.values() if all(d.get(k) == v for k, v in query.items())), None)

    def count_documents(self, query):
        return sum(all(d.get(k) == v for k, v in query.items()) for d in self.docs.values())

    def update_one(self, query, update, upsert=False):
        doc = self.docs.get(query["_id"])
        if doc is None and upsert:
            doc = self.docs[query["_id"]] = {"_id": query["_id"]}
        doc.update(update["$set"])


class FakeDb(dict):
    def __missing__(self, name):
        self[name] = FakeCollection()
        return self[name]


def _application_event(event_type=topics.APPLICATION_CREATED, **extra):
    data = {"application_id": 7, "job_id": 3, "student_id": 11, "company_id": 2, **extra}
    return new_event(event_type, 7, data, source="test")


# ------------------------------------------------------------------ envelope
def test_envelope_round_trip():
    event = _application_event()
    assert decode(encode(event)) == event


@pytest.mark.parametrize("raw", [None, b"not json", b'{"event_id": "x"}', b"[]"])
def test_decode_rejects_malformed_messages(raw):
    with pytest.raises(ValueError):
        decode(raw)


def test_publish_is_a_no_op_without_kafka(monkeypatch):
    monkeypatch.setattr(producer.settings, "kafka_bootstrap_servers", "")
    assert producer.publish(topics.JOB_CREATED, 1, {"job_id": 1}) is None


# ------------------------------------------------------- retries and the DLQ
def test_success_on_first_attempt():
    outcome = process_with_retries(encode(_application_event()), lambda e: "processed", max_attempts=3, backoff_seconds=0)
    assert (outcome.status, outcome.attempts) == ("processed", 1)


def test_transient_handler_failure_recovers_within_the_bound():
    calls = []

    def flaky(_event):
        calls.append(1)
        if len(calls) < 3:
            raise RuntimeError("boom")
        return "processed"

    sleeps = []
    outcome = process_with_retries(
        encode(_application_event()), flaky, max_attempts=3, backoff_seconds=0.5, sleep=sleeps.append
    )
    assert (outcome.status, outcome.attempts) == ("processed", 3)
    assert sleeps == [0.5, 1.0]


def test_poison_message_is_dead_lettered_after_bounded_retries():
    sleeps = []
    outcome = process_with_retries(b"not json at all", lambda e: "processed", max_attempts=3, backoff_seconds=0.5, sleep=sleeps.append)
    assert outcome.status == "dead_letter"
    assert outcome.attempts == 3
    assert "not JSON" in outcome.error
    assert sleeps == [0.5, 1.0]  # no sleep after the last attempt


def test_mongo_outage_is_not_dead_lettered():
    def down(_event):
        raise AutoReconnect("mongo down")

    with pytest.raises(AutoReconnect):
        process_with_retries(encode(_application_event()), down, max_attempts=3, backoff_seconds=0)


# ------------------------------------------------------- idempotent handlers
def test_application_event_published_twice_is_stored_once():
    db = FakeDb()
    handle = build_application_handler(db)
    event = _application_event()
    assert handle(event) == "processed"
    assert handle(decode(encode(event))) == "duplicate"
    assert db["application_events"].count_documents({"application_id": 7}) == 1


def test_status_change_writes_one_notification():
    db = FakeDb()
    handle = build_application_handler(db)
    event = _application_event(topics.APPLICATION_STATUS_CHANGED, old_status="Pending", new_status="Reviewed")
    handle(event)
    handle(event)
    notes = list(db["notifications"].docs.values())
    assert len(notes) == 1 and "Pending to Reviewed" in notes[0]["message"]


def test_status_change_without_statuses_is_rejected():
    handle = build_application_handler(FakeDb())
    with pytest.raises(ValueError):
        handle(_application_event(topics.APPLICATION_STATUS_CHANGED))


def test_registration_count_is_not_double_counted():
    db = FakeDb()
    handle = build_event_handler(db)
    data = {"registration_id": 5, "event_id": 9, "student_id": 11, "company_id": 2}
    first = new_event(topics.EVENT_REGISTRATION_CREATED, 9, data, source="test")
    republished = new_event(topics.EVENT_REGISTRATION_CREATED, 9, data, source="test")  # new event_id, same registration
    assert handle(first) == "processed"
    assert handle(republished) == "duplicate"
    assert db["event_stats"].docs[9]["registrations"] == 1


def test_job_index_is_upserted_once():
    db = FakeDb()
    handle = build_job_handler(db)
    data = {
        "job_id": 4, "company_id": 2, "title": "Data Intern", "category": "internship", "city": "Palo Alto",
        "skills_required": "Python, SQL", "posting_date": "2026-11-01", "deadline": "2026-12-01",
    }
    event = new_event(topics.JOB_CREATED, 4, data, source="test")
    assert handle(event) == "processed"
    assert handle(event) == "duplicate"
    doc = db["job_search_index"].docs[4]
    assert doc["skills"] == ["python", "sql"] and "data intern" in doc["search_text"]


def test_envelope_json_is_plain_json():
    payload = json.loads(encode(_application_event()))
    assert payload["key"] == "7" and payload["event_type"] == topics.APPLICATION_CREATED
