# pair17-handshake-platform

Distributed Systems for Data Engineering, Pair 17: Handshake-style job and events platform with a local-LLM assistant.

## Pair parameters

| Parameter | Value |
|---|---|
| PAIR | 17 |
| PORT_BASE | 9170 (= 9000 + 17 × 10) |
| Database / Kafka prefix | `p17` |
| SEED | 17 |
| CITY_SET | TODO — the three cities assigned to pair 17 on Canvas |

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
cp .env.example .env
cp frontend/.env.example frontend/.env
```

Edit `.env` with your local MySQL credentials and the real `CITY_SET` for pair 17.

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

Once the seed generator is implemented, populate sample data with:

```bash
python backend/db/seed/generate_seed.py
```

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

## Quick smoke test

1. Start the backend and frontend as above.
2. Visit http://localhost:5173/signup/company and create a company account.
3. Sign in at http://localhost:5173/login — you should land on the company dashboard.
