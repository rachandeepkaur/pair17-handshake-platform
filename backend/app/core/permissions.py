"""Team roles and what each may do. Single source of truth: the API enforces
these and serves them to the frontend (GET /team/permissions), so the UI's
permission matrix can never drift from the real rules.

Every member can *read* everything in the company workspace; permissions
below gate writes only.
"""

PERMISSIONS = {
    "jobs:write": "Post jobs",
    "applicants:write": "Update application status",
    "events:write": "Create events",
    "messages:write": "Message students",
    "profile:write": "Edit company profile",
    "team:manage": "Invite and manage teammates",
}

ROLE_LABELS = {
    "owner": "Owner",
    "admin": "Admin",
    "recruiter": "Recruiter",
    "hiring_manager": "Hiring Manager",
    "viewer": "Viewer",
}

ROLE_DESCRIPTIONS = {
    "owner": "Full access. The account that created the company.",
    "admin": "Full access, including managing teammates.",
    "recruiter": "Runs recruiting: jobs, applicants, events, and messages.",
    "hiring_manager": "Reviews applicants and messages candidates.",
    "viewer": "Read-only access to the workspace.",
}

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "owner": frozenset(PERMISSIONS),
    "admin": frozenset(PERMISSIONS),
    "recruiter": frozenset({"jobs:write", "applicants:write", "events:write", "messages:write"}),
    "hiring_manager": frozenset({"applicants:write", "messages:write"}),
    "viewer": frozenset(),
}


def has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, frozenset())


def permissions_for(role: str) -> list[str]:
    return sorted(ROLE_PERMISSIONS.get(role, frozenset()))
