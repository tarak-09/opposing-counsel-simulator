# API

Base path: `/api`

## Health

### `GET /health`

Returns:

```json
{
  "status": "ok",
  "service": "opposing-counsel-simulator-api"
}
```

## Demo

### `POST /demo/happy-path`

Seeds the bundled sample documents and personas if needed, creates a sample run, and by default executes it synchronously.

Request body:

```json
{
  "persona_slug": "big-tech-legal",
  "run_async": false
}
```

Response includes:

- `message`
- `task_mode`
- `persona`
- `original_document_version`
- `revised_document_version`
- `evidence_document_versions`
- `run`
- `overview`

## Document Uploads

All upload endpoints accept multipart form data.

Shared fields:

- `name` optional
- `text_content` optional
- `file` optional

At least one of `text_content` or `file` must be provided.
Files larger than the configured upload limit are rejected.

### `POST /documents/original`

Creates an original contract document.

### `POST /documents/revised`

Creates a revised contract document.

### `POST /documents/evidence`

Creates an evidence document and indexes snippets for retrieval.

Extra field:

- `evidence_type`: `playbook | precedent | fallback | benchmark`

The evidence route intentionally rejects `contract` as an evidence type.

Response includes:

- `document`
- `version`
- `clauses`
- `evidence_sources`

## Personas

### `GET /personas`

Returns the active built-in personas and any future custom personas.

## Runs

### `POST /runs`

Request body:

```json
{
  "original_document_version_id": "uuid",
  "revised_document_version_id": "uuid",
  "persona_id": "uuid",
  "evidence_document_version_ids": ["uuid"],
  "run_async": true
}
```

Response:

- `run`
- `task_mode` (`async` or `sync`)

The endpoint validates that:

- the original document version came from an original contract upload
- the revised document version came from a revised contract upload
- evidence ids refer only to evidence document versions

### `GET /runs/{run_id}/status`

Returns current stage and status.

### `GET /runs/{run_id}/summary`

Returns:

- `run`
- `persona`
- `overview`

Overview fields currently include:

- `total_changed_clauses`
- `likely_pushback_count`
- `high_friction_clauses`
- `overall_negotiation_difficulty`

### `GET /runs/{run_id}/clauses`

Returns clause-by-clause review objects containing:

- `clause_change`
- `original_clause`
- `revised_clause`
- `simulation_result`
- `scoring_result`
- `retrieval_hits`

### `GET /runs/{run_id}/clauses/{clause_change_id}/evidence`

Returns persisted evidence hits for that clause change.

## Error Model

FastAPI default error format is used:

```json
{
  "detail": "message"
}
```

## Notes

- Upload and run responses are fully typed with Pydantic on the backend and validated with Zod on the frontend.
- Simulation outputs are product prototype guidance, not legal advice.
