# Student Portal API Contract

## Status and purpose

**Status: student sign-up, profile, and job-discovery routes are implemented; the remaining routes are planned.**

This document defines the integration boundary for the Lab 1 Part A student
portal. It intentionally leaves the existing company routes and their source
code unchanged. Company and student features operate on the same MySQL tables
and SQLAlchemy models, but student-specific paths prevent route collisions.

## Shared data ownership

| Record | Company portal | Student portal |
|---|---|---|
| `jobs` | Creates and reads its own postings | Reads visible postings; creates an application for itself |
| `events` | Creates and reads its own events | Reads upcoming eligible events; creates a registration for itself |
| `applications` | Reads applicants for its jobs; changes status | Creates and reads only its own applications |
| `registrations` | Reads registrants for its events | Creates and reads only its own registrations |
| `students` | Searches and views student profiles | Creates/updates the signed-in student's profile; browses directory records |

The existing shared models are `Student`, `Company`, `Job`, `Event`,
`Application`, and `Registration`. The relationship keys remain unchanged:
`Job.company_id`, `Event.company_id`, `Application.student_id`,
`Application.job_id`, `Registration.student_id`, and `Registration.event_id`.

## Authentication and authorization

- Student routes require the existing Bearer JWT authentication mechanism.
- A student route must require a student account and derive the student ID from
  the authenticated account; it must never accept a client-supplied student ID
  for a write operation.
- Student reads of applications and registrations are limited to the current
  student.
- Existing company authorization and company routes are out of scope for this
  contract and must retain their current behavior.

## Planned student routes

| Method and path | Purpose | Shared data touched |
|---|---|---|
| `POST /auth/signup/student` | **Implemented.** Create a student account and initial student profile from name, email, password, and college name | `accounts`, `students` |
| `GET /students/me` | **Implemented.** Return the signed-in student's profile | `students`, `accounts` |
| `PUT /students/me` | **Implemented.** Update the signed-in student's allowed profile fields | `students`, `accounts` where email is updated |
| `POST /students/me/picture` | **Implemented.** Upload or replace the signed-in student's profile picture | `students` and profile-picture storage |
| `GET /student/jobs` | **Implemented.** Search visible jobs by title/company and filter by category and city | `jobs`, `companies` |
| `GET /student/jobs/{job_id}` | **Implemented.** Return one visible job with the required company/contact details | `jobs`, `companies` |
| `POST /student/jobs/{job_id}/apply` | Upload a PDF resume and create one application for the current student | `applications`, `jobs`, resume storage |
| `GET /student/applications` | List the current student's applications; support status filtering | `applications`, `jobs`, `companies` |
| `GET /student/events` | List upcoming events in increasing date order; support event-name search | `events`, `companies` |
| `GET /student/events/{event_id}` | Return one visible event | `events`, `companies` |
| `POST /student/events/{event_id}/register` | Create one registration for the current student when eligible | `registrations`, `events`, `students` |
| `GET /student/registrations` | List the current student's registered events | `registrations`, `events`, `companies` |
| `GET /student/directory` | Browse/search enrolled students by name or college and filter by major | `students` |
| `GET /student/directory/{student_id}` | Return a student profile suitable for directory viewing | `students` |

## Route separation

The following existing company routes are intentionally not reused or
modified by student code:

| Existing company route | Student counterpart |
|---|---|
| `GET /jobs/{job_id}` | `GET /student/jobs/{job_id}` |
| `GET /events/{event_id}` | `GET /student/events/{event_id}` |
| `GET /jobs/mine` | `GET /student/applications` for a student's application history |
| `GET /events/mine` | `GET /student/registrations` for a student's event history |

## Required rules for later implementation

- Job category values stay compatible with the existing job model:
  `full_time`, `part_time`, `on_campus`, and `internship`.
- Application status values stay compatible with the existing application
  model: `Pending`, `Reviewed`, and `Declined`.
- An application may be created only for an existing visible job before its
  deadline, with a PDF resume, and without a prior application by the same
  student for that job.
- Event registration may be created only for an existing upcoming event when
  the student satisfies the event's eligibility rule and has not already
  registered.
- Resumes remain private. A student may access only their own uploaded resume;
  company-side resume preview remains governed by the existing company
  ownership checks.
- API request/response schemas, error responses, and OpenAPI examples must be
  finalized alongside implementation, not inferred from this planning
  document.
