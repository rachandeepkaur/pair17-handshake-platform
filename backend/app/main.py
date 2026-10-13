from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.exceptions import register_exception_handlers
from app.routers import (
    applications,
    auth,
    companies,
    dashboards,
    events,
    jobs,
    messages,
    students,
    team,
)
from app.services.file_service import PICTURE_DIR, ensure_upload_dirs

app = FastAPI(
    title="Handshake Platform API (Pair 17)",
    description="REST API for the student/company recruiting platform. "
    "Authorize with the `access_token` from `POST /auth/login` as a Bearer token.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

for router in (auth, companies, jobs, applications, events, students, messages, team, dashboards):
    app.include_router(router.router)

# Only profile pictures are public. Resumes are served through the
# authorized GET /applications/{id}/resume endpoint instead.
ensure_upload_dirs()
app.mount("/uploads/profile_pictures", StaticFiles(directory=PICTURE_DIR), name="profile_pictures")
