# pair17-handshake-platform

Distributed Systems for Data Engineering, Pair 17: Handshake-style job and events platform with a local-LLM assistant.

## Demo recording

[Watch the screen-capture of our application portal](https://drive.google.com/file/d/1vRTv-ZeoXDqwvzLa70NRfP7zCFSfea87/view?usp=sharing)

This Zoom recording demonstrates the application from both the student and company user perspectives.

## Pair parameters

| Parameter | Value |
|---|---|
| PAIR | 17 |
| PORT_BASE | 9170 (= 9000 + 17 × 10) |
| Database prefix | `p17` |
| SEED | 17 |
| CITY_SET | Palo Alto, Mountain View, Menlo Park |

## Prerequisites

- Python 3.11+
- Node.js 18+
- MySQL 8+
- [Ollama](https://ollama.com) (serves the local model used by the AI assistant)

## Setup

### 1. Clone and configure environment variables

```bash
git clone <repo-url>
cd pair17-handshake-platform
cp frontend/.env.example frontend/.env
```

Create a root `.env` file with your local MySQL credentials. Pair 17 uses Palo Alto, Mountain View, and Menlo Park.

### 2. Database

```bash
mysql -u root -p < backend/db/schema.sql
```

Upgrading a database created before team accounts and messaging existed? Apply
the migration instead (safe to re-run). It adds the team and messaging tables
and makes each existing company's signup account its owner:

```bash
mysql -u root -p < backend/db/migrations/001_team_messages.sql
```

Populate a fresh database with deterministic demo data (50 companies, 200
students, 300 jobs, 1,500 applications, and 100 events) with:

```bash
python backend/db/seed/generate_seed.py
```

The generator validates that `CITY_SET` contains your three assigned cities
and refuses to overwrite existing data. To replace all database application data:

```bash
python backend/db/seed/generate_seed.py --reset
```

Seeded accounts use password `SeedPass17!`. For example, use
`student001@seed.p17.example` or `company001@seed.p17.example`.

### 3. Backend (FastAPI)

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cd backend
uvicorn app.main:app --reload --port 9170
```

- API base URL: http://localhost:9170
- Swagger UI: http://localhost:9170/docs

### 4. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

- App: http://localhost:5173

### 5. Local LLM for the AI assistant

```bash
ollama pull qwen3:8b        # default; use llama3-groq-tool-use:8b or qwen3:4b as a fallback
ollama serve
```

## Docker deployment (Lab 2)

The API runs as six services built from the shared `backend/app` code. Each service
has its own Dockerfile in `backend/docker/<service>/`, installs only its own
requirements, and mounts only its routers (`backend/app/entrypoints/`).

| Container | Image | Host port | Owns |
|---|---|---|---|
| `p17-frontend` | `p17-frontend` | 9170 | React build + nginx gateway (`/api/*` → services) |
| `p17-student-service` | `p17-student-service` | 9171 | `/auth/signup/student`, `/students`, `/student/preferences`, profile pictures |
| `p17-company-service` | `p17-company-service` | 9172 | `/auth/login`, `/auth/signup/company`, `/companies`, `/team`, `/messages`, `/dashboards` |
| `p17-job-service` | `p17-job-service` | 9173 | `/jobs`, `/student/jobs` |
| `p17-application-service` | `p17-application-service` | 9174 | `/applications`, `/student/jobs/{id}/apply`, `/student/applications` |
| `p17-event-service` | `p17-event-service` | 9175 | `/events`, `/student/events` |
| `p17-assistant-service` | `p17-assistant-service` | 9176 | `/assistant` (uses Ollama on the host) |
| `p17-mongodb` | `mongo:7.0` | 9177 | MongoDB |
| `p17-mysql` | `mysql:8.0` | 9178 | MySQL (Lab 1 system of record, schema loaded on first start) |
| `p17-kafka` | `apache/kafka:3.8.0` | 9179 | Kafka, single-node KRaft (`p17-kafka:9092` inside the network) |

Every service exposes `GET /health/live` (process up) and `GET /health` (200 only when
MySQL, MongoDB, and Kafka are reachable, 503 otherwise). The Docker `HEALTHCHECK` and
compose `depends_on: service_healthy` use `/health`. The assistant's `/health` also reports
Ollama and the other platform services. Through the gateway, use
`http://localhost:9170/api/health/<service>`.

### Run the stack

Prerequisites: Docker Desktop running, and Ollama on the host (`ollama serve`, with
`qwen3:8b` pulled) for the assistant. Run every command from the repository root.

**Build** the seven `p17-*` images (six services and the frontend):

```bash
docker compose build                       # all images
docker compose build p17-job-service       # one service after a code change
docker images "p17-*"                      # list the built images
```

**Start** the stack and load demo data:

```bash
docker compose up -d --wait                          # start; returns once every container is healthy
docker compose --profile seed run --rm p17-db-seed   # first run only: 50 companies, 200 students, 300 jobs
```

`docker compose up -d --build --wait` builds and starts in one step.
App: http://localhost:9170 (sign in as `student001@seed.p17.example` / `SeedPass17!`).
Swagger for each service: `http://localhost:917N/docs` (N = 1 to 6).

**Inspect** the running stack:

```bash
docker compose ps                                    # status and health of every container
docker compose logs -f p17-assistant-service         # follow one service's logs
docker compose logs --tail 50                        # recent logs from all containers
curl -s http://localhost:9170/api/health/assistant   # a service's /health through the gateway
curl -s http://localhost:9173/health                 # a service's /health on its own port
docker inspect --format '{{json .State.Health}}' p17-job-service   # Docker health-check history
docker network inspect p17-handshake-net             # containers attached to the network
docker compose exec p17-mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" p17_handshake -e "SHOW TABLES"'
docker compose exec p17-mongodb mongosh -u p17_admin -p p17_mongo_pass --quiet --eval 'db.adminCommand("ping")'
```

**Verify** frontend → backend, backend → databases, and assistant → platform services:

```bash
scripts/verify_local.sh                    # health, gateway routing, MySQL and MongoDB, assistant reach
scripts/verify_local.sh --chat --failover  # + one real assistant turn, + MongoDB outage and recovery
```

**Stop** the stack:

```bash
docker compose stop                        # stop containers, keep them and their data
docker compose down                        # remove containers and network, keep data volumes
docker compose --profile seed down -v      # also delete the MySQL, MongoDB, Kafka, and upload volumes
```

Optional overrides in the root `.env`: `P17_DB_PASSWORD`, `P17_MYSQL_ROOT_PASSWORD`,
`P17_MONGO_PASSWORD`, `JWT_SECRET`, `OLLAMA_MODEL`, `P17_OLLAMA_HOST`.

## Running tests

```bash
source .venv/bin/activate
cd backend
pytest
```

## Assistant evaluations (real model)

Run from the repository root with Ollama running and the database seeded. Each one is slow on a CPU (several minutes per turn).

```bash
python backend/evaluation/run_transcripts.py         # Part B: five transcripts -> docs/transcripts/
python backend/evaluation/run_confirmation_demo.py   # Part C: decline/approve a save -> docs/evaluation/confirmation_demo.txt
python backend/evaluation/run_injection_eval.py      # Part C: 5 injection queries, defense off/on -> docs/evaluation/injection_eval.md
python backend/evaluation/run_reliability_eval.py    # Part C: 22 turns, repair off/on -> docs/evaluation/reliability_eval.md
python backend/evaluation/agent_harness.py           # Lab 2: deterministic guardrail harness -> docs/evaluation/agent_harness.jsonl
```

`run_injection_eval.py` adds one job and one event with injected instructions. Remove them with
`python backend/db/seed/injected_content.py --remove`.

## Quick smoke test

1. Start the backend and frontend as above.
2. Visit http://localhost:5173/signup/company and create a company account.
3. Sign in at http://localhost:5173/login — you should land on the company dashboard.
