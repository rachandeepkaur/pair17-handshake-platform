# Architecture & Implementation Notes — Pair 17

Status snapshot of what is actually built and working, as of the company
signup/login milestone. This documents the **current** code, not the full
planned feature set (see `README.md` for setup/run commands and the overall
folder layout).

## 1. Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.12), SQLAlchemy 2.0 ORM, Pydantic v2 |
| Database | MySQL 8, accessed via PyMySQL |
| Auth | bcrypt password hashing (via passlib), JWT (via python-jose) |
| Frontend | React 18 + Vite, React Router, Axios, Tailwind CSS |

## 2. What's implemented so far

**Backend — company signup and shared login**:
- `POST /auth/signup/company` — create a company account
- `POST /auth/login` — authenticate a student *or* company account (same endpoint for both roles)
- JWT issuance with role embedded in the token
- Role-gated request dependencies (`require_student`, `require_company`) ready for future protected routes

**Frontend — company signup and login UI**:
- `/signup/company` — company signup form
- `/login` — shared login form (routes to `/company/dashboard` or `/student/dashboard` based on the role returned by the API)
- `/company/dashboard` — minimal placeholder page with a working sign-out button
- Auth session state (`AuthContext`) persisted in `localStorage`
- A small reusable form layer (`useForm` hook + `FormField` component) so the student signup form can reuse the same plumbing later

**Not implemented yet** (scaffolded as empty files, per the project's full planned structure): student signup endpoint/page, all profile/job/application/event/registration/preference features, the AI assistant, file uploads. The `Student` and `StudentSignupRequest` model/schema already exist (see §4) but have no router wired up yet.

## 3. Database design

### Why a shared `accounts` table

Students and companies log in through **one** endpoint (`POST /auth/login`)
rather than two separate forms, because there's no UX reason to ask "are you
a student or a company?" before login when the backend can resolve it from
the email alone. That only works cleanly if email uniqueness is enforced
*across both roles* — which requires one shared table, not two independent
ones with duplicated `email`/`password_hash` columns.

```
accounts (id, email UNIQUE, password_hash, role ENUM('student','company'), created_at)
    │ 1:1                                │ 1:1
    ▼                                    ▼
students (account_id PK/FK, name, college_name, ...)   companies (account_id PK/FK, company_name, location, ...)
```

- `accounts.role` decides which profile table to join against.
- `students.account_id` / `companies.account_id` are both the primary key *and* the foreign key — there is no separate surrogate ID on the profile tables.
- Login flow: one query against `accounts` by email → verify bcrypt hash → issue a JWT with `{sub: account_id, role}`.

### Full schema (`backend/db/schema.sql`)

| Table | Purpose | Status |
|---|---|---|
| `accounts` | Shared login (email, password hash, role) | ✅ implemented |
| `students` | Student profile, 1:1 with `accounts` | ✅ model exists, no endpoint yet |
| `companies` | Company profile, 1:1 with `accounts` | ✅ implemented |
| `jobs` | Job postings | schema only |
| `applications` | Student job applications + resume path + status | schema only |
| `events` | Company-posted events | schema only |
| `registrations` | Student event registrations | schema only |
| `saved_items` | Saved jobs/events (backs the `save_job_or_event` assistant tool) | schema only |
| `preferences` | Per-student search preferences (backs `get_student_preferences`) | schema only |

Notable schema details:
- `jobs.category` is a MySQL `ENUM('full_time','part_time','on_campus','internship')`.
- `jobs` has a `FULLTEXT` index on `title, description, skills_required` for search.
- `applications.status` is `ENUM('Pending','Reviewed','Declined')`, unique per `(student_id, job_id)`.
- Every student-owned table cascades on delete from `accounts.id`.

## 4. Backend code walkthrough

```
backend/app/
├── config.py          Settings (pydantic-settings), loads .env from the
│                      project root regardless of the process's cwd
├── database.py        SQLAlchemy engine/session, declarative Base, get_db()
├── dependencies.py     get_current_user / require_student / require_company
├── core/
│   ├── security.py    bcrypt hash/verify, JWT create/decode
│   └── exceptions.py  AppError hierarchy + a single FastAPI exception handler
├── models/
│   ├── __init__.py    imports Account, Company, Student so SQLAlchemy
│   │                  registers all mapped classes before any relationship
│   │                  with a forward-reference string (e.g. "Student | None")
│   │                  needs to resolve
│   ├── account.py     Account + AccountRole enum
│   ├── company.py     Company profile
│   └── student.py     Student profile
├── schemas/
│   ├── auth.py        CompanySignupRequest, StudentSignupRequest, LoginRequest,
│   │                  TokenResponse, AccountResponse
│   └── company.py     CompanyOut (signup response)
├── routers/
│   └── auth.py        POST /auth/signup/company, POST /auth/login
└── main.py             FastAPI app, CORS, exception handlers, router registration
```

### `config.py`

Reads `PAIR`, `PORT_BASE`, `DB_PREFIX`, `SEED`, `CITY_SET`, DB credentials,
JWT settings, and Ollama settings from a `.env` file. The `.env` path is
resolved **relative to `config.py`'s own file location** (two directories up
to the project root), not the process's working directory — this matters
because `uvicorn` is normally started from `backend/`, where no `.env`
exists; resolving by cwd would silently fall back to defaults with an empty
DB password.

### `core/security.py`

```python
hash_password(password: str) -> str
verify_password(plain_password: str, password_hash: str) -> bool
create_access_token(subject: str, role: str, expires_delta: timedelta | None = None) -> str
decode_access_token(token: str) -> dict
```

`create_access_token` takes `subject` (the account ID, as a string) rather
than an int — JWT `sub` claims are conventionally strings. The JWT payload
is `{"sub": subject, "role": role, "exp": ...}`.

### `models/account.py` — the `role` enum gotcha

```python
class AccountRole(str, PyEnum):
    STUDENT = "student"
    COMPANY = "company"

role: Mapped[AccountRole] = mapped_column(
    Enum(AccountRole, name="account_role",
         values_callable=lambda enum_cls: [m.value for m in enum_cls]),
    nullable=False,
)
```

By default, SQLAlchemy's `Enum` type stores/matches a Python `Enum` by its
**member name** (`STUDENT`, `COMPANY`), but the MySQL column is
`ENUM('student','company')` (lowercase values), and the rest of the codebase
passes plain lowercase strings (`role="company"`, `account.role != "student"`).
`values_callable` tells SQLAlchemy to use `.value` instead of `.name`,
matching both the DB column and the plain-string comparisons everywhere else.
Without it, reading a row back raises `LookupError: 'company' is not among
the defined enum values`.

### `dependencies.py`

- `get_db()` — one SQLAlchemy session per request, always closed.
- `get_current_user()` — reads the `Authorization: Bearer <token>` header, decodes the JWT, loads the `Account`.
- `require_student` / `require_company` — thin wrappers that additionally check `account.role`, for gating future endpoints.

### `routers/auth.py`

```
POST /auth/signup/company
  body: { company_name, email, password, location }
  → 201 { account_id, company_name, email, location }
  → 409 if the email is already registered

POST /auth/login
  body: { email, password }
  → 200 { access_token, token_type: "bearer", role }
  → 401 on any mismatch (account not found or wrong password —
        same error message either way, so the response can't be used
        to enumerate which emails are registered)
```

Signup writes two rows in one transaction: an `Account` row, then a
`Company` row referencing `account.id` (obtained via `db.flush()` before the
second insert, since the FK needs the generated `account.id`).

## 5. Frontend code walkthrough

```
frontend/src/
├── services/
│   ├── api.js             Axios instance; attaches the JWT from
│   │                      localStorage to every request via an interceptor
│   └── authService.js     signupCompany(), login() — thin wrappers over api.js
├── context/
│   └── AuthContext.jsx    Holds {token, role}; persists to localStorage;
│                          login()/logout(); logout is purely client-side
│                          (JWTs are stateless — nothing to invalidate server-side)
├── hooks/
│   ├── useAuth.js         useContext(AuthContext) with a guard
│   └── useForm.js         Generic form state/validation hook — shared by
│                          every current and future auth/profile form
├── utils/
│   └── validators.js      required(), isEmail(), minLength(), composeValidators()
├── components/common/
│   └── FormField.jsx      One label+input+error component, used by every form
├── routes/
│   ├── AppRoutes.jsx      Route table
│   └── ProtectedRoute.jsx Redirects to /login if unauthenticated or wrong role
└── pages/
    ├── auth/
    │   ├── Login.jsx          Shared login for both roles
    │   └── CompanySignup.jsx  Company signup form
    └── company/
        └── Dashboard.jsx      Placeholder with a working "Sign out" button
```

### Why one `useForm` + `FormField` pair instead of one-off form logic

`CompanySignup.jsx` is built entirely from `useForm` (values/errors/submit
state) + `validators.js` (composable field rules) + `FormField` (the
rendered input). Building the student signup form later is just a different
`initialValues`/`validators` object and a different list of `<FormField>`s —
no new form infrastructure needed.

### Auth flow end to end

1. `CompanySignup` submits to `POST /auth/signup/company` directly via `authService` (signup doesn't touch session state, so it doesn't go through `AuthContext`).
2. `Login` submits to `POST /auth/login` via `AuthContext.login()`, which stores `{token, role}` and persists them to `localStorage`.
3. `api.js`'s request interceptor attaches `Authorization: Bearer <token>` to every subsequent request automatically.
4. `ProtectedRoute` reads `{isAuthenticated, role}` from `AuthContext` and redirects to `/login` if the viewer is unauthenticated or has the wrong role for that route.
5. Signing out calls `AuthContext.logout()`, which clears the token; `ProtectedRoute` then redirects away from any page that required auth on its next render — no manual navigation needed.

## 6. Known gaps / inconsistencies worth tracking

- `schemas/company.py` (`CompanyOut`) and `models/company.py` still use the
  older `Column(...)` SQLAlchemy 1.x-style syntax, while `models/account.py`
  and `models/student.py` use the newer `Mapped[...]` / `mapped_column(...)`
  style. Both work today; worth unifying later for consistency.
- `schemas/auth.py` defines `StudentSignupRequest` and `AccountResponse`,
  but no router uses them yet — they're groundwork for the student signup
  endpoint, not currently reachable from any route.
- `CITY_SET` in `.env` is still a placeholder (`city_one,city_two,city_three`)
  pending the real three cities assigned to pair 17 on Canvas.

## 7. Environment configuration reference

See `.env.example` / `frontend/.env.example` for the full list. Backend
`config.py` reads (via `pydantic-settings`): `PAIR`, `PORT_BASE`,
`DB_PREFIX`, `SEED`, `CITY_SET`, `DB_HOST`, `DB_PORT`, `DB_USER`,
`DB_PASSWORD`, `DB_NAME`, `JWT_SECRET`, `JWT_ALGORITHM`,
`JWT_EXPIRE_MINUTES`, `OLLAMA_MODEL`, `OLLAMA_HOST`. The frontend reads
`VITE_API_URL` (Vite only exposes env vars prefixed `VITE_`).
