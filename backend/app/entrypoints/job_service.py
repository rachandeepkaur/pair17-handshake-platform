"""Job service: company job postings and student job browsing."""

from app.core.service_app import create_service_app
from app.routers import jobs, student_jobs

app = create_service_app(
    "job",
    (jobs, student_jobs),
    description="/jobs (company postings) and /student/jobs (student search and details).",
)
