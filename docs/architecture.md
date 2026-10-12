# Architecture & Implementation Notes — Pair 17

Status snapshot of what is built and working: the **company portal** is
feature-complete against the Lab 1 Part A company rubric. The student portal,
seed generator, and AI assistant (Parts B/C) are not built yet. See
`README.md` for setup/run commands.

## 1. Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.12), SQLAlchemy 2.0 ORM, Pydantic v2 |
| Database | MySQL 8, accessed via PyMySQL |
| Auth | bcrypt password hashing (passlib), JWT bearer tokens (python-jose) |
| Frontend | React 18 + Vite, React Router, Axios, Tailwind CSS, lucide-react icons |

## 2. Rubric coverage — company features

| Lab 1 requirement | Where it lives |
|---|---|
| Signup with company name, email, password, location; sign in/out | `POST /auth/signup/company`, `POST /auth/login`; `/signup/company`, `/login`, sign-out in the top-bar menu |
| Dashboard for posting jobs (title, posting date, deadline, location, salary, description, category) | `POST /jobs`; `/company/dashboard`, `/company/jobs/new` |
| View owned job postings and the students who applied to each | `GET /jobs/mine`, `GET /jobs/{id}/applications`; `/company/jobs`, `/company/jobs/:id`, `/company/applicants` |
| Open a student profile, preview the PDF resume, set status Pending/Reviewed/Declined | `GET /applications/{id}`, `GET /applications/{id}/resume`, `PATCH /applications/{id}/status`; `/company/applications/:id` |
| Company profile (name, location, description, contact, picture) with updates | `GET/PUT /companies/me`, `POST /companies/me/picture`; `/company/profile` |
| Students tab: search by name, college, or skillset and view profiles | `GET /students`, `GET /students/{id}`; `/company/students`, `/company/students/:id` |
| Events tab: post events (name, description, date, time, location, eligibility); view registered students and their profiles | `POST /events`, `GET /events/mine`, `GET /events/{id}/registrations`; `/company/events`, `/company/events/new`, `/company/events/:id` |
| Validate input, encrypt passwords, exception handling, restrict to authorized actions | Pydantic schemas + client-side validators; bcrypt; `core/exceptions.py`; `require_company` + ownership checks (§5) |
| Axios with loading and error states; separate components, pages, services | `services/*`, `hooks/useFetch.js`, skeleton loaders + `ErrorMessage` on every page |
| Swagger UI | `http://localhost:9170/docs` — click **Authorize** and paste the `access_token` from `/auth/login` |

Messages, Team & Permissions, and Settings appear in the sidebar under
**Coming soon**. They have no backend and are not part of the rubric.

## 3. Database design

### Why a shared `accounts` table

Students and companies sign in through **one** endpoint, resolved by email.
That requires email uniqueness *across both roles*, so login credentials live
in one table and each role has a 1:1 profile table keyed on `account_id`.

```
accounts (id, email UNIQUE, password_hash, role ENUM('student','company'))
    │ 1:1                                  │ 1:1
    ▼                                      ▼
students (account_id PK/FK, …)        companies (account_id PK/FK, …)
    │                                      │ 1:N
    │ 1:N                                  ├──▶ jobs ──1:N──▶ applications ◀──N:1── students
    └──────────────────────────────────────┴──▶ events ─1:N─▶ registrations ◀─N:1─ students
```

| Table | Status |
|---|---|
| `accounts`, `companies`, `jobs`, `applications`, `events`, `registrations` | ✅ model + endpoints |
| `students` | ✅ model; read endpoints (search, profile). No student signup yet |
| `saved_items`, `preferences` | schema only (for the Part B assistant tools) |

Schema details worth knowing: `jobs.category` is
`ENUM('full_time','part_time','on_campus','internship')`;
`applications.status` is `ENUM('Pending','Reviewed','Declined')` and unique
per `(student_id, job_id)`; every child row cascades on delete.

## 4. Backend layout

```
backend/app/
├── config.py           Settings; loads .env from the project root regardless of cwd
├── database.py         engine, SessionLocal, Base, get_db()
├── dependencies.py      get_current_user (HTTP Bearer), require_student, require_company
├── core/
│   ├── security.py     bcrypt hash/verify, JWT create/decode
│   └── exceptions.py   AppError hierarchy + handlers (see §6)
├── models/             Account, Company, Student, Job, Application, Event, Registration
│   └── __init__.py     imports every model so string relationships ("Student") resolve
├── schemas/            Pydantic request/response models; common.py has Page[T] and
│                       shared trim/blank-to-NULL validators
├── services/           all queries and business rules; routers stay thin
│   ├── job_service.py          create, list with applicant counts, owned-job lookup
│   ├── application_service.py  list/filter, detail, status update, resume path
│   ├── event_service.py        create, list with registration counts, registrants
│   ├── student_service.py      paginated search, profile
│   ├── company_service.py      profile read/update, picture, completion %
│   └── file_service.py         upload validation, safe paths (see §7)
└── routers/            auth, companies, jobs, applications, events, students, dashboards
```

### API reference (company portal)

All routes except `/auth/*` need `Authorization: Bearer <token>`.

| Method & path | Purpose |
|---|---|
| `POST /auth/signup/company` | Create company account → 201, or 409 if the email exists |
| `POST /auth/login` | Any role → `{access_token, token_type, role}`; 401 on bad credentials |
| `GET /companies/me` · `PUT /companies/me` | Read / update company profile |
| `POST /companies/me/picture` | Multipart image upload (JPEG/PNG/WebP, ≤ 2 MB) |
| `POST /jobs` | Post a job; `posting_date` defaults to today, `deadline ≥ posting_date` |
| `GET /jobs/mine` | Own postings, each with `applicant_count` |
| `GET /jobs/{id}` | One owned posting |
| `GET /jobs/{id}/applications?status=` | Applicants to one owned posting |
| `GET /applications/company?job_id=&status=` | All applicants across the company's postings |
| `GET /applications/{id}` | Application + applicant's full student profile |
| `PATCH /applications/{id}/status` | `{status: "Pending" \| "Reviewed" \| "Declined"}` |
| `GET /applications/{id}/resume` | The applicant's PDF, `Content-Disposition: inline` |
| `POST /events` · `GET /events/mine` · `GET /events/{id}` | Create / list (with `registration_count`) / read own events; date cannot be in the past |
| `GET /events/{id}/registrations` | Students registered for an owned event |
| `GET /students?q=&college=&skills=&major=&limit=&offset=` | Paginated search; `skills` is comma-separated and matches *any* |
| `GET /students/{id}` | Student profile |
| `GET /dashboards/company` | Counts, status breakdown, profile completion, recent applicants |

## 5. Authorization rules

- **No/invalid/expired token → 401.** The frontend's Axios interceptor clears
  the session and redirects to `/login`.
- **Wrong role → 403** (`require_company` / `require_student`).
- **Another company's job, application, or event → 404**, not 403. Lookups go
  through `get_owned_job` / `get_owned_application` / `get_owned_event`, which
  treat "doesn't exist" and "not yours" the same so IDs can't be probed.
- Students endpoints accept any signed-in role, because the rubric lets
  students browse students too.

## 6. Error handling

`core/exceptions.py` registers handlers so every error body is
`{"detail": "<one readable message>"}`, which the frontend shows directly:

| Source | Status | Body |
|---|---|---|
| `AppError` subclasses (`BadRequest`, `Unauthorized`, `Forbidden`, `NotFound`, `Conflict`) | 400/401/403/404/409 | the error's message |
| Pydantic validation | 422 | first error as `field: message`, plus the full `errors` list |
| Database `IntegrityError` | 409 | generic conflict message (details logged) |
| Anything else | 500 | generic message; traceback logged, never sent to the client |

## 7. File handling

- **Resumes are private.** They are stored under `backend/uploads/resumes/`
  and served **only** via `GET /applications/{id}/resume`, after the
  ownership check. `resolve_resume` refuses any path that resolves outside
  that folder. The frontend fetches the PDF as a blob with the auth header
  and previews it in an `<iframe>` through an object URL (a plain
  `<iframe src>` can't send the header).
- **Profile pictures are public.** They are mounted at
  `/uploads/profile_pictures/` and validated by their leading bytes (JPEG/PNG/WebP
  signature), not the client-supplied content type, and capped at 2 MB. Files
  get random names; the previous picture is deleted on replacement.
- `backend/uploads/` is gitignored.

## 8. Frontend layout

```
frontend/src/
├── services/        api.js (token + 401 interceptors, apiUrl, errorMessage),
│                    company/job/application/event/student/auth services
├── hooks/           useAuth, useForm (form state + validation), useFetch
│                    (loading/error, reload, local setData patching)
├── utils/           constants (categories, statuses), validators, format
│                    (dates parsed as local, en-US currency/time)
├── components/
│   ├── ui/          Button, Card, StatCard, StatusBadge, Tabs, PageHeader,
│   │                Avatar, SkillTags, Skeleton, EmptyState
│   ├── common/      Sidebar, Navbar, FormField (+TextArea/Select), Modal +
│   │                ConfirmDialog, Pagination, ErrorMessage, ComingSoon
│   ├── layout/      CompanyLayout — shell; shares the dashboard summary with
│   │                pages via outlet context (`company`, `reloadCompany`)
│   ├── applications/ ApplicantsTable, StatusUpdater, ResumePreview
│   ├── profile/     StudentProfileView, CompanyProfileForm, ProfilePicture
│   ├── students/    StudentCard
│   └── events/      RegistrantList
└── pages/company/   Dashboard, MyJobs, PostJob, JobDetail, Applicants,
                     ApplicantProfile, CompanyEvents, CreateEvent,
                     EventRegistrations, StudentSearch, StudentProfile,
                     Analytics, CompanyProfile, Messages/Team/Settings (coming soon)
```

UX conventions applied across pages: skeleton loaders while loading, an
`ErrorMessage` for failed requests, a written empty state for every list,
inline field validation that mirrors the server rules, confirmation before
declining an applicant, status shown as a dot plus text label (never color
alone), visible keyboard focus rings, a skip-to-content link, and layouts that
reflow to one column at phone width.

## 9. Known gaps

- **No seed data yet.** The rubric's generator (300 jobs, 1,500 applications,
  200 students, 50 companies, 100 events across `CITY_SET` with
  `random_state = SEED`) is not written; `CITY_SET` in `.env` is still a
  placeholder.
- **Student-side features** (signup, applying with a resume upload, event
  registration) aren't built, so applications and registrations currently
  enter the database only through fixtures or the future seed script.
- Job postings can't be edited or deleted. This isn't required by the rubric.
- Student search uses `LIKE '%term%'` filters. That's fine at the rubric's 200
  students; the `FULLTEXT` index on `jobs` is unused until job search is
  built.

## 10. Environment configuration

See `.env.example` / `frontend/.env.example`. The backend reads `PAIR`,
`PORT_BASE`, `DB_PREFIX`, `SEED`, `CITY_SET`, `DB_HOST`, `DB_PORT`,
`DB_USER`, `DB_PASSWORD`, `DB_NAME`, `JWT_SECRET`, `JWT_ALGORITHM`,
`JWT_EXPIRE_MINUTES`, `OLLAMA_MODEL`, `OLLAMA_HOST`. The frontend reads
`VITE_API_URL`.
