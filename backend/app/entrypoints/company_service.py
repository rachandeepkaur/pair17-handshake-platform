"""Company service: login, company signup/profile, team, messaging, dashboards."""

from app.core.service_app import create_service_app
from app.routers import auth, companies, dashboards, messages, team

app = create_service_app(
    "company",
    (auth, companies, team, messages, dashboards),
    description="/auth/login, /auth/signup/company, /auth/change-password, /companies, /team, /messages, /dashboards.",
)
