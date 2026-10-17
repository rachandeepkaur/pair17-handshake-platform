from datetime import date, time
from decimal import Decimal
from types import SimpleNamespace

from app.assistant.prompts import system_prompt_for_role
from app.assistant.registry import tool_registry_for_role
from app.assistant.tools.get_job_details import get_job_details
from app.assistant.tools.get_platform_options import get_platform_options
from app.assistant.tools.get_student_preferences import get_student_preferences
from app.assistant.tools.search_events import search_events
from app.assistant.tools.search_jobs import search_jobs
from app.assistant.tools.save_job_or_event import save_job_or_event
from app.assistant.tools.schemas import AssistantContext
from app.core.exceptions import NotFoundError


def _context() -> AssistantContext:
    return AssistantContext(account_id=12, role="student", db=object())


def test_student_registry_has_all_read_only_part_b_tools() -> None:
    registry = tool_registry_for_role("student")

    assert [tool["function"]["name"] for tool in registry.schemas] == [
        "get_student_preferences",
        "get_platform_options",
        "search_jobs",
        "get_job_details",
        "search_events",
        "save_job_or_event",
    ]


def test_student_prompt_requires_preferences_before_city_recommendations() -> None:
    prompt = system_prompt_for_role("student")

    assert "first call get_student_preferences, then call search_jobs" in prompt
    assert "MUST call a tool" in prompt
    assert "For jobs or internships, call search_jobs." in prompt
    assert "get_platform_options" in prompt


def test_platform_options_returns_configured_search_vocabulary(monkeypatch) -> None:
    monkeypatch.setattr("app.assistant.tools.get_platform_options.settings.city_set", "Palo Alto, Menlo Park")

    result = get_platform_options(_context(), {})

    assert "Available cities: Palo Alto, Menlo Park" in result
    assert "internship" in result


def test_get_student_preferences_reports_missing_preferences(monkeypatch) -> None:
    monkeypatch.setattr("app.assistant.tools.get_student_preferences.Preference", object())
    context = AssistantContext(account_id=12, role="student", db=SimpleNamespace(get=lambda *_args: None))

    assert get_student_preferences(context, {}) == "No saved job or event preferences are available for this student."


def test_search_jobs_passes_all_supported_filters(monkeypatch) -> None:
    captured = {}
    job = SimpleNamespace(
        id=4,
        title="Machine Learning Intern",
        company_name="NVIDIA",
        location="Palo Alto, CA",
        city="Palo Alto",
        category="internship",
        salary=Decimal("45000"),
        deadline=date(2026, 11, 30),
    )

    def fake_list_jobs(_db, **filters):
        captured.update(filters)
        return SimpleNamespace(items=[job])

    monkeypatch.setattr("app.assistant.tools.search_jobs.student_job_service.list_jobs", fake_list_jobs)

    result = search_jobs(
        _context(),
        {
            "title": "machine learning",
            "company": "NVIDIA",
            "category": "internship",
            "city": "Palo Alto",
            "min_salary": 40000,
            "skills": "Python, PyTorch",
            "deadline_on_or_before": "2026-11-30",
            "remote": False,
        },
    )

    assert captured["min_salary"] == Decimal("40000")
    assert captured["deadline_on_or_before"] == date(2026, 11, 30)
    assert captured["remote"] is False
    assert "ID 4: Machine Learning Intern at NVIDIA" in result


def test_get_job_details_returns_clear_missing_id_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.assistant.tools.get_job_details.student_job_service.get_job",
        lambda *_args: (_ for _ in ()).throw(NotFoundError("Job not found")),
    )

    assert get_job_details(_context(), {"job_id": 999}) == "Job 999 was not found: Job not found."


def test_search_events_passes_date_and_eligibility_filters(monkeypatch) -> None:
    captured = {}
    event = SimpleNamespace(
        id=8,
        name="Technology Career Fair 8",
        event_date=date(2026, 11, 12),
        event_time=time(10, 0),
        location="Mountain View, CA",
        company_name="Google",
        eligibility="Computer Science",
    )

    def fake_list_events(_db, _student_id, **filters):
        captured.update(filters)
        return [event]

    monkeypatch.setattr("app.assistant.tools.search_events.student_event_service.list_events", fake_list_events)

    result = search_events(
        _context(),
        {
            "city": "Mountain View",
            "start_date": "2026-11-01",
            "end_date": "2026-11-30",
            "major": "Computer Science",
            "eligible_only": True,
        },
    )

    assert captured["start_date"] == date(2026, 11, 1)
    assert captured["end_date"] == date(2026, 11, 30)
    assert captured["major"] == "Computer Science"
    assert captured["eligible_only"] is True
    assert "ID 8: Technology Career Fair 8" in result


def test_save_job_or_event_creates_a_saved_item(monkeypatch) -> None:
    added = []
    committed = []
    db = SimpleNamespace(
        scalar=lambda _query: None,
        add=added.append,
        commit=lambda: committed.append(True),
        rollback=lambda: None,
    )
    monkeypatch.setattr("app.assistant.tools.save_job_or_event._visibility_error", lambda *_args: None)

    result = save_job_or_event(AssistantContext(account_id=12, role="student", db=db), {"item_type": "job", "item_id": 4})

    assert result == "Saved job 4 for this student."
    assert added[0].student_id == 12
    assert added[0].item_type == "job"
    assert added[0].item_id == 4
    assert committed == [True]


def test_save_job_or_event_rejects_duplicates() -> None:
    db = SimpleNamespace(
        scalar=lambda _query: 8,
        add=lambda _item: None,
        commit=lambda: None,
        rollback=lambda: None,
    )

    result = save_job_or_event(AssistantContext(account_id=12, role="student", db=db), {"item_type": "event", "item_id": 7})

    assert result == "Event 7 is already saved."
