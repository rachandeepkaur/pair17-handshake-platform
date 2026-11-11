"""Application service: students apply to jobs; companies review applicants and resumes."""

from app.core.service_app import create_service_app
from app.routers import applications, student_applications

app = create_service_app(
    "application",
    (applications, student_applications),
    description="/applications (company review) and /student/jobs/{id}/apply, /student/applications.",
)
