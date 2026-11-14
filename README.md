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

## Kafka event pipeline (Lab 2)

The APIs publish an event after each MySQL commit; three workers consume them and
maintain MongoDB projections.

| Topic | Producer | Consumer | MongoDB collections |
|---|---|---|---|
| `application.created`, `application.updated` | Application service | `p17-application-worker` | `application_events` |
| `application.status_changed` | Application service (company status change) | `p17-application-worker` | `application_events`, `notifications` |
| `event.registration_created` | Event service | `p17-event-worker` | `event_registrations`, `event_stats` |
| `job.created` | Job service | `p17-job-worker` | `job_search_index` |

- **Envelope:** `{event_id, event_type, occurred_at, source, key, data}`. The Kafka key is the
  entity ID, so all events for one application, event or job stay in order on one partition.
- **At-least-once delivery:** offsets are committed only after the MongoDB write.
- **Idempotent writes:** every insert uses a deterministic `_id`, so redelivered or
  re-published events are skipped.
- **Poison messages:** after 3 attempts (backoff 0.5 s, then 1 s) the message goes to
  `<topic>.dlq` with error headers, and the partition moves on.
- **Topics:** created by `p17-kafka-init` (Compose) or the `p17-kafka-topics` Job (Kubernetes),
  with 3 partitions each.
- **Code:** `backend/app/events/` (producer and envelope) and `backend/app/workers/` (consumers).

```bash
scripts/kafka_demos.sh                       # happy path + the 3 failure cases (output in RUN_LOG.txt)
docker compose logs -f p17-application-worker
docker exec p17-kafka /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --describe --group p17-application-worker  # committed offsets and lag
```

## Kubernetes deployment (Lab 2)

Manifests live in [`k8s/`](k8s/) and deploy into the `p17-handshake` namespace. Every
resource name starts with `p17-`.

| Resource | Kind | Replicas (HPA min–max) | Requests / limits |
|---|---|---|---|
| `p17-student-service`, `p17-company-service`, `p17-application-service`, `p17-event-service` | Deployment + ClusterIP Service + HPA | 2 (2–5) | 100m/192Mi · 500m/512Mi |
| `p17-job-service` | Deployment + ClusterIP Service + HPA | 2 (2–6) | 100m/192Mi · 500m/512Mi |
| `p17-assistant-service` | Deployment + ClusterIP Service + HPA | 1 (1–3) | 100m/256Mi · 1/512Mi |
| `p17-frontend` | Deployment + LoadBalancer Service (port 9170) + HPA | 2 (2–4) | 50m/64Mi · 250m/128Mi |
| `p17-mysql`, `p17-mongodb`, `p17-kafka` | StatefulSet + headless Service + 2Gi PVC | 1 | 250m/512–768Mi · 1/1–1.5Gi |
| `p17-backend-config`, `p17-assistant-config`, `p17-frontend-config` | ConfigMap | | |
| `p17-handshake-secrets` | Secret (created by `deploy.sh`, never committed) | | |
| `p17-mysql-init` | ConfigMap built from `backend/db/schema.sql` by `deploy.sh` | | |
| `p17-uploads` | PVC (ReadWriteMany), shared by student, company, application | | |

- **Service discovery:** pods reach each other by Service name. Examples: `DB_HOST=p17-mysql`,
  `KAFKA_BOOTSTRAP_SERVERS=p17-kafka:9092`, and the assistant's
  `http://p17-job-service:9173`. The nginx gateway uses the FQDN
  `p17-<svc>-service.p17-handshake.svc.cluster.local`, because nginx's resolver ignores
  search domains.
- **Probes:** readiness uses `GET /health` (MySQL, MongoDB and Kafka reachable). Liveness uses
  `GET /health/live`, so a database outage removes a pod from load balancing without restarting it.
- **Scaling:** the HPAs target 70% CPU of the requests and need metrics-server. Manual scaling:
  `kubectl -n p17-handshake scale deployment/p17-job-service --replicas=4`.
- **Secrets:** `k8s/secrets.env` is git-ignored. `deploy.sh` generates it with random
  values on first run (template: `k8s/secrets.env.example`). Manifests only reference
  `p17-handshake-secrets` keys. The Mongo URI is assembled in the pod from
  `$(MONGO_PASSWORD)`.

```bash
docker compose build && docker compose --profile seed build   # p17-* images (local cluster uses them directly)
k8s/deploy.sh --seed                                          # secrets, schema, manifests, rollout, demo data
kubectl -n p17-handshake get pods,svc,hpa                     # inspect
kubectl -n p17-handshake logs -f deploy/p17-assistant-service # logs from one service
kubectl delete namespace p17-handshake                        # remove everything (including volumes)
```

The app is at http://localhost:9170 on Docker Desktop Kubernetes. On other clusters, use
`kubectl -n p17-handshake port-forward svc/p17-frontend 9170:9170`, and push the images to a
registry (see the `images:` block in `k8s/base/kustomization.yaml`). On a multi-node cluster,
`p17-uploads` needs a storage class that supports ReadWriteMany.

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

### Assistant context compaction

The assistant automatically compacts a conversation after a model call reaches 70% of the configured context window. A student can also type `/compact` in the assistant chat. The UI reports measured pre-compaction prompt tokens and the estimated token count of the compacted summary.

## Quick smoke test

1. Start the backend and frontend as above.
2. Visit http://localhost:5173/signup/company and create a company account.
3. Sign in at http://localhost:5173/login — you should land on the company dashboard.
