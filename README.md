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
```

`run_injection_eval.py` adds one job and one event with injected instructions. Remove them with
`python backend/db/seed/injected_content.py --remove`.

## Quick smoke test

1. Start the backend and frontend as above.
2. Visit http://localhost:5173/signup/company and create a company account.
3. Sign in at http://localhost:5173/login — you should land on the company dashboard.
