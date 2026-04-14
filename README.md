# Opposing Counsel Simulator

Opposing Counsel Simulator is a production-style MVP for clause-level contract negotiation review. It ingests an original contract, a revised contract, and optional supporting playbooks or fallback clauses, then runs a deterministic workflow:

`ingest -> parse -> diff -> classify -> retrieve -> simulate -> critique -> score -> render`

This is intentionally not a "chat with a PDF" demo. The system treats negotiation as a structured clause-by-clause workflow with inspectable evidence, typed schemas, and configurable model adapters.

## Product Scope

Given:

1. an original contract,
2. a revised or redlined contract,
3. a selected opposing-counsel persona,
4. optional playbook / precedent / fallback documents,

the app will:

- detect changed clauses
- classify issue types
- retrieve supporting evidence
- simulate opposing-counsel responses
- generate counterproposals
- explain the rationale
- score likely friction
- render a legal-tech review interface

## Monorepo Layout

```text
.
├── apps
│   ├── api
│   │   ├── app
│   │   ├── alembic
│   │   └── tests
│   └── web
│       └── src
├── packages
│   ├── personas
│   ├── prompts
│   ├── sample-data
│   └── schemas
├── infrastructure
│   └── docker
└── docs
```

## Architecture

```text
                +--------------------------+
                |        Next.js UI        |
                | upload / review / score  |
                +------------+-------------+
                             |
                             v
                   +---------+---------+
                   |      FastAPI      |
                   |   typed REST API  |
                   +---------+---------+
                             |
          +------------------+------------------+
          |                  |                  |
          v                  v                  v
   +------+-------+   +------+-------+   +------+------+
   | PostgreSQL   |   | Redis/Celery |   |   Qdrant    |
   | runs + docs  |   | async jobs   |   | embeddings  |
   +------+-------+   +------+-------+   +------+------+
          |                  |                  |
          +------------------+------------------+
                             |
                             v
      ingest -> parse -> diff -> classify -> retrieve
                   -> simulate -> critique -> score
```

## Key Decisions

- Backend uses `FastAPI`, `SQLAlchemy`, `Pydantic v2`, `Alembic`, `PostgreSQL`, `Redis`, `Celery`, and `Qdrant`.
- Retrieval is hybrid: BM25 lexical scoring plus vector similarity, merged with a transparent weighted rerank.
- Parsing, diffing, classification, simulation, critique, and scoring are separate modules rather than one giant prompt.
- Model providers are abstracted behind OpenAI-compatible adapters with deterministic local fallbacks for demoability.
- UI is a serious contract review surface built with `Next.js`, `TypeScript`, `Tailwind`, React Query, and local shadcn-style components.

## Quick Demo

No backend, API keys, uploads, or external files are required for the demo path.

```bash
npm install
npm run dev
```

Then open `http://localhost:3000` and click `Run Demo`.

What happens:

1. The app loads bundled sample contracts, playbook, precedent, and fallback clauses.
2. It selects a built-in persona and runs a deterministic local workflow:
   `parse -> diff -> classify -> retrieve -> simulate -> score`
3. The dashboard, clause review queue, evidence panel, rationale, and counterproposals all populate immediately.

The local demo path works even if the API is offline.

## Local Setup

### 1. Environment

```bash
cp .env.example .env
```

### 2. Backend

Supported target runtime is Python `3.11+`.

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

### 4. Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Services:

- API: `http://localhost:8000`
- Web: `http://localhost:3000`
- Qdrant: `http://localhost:6333`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

## Makefile Commands

```bash
make api-install
make api-migrate
make api-seed
make api-demo
make api-dev
make api-test
make web-install
make web-dev
make up
```

## Environment Variables

Important variables live in `.env.example`:

- `DATABASE_URL`
- `REDIS_URL`
- `QDRANT_URL`
- `QDRANT_COLLECTION`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `LLM_PROVIDER`
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `EMBEDDING_PROVIDER`
- `EMBEDDING_API_KEY`
- `EMBEDDING_BASE_URL`
- `EMBEDDING_MODEL`
- `EMBEDDING_DIMENSION`
- `USE_RULE_BASED_AI_FALLBACK`
- `NEXT_PUBLIC_API_BASE_URL`

## Sample Workflow

### One-click local demo

1. Run `npm install`.
2. Run `npm run dev`.
3. Open the web app and click `Run Demo`.
4. Review the populated dashboard, clause queue, evidence hits, opposing-counsel rationale, and counterproposal text.

### Manual path

1. Click `Run Demo` for the bundled matter or upload your own PDF, DOCX, or TXT documents.
2. Upload the original and revised contracts.
3. Upload optional playbook, precedent, and fallback clause documents.
4. Pick a persona such as `Aggressive Procurement`.
5. Run `Run manual analysis`.
6. Review clause-level summaries, evidence hits, counterproposals, and friction scores.

## API Surface

Implemented REST endpoints:

- `GET /api/health`
- `POST /api/demo/happy-path`
- `POST /api/documents/original`
- `POST /api/documents/revised`
- `POST /api/documents/evidence`
- `GET /api/personas`
- `POST /api/runs`
- `GET /api/runs/{run_id}/status`
- `GET /api/runs/{run_id}/summary`
- `GET /api/runs/{run_id}/clauses`
- `GET /api/runs/{run_id}/clauses/{clause_change_id}/evidence`

See [docs/api.md](docs/api.md) for details.

## Demo Assets

Included sample content:

- original contract
- revised contract
- customer playbook
- vendor precedent
- fallback clauses
- three built-in personas
- a committed happy-path example payload

Locations:

- [packages/sample-data/contracts/original_msa.txt](packages/sample-data/contracts/original_msa.txt)
- [packages/sample-data/contracts/revised_msa.txt](packages/sample-data/contracts/revised_msa.txt)
- [packages/sample-data/contracts/original_contract.md](packages/sample-data/contracts/original_contract.md)
- [packages/sample-data/contracts/revised_contract.md](packages/sample-data/contracts/revised_contract.md)
- [packages/personas/builtin_personas.json](packages/personas/builtin_personas.json)
- [packages/sample-data/example-run/happy_path.json](packages/sample-data/example-run/happy_path.json)

## Testing

Backend tests are in `apps/api/tests` and cover:

- parsing
- clause diffing and issue classification
- simulation + critique + scoring flow

Frontend includes a minimal presenter test for display logic.

## Demo Notes

- `Run Demo` in the web app executes a fully local deterministic workflow with bundled sample contracts and mock evidence.
- The local demo path requires no API keys, no uploads, and no backend process.
- `docker compose up --build` waits for API health before starting the web container.
- `POST /api/demo/happy-path` provides a one-call sample matter bootstrap path.
- `make api-demo` runs the sample flow from the CLI and writes a result artifact to `packages/sample-data/example-run/happy_path.json`.

## Screenshots

Placeholder notes:

- add an overview dashboard screenshot
- add a clause review screenshot with evidence panel expanded
- add a persona selector screenshot

## Future Improvements

- DOCX redline reconciliation with tracked changes import
- richer clause matching across reordered sections
- authenticated workspaces and multi-matter support
- human review queues and approval audit logs
- explicit reranker model support
- benchmark corpora and more granular negotiation analytics
- stronger frontend test coverage and end-to-end browser tests

## Documentation

- [Architecture](docs/architecture.md)
- [Data Model](docs/data-model.md)
- [API](docs/api.md)
- [Prompting](docs/prompting.md)
