"""End-to-end API flows on MongoDB (mongomock), covering the Lab 1 features after the migration."""

from datetime import date, timedelta

import mongomock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.mongo import ensure_indexes, get_db, utcnow

PDF = b"%PDF-1.4\n% test resume\n"


@pytest.fixture()
def db():
    database = mongomock.MongoClient(tz_aware=False)["p17_test"]
    ensure_indexes(database)
    app.dependency_overrides[get_db] = lambda: database
    yield database
    app.dependency_overrides.clear()


@pytest.fixture()
def http(db):
    return TestClient(app)


def _login(http, email, password="Passw0rd!"):
    response = http.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture()
def company(http):
    response = http.post(
        "/auth/signup/company",
        json={"email": "hr@acme.example", "password": "Passw0rd!", "company_name": "Acme", "location": "Palo Alto, CA"},
    )
    assert response.status_code == 201, response.text
    return _login(http, "hr@acme.example")


@pytest.fixture()
def student(http):
    response = http.post(
        "/auth/signup/student",
        json={"email": "ada@uni.example", "password": "Passw0rd!", "name": "Ada Lovelace", "college_name": "SJSU"},
    )
    assert response.status_code == 201, response.text
    return _login(http, "ada@uni.example")


def _job_payload(**extra):
    return {
        "title": "Data Intern",
        "category": "internship",
        "city": "Palo Alto",
        "salary": 45000,
        "skills_required": "Python, SQL",
        "deadline": (date.today() + timedelta(days=30)).isoformat(),
        **extra,
    }


# ------------------------------------------------------------------ auth + sessions
def test_passwords_are_bcrypt_and_sessions_are_stored(http, db, student):
    account = db.accounts.find_one({"email": "ada@uni.example"})
    assert account["password_hash"].startswith("$2b$") and "Passw0rd!" not in account["password_hash"]
    session = db.sessions.find_one({"account_id": account["_id"]})
    assert session["expires_at"] > utcnow() and session["revoked_at"] is None
    assert len(session["_id"]) == 64  # only the SHA-256 of the session id is stored
    assert http.get("/students/me", headers=student).status_code == 200


def test_logout_revokes_the_token(http, student):
    assert http.post("/auth/logout", headers=student).status_code == 204
    response = http.get("/students/me", headers=student)
    assert response.status_code == 401 and "signed out" in response.json()["detail"]


def test_expired_session_is_rejected_even_with_a_valid_jwt(http, db, student):
    db.sessions.update_many({}, {"$set": {"expires_at": utcnow() - timedelta(seconds=1)}})
    assert http.get("/students/me", headers=student).status_code == 401


def test_duplicate_email_and_wrong_password(http, student):
    response = http.post(
        "/auth/signup/student",
        json={"email": "ada@uni.example", "password": "Passw0rd!", "name": "A", "college_name": "X"},
    )
    assert response.status_code == 409
    assert http.post("/auth/login", json={"email": "ada@uni.example", "password": "nope"}).status_code == 401


def test_change_password_revokes_other_sessions(http, student):
    other = _login(http, "ada@uni.example")
    response = http.post(
        "/auth/change-password", headers=student,
        json={"current_password": "Passw0rd!", "new_password": "N3wPassw0rd!"},
    )
    assert response.status_code == 204
    assert http.get("/students/me", headers=other).status_code == 401
    assert http.get("/students/me", headers=student).status_code == 200


# ------------------------------------------------------------------ student profile + preferences
def test_profile_and_preferences_round_trip(http, student):
    profile = http.get("/students/me", headers=student).json()
    profile.update({"city": "Palo Alto", "major": "Data Science", "skills": "Python, SQL", "cgpa": "3.85",
                    "date_of_birth": "2001-04-02"})
    response = http.put("/students/me", headers=student, json=profile)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["major"] == "Data Science" and body["date_of_birth"] == "2001-04-02" and float(body["cgpa"]) == 3.85

    prefs = {"preferred_categories": "internship", "preferred_cities": "Palo Alto", "min_salary": "40000.00",
             "preferred_skills": "Python", "remote_ok": True}
    assert http.put("/student/preferences", headers=student, json=prefs).status_code == 200
    assert http.get("/student/preferences", headers=student).json()["min_salary"] == "40000.00"


# ------------------------------------------------------------------ jobs + applications
def test_job_apply_and_status_flow(http, db, company, student):
    job = http.post("/jobs", headers=company, json=_job_payload()).json()
    assert job["id"] == 1 and job["applicant_count"] == 0

    listing = http.get("/student/jobs", headers=student, params={"q": "acme", "category": "internship"}).json()
    assert listing["total"] == 1 and listing["items"][0]["company_name"] == "Acme"
    assert http.get("/student/jobs", headers=student, params={"q": "zzz"}).json()["total"] == 0

    applied = http.post(f"/student/jobs/{job['id']}/apply", headers=student,
                        files={"resume": ("cv.pdf", PDF, "application/pdf")})
    assert applied.status_code == 201, applied.text
    resume = db.applications.find_one({})["resume"]
    assert resume["original_filename"] == "cv.pdf" and resume["size_bytes"] == len(PDF) and len(resume["sha256"]) == 64

    again = http.post(f"/student/jobs/{job['id']}/apply", headers=student,
                      files={"resume": ("cv.pdf", PDF, "application/pdf")})
    assert again.status_code == 409

    app_id = applied.json()["id"]
    changed = http.patch(f"/applications/{app_id}/status", headers=company, json={"status": "Reviewed"})
    assert changed.status_code == 200 and changed.json()["status"] == "Reviewed"
    assert http.get("/student/applications", headers=student).json()[0]["status"] == "Reviewed"
    assert http.get(f"/jobs/{job['id']}", headers=company).json()["applicant_count"] == 1

    detail = http.get(f"/applications/{app_id}", headers=company).json()
    assert detail["student"]["email"] == "ada@uni.example"

    dashboard = http.get("/dashboards/company", headers=company).json()
    assert dashboard["total_jobs"] == 1 and dashboard["applications_by_status"]["Reviewed"] == 1

    actions = {row["action"] for row in db.activity_logs.find()}
    assert {"auth.login", "job.created", "application.created", "application.status_changed"} <= actions


def test_salary_and_skill_filters(http, company, student):
    http.post("/jobs", headers=company, json=_job_payload(title="Low", salary=20000, skills_required="Excel"))
    http.post("/jobs", headers=company, json=_job_payload(title="High", salary=90000, skills_required="Python, Spark"))
    search = http.get("/student/jobs", headers=student, params={"limit": 10}).json()
    assert [item["title"] for item in search["items"]] == ["High", "Low"]
    from app.mongo import get_database  # noqa: F401  (ensures module import path is fine)


# ------------------------------------------------------------------ events
def test_event_registration_and_eligibility(http, db, company, student):
    soon = (date.today() + timedelta(days=5)).isoformat()
    open_event = http.post("/events", headers=company, json={"name": "Career Fair", "event_date": soon,
                                                             "event_time": "10:00:00", "eligibility": "Everyone"}).json()
    cs_only = http.post("/events", headers=company, json={"name": "CS Night", "event_date": soon,
                                                          "eligibility": "Computer Science"}).json()

    events = http.get("/student/events", headers=student).json()
    assert {e["name"]: e["eligible"] for e in events} == {"Career Fair": True, "CS Night": False}

    assert http.post(f"/student/events/{cs_only['id']}/register", headers=student).status_code == 403
    registered = http.post(f"/student/events/{open_event['id']}/register", headers=student)
    assert registered.status_code == 201, registered.text
    assert http.post(f"/student/events/{open_event['id']}/register", headers=student).status_code == 409
    assert http.get("/student/events/registrations", headers=student).json()[0]["event"]["registered"] is True
    assert http.get(f"/events/{open_event['id']}/registrations", headers=company).json()[0]["student"]["name"] == "Ada Lovelace"
    assert db.registrations.find_one({})["company_id"] == db.companies.find_one({})["_id"]


# ------------------------------------------------------------------ messaging + team + search
def test_messaging_between_company_and_student(http, db, company, student):
    student_id = db.students.find_one({})["_id"]
    thread = http.post("/messages/conversations", headers=company, json={"student_id": student_id}).json()
    sent = http.post(f"/messages/conversations/{thread['id']}/messages", headers=company, json={"body": "Hi Ada"})
    assert sent.status_code == 201, sent.text
    inbox = http.get("/messages/conversations", headers=student).json()
    assert inbox[0]["unread_count"] == 1 and inbox[0]["last_message"]["body"] == "Hi Ada"
    assert http.post(f"/messages/conversations/{thread['id']}/read", headers=student).status_code in (200, 204)
    assert http.get("/messages/conversations", headers=student).json()[0]["unread_count"] == 0
    assert db.message_threads.count_documents({}) == 1 and db.messages.find_one({})["thread_id"] == thread["id"]


def test_team_invitation_flow(http, company):
    invite = http.post("/team/invitations", headers=company,
                       json={"email": "rec@acme.example", "name": "Rae", "role": "recruiter"})
    assert invite.status_code == 201, invite.text
    token = invite.json()["token"]
    assert http.get(f"/team/invitations/token/{token}").json()["company_name"] == "Acme"
    accepted = http.post(f"/team/invitations/token/{token}/accept", json={"name": "Rae", "password": "Passw0rd!"})
    assert accepted.status_code == 200, accepted.text
    recruiter = {"Authorization": f"Bearer {accepted.json()['access_token']}"}
    members = http.get("/team/members", headers=recruiter).json()
    assert {m["role"] for m in members} == {"owner", "recruiter"}
    assert http.post("/jobs", headers=recruiter, json=_job_payload()).status_code == 201


def test_student_search_for_companies(http, company, student):
    results = http.get("/students", headers=company, params={"q": "ada"}).json()
    assert results["total"] == 1 and results["items"][0]["name"] == "Ada Lovelace"
