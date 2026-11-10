"""Student service: student signup, profile, preferences, and company-side student search."""

from app.core.service_app import create_service_app
from app.routers import preferences, student_auth, student_profile, students

app = create_service_app(
    "student",
    (student_auth, student_profile, preferences, students),
    description="POST /auth/signup/student, /students/*, /student/preferences.",
    serve_profile_pictures=True,
)
