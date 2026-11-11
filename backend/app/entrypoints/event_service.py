"""Event service: company events and student event registration."""

from app.core.service_app import create_service_app
from app.routers import events, student_events

app = create_service_app(
    "event",
    (events, student_events),
    description="/events (company events) and /student/events (browse and register).",
)
