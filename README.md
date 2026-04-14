# Opposing Counsel Simulator

Clause-level contract negotiation review. Not a "chat with a PDF" demo — the system treats negotiation as a structured, clause-by-clause workflow with inspectable evidence, typed schemas, and configurable model adapters.

**Pipeline:** `ingest → parse → diff → classify → retrieve → simulate → critique → score → render`

---

## What it does

Given an original contract, a revised/redlined contract, an opposing-counsel persona, and optional playbook/precedent/fallback documents, the app:

- detects changed clauses
- classifies issue types (liability, indemnity, payment, confidentiality, etc.)
- retrieves supporting evidence via hybrid BM25 + vector search
- simulates opposing-counsel responses per persona
- generates counterproposals grounded in playbook evidence
- scores friction, pushback probability, and delay risk per clause
- renders a clause-by-clause review interface

---

## Quick start (no backend needed)

```bash
npm install
npm run dev
```

Open `http://localhost:3000` and click **Run Demo**. The demo runs entirely in the browser with bundled sample contracts — no API keys, no uploads, no backend process.

---

## Full stack setup

### 1. Environment

```bash
cp .env.example .env
```

### 2. Backend (Python 3.11+)

```bash
cd apps/api
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
python -m app.utils.seed_data
uvicorn app.main:app --reload
```

### 3. Frontend

```bash
npm install
npm run dev
```

### 4. Docker (one command)

```bash
cp .env.example .env
docker compose up --build
```

| Service  | URL                      |
|----------|--------------------------|
| Web      | http://localhost:3000    |
| API      | http://localhost:8000    |
| Qdrant   | http://localhost:6333    |
| Postgres | localhost:5432           |
| Redis    | localhost:6379           |

---

## Architecture

```
          Next.js UI
          (upload / review / score)
               |
               v
          FastAPI (typed REST)
               |
       ┌───────┼───────┐
       v       v       v
  PostgreSQL  Redis  Qdrant
  runs+docs  Celery  vectors
       └───────┼───────┘
               v
  diff → classify → retrieve → simulate → critique → score
```

---

## Tech stack

| Layer | Stack |
|-------|-------|
| Backend | FastAPI, SQLAlchemy 2, Pydantic v2, Alembic, Celery |
| Storage | PostgreSQL, Redis, Qdrant |
| Retrieval | Hybrid BM25 (rank-bm25) + vector similarity, configurable rerank weights |
| LLM | OpenAI-compatible adapter, rule-based fallback for offline demo |
| Frontend | Next.js, TypeScript, Tailwind, React Query |

---

## Retrieval

Hybrid BM25 + vector search with:

- Regex tokenizer (handles hyphenated legal terms, strips punctuation)
- Per-issue-type query expansion (legal synonyms to improve recall)
- Configurable lexical/vector weights via `RETRIEVAL_LEXICAL_WEIGHT` / `RETRIEVAL_VECTOR_WEIGHT`
- Per-call `RetrievalMetrics` logged with candidate count, score distribution, and vector availability

---

## Monorepo layout

```
.
├── apps
│   ├── api          FastAPI backend
│   └── web          Next.js frontend
├── packages
│   ├── personas     Built-in persona definitions
│   ├── prompts      LLM prompt templates
│   ├── sample-data  Demo contracts, evidence, example run
│   └── schemas      Shared TypeScript types
├── infrastructure
│   └── docker
└── docs
```

---

## API endpoints

```
GET  /api/health
POST /api/demo/happy-path
POST /api/documents/original
POST /api/documents/revised
POST /api/documents/evidence
GET  /api/personas
POST /api/runs
GET  /api/runs/{run_id}/status
GET  /api/runs/{run_id}/summary
GET  /api/runs/{run_id}/clauses
GET  /api/runs/{run_id}/clauses/{clause_change_id}/evidence
```

---

## Environment variables

```
DATABASE_URL
REDIS_URL
QDRANT_URL / QDRANT_COLLECTION
CELERY_BROKER_URL / CELERY_RESULT_BACKEND
LLM_PROVIDER / LLM_API_KEY / LLM_BASE_URL / LLM_MODEL
EMBEDDING_PROVIDER / EMBEDDING_API_KEY / EMBEDDING_BASE_URL / EMBEDDING_MODEL / EMBEDDING_DIMENSION
RETRIEVAL_LEXICAL_WEIGHT   # default 0.45
RETRIEVAL_VECTOR_WEIGHT    # default 0.55
USE_RULE_BASED_AI_FALLBACK
NEXT_PUBLIC_API_BASE_URL
```

---

## Tests

```bash
cd apps/api
pytest
```

Covers: parsing, clause diffing, issue classification, simulation + critique + scoring flow.

---

## Makefile

```bash
make api-install   # install Python deps
make api-migrate   # run alembic migrations
make api-seed      # seed personas
make api-dev       # start uvicorn dev server
make api-test      # run pytest
make web-install   # npm install
make web-dev       # start Next.js dev server
make up            # docker compose up --build
```

---

## Documentation

- [Architecture](docs/architecture.md)
- [Data Model](docs/data-model.md)
- [API](docs/api.md)
- [Prompting](docs/prompting.md)
