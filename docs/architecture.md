# Architecture

## Overview

Opposing Counsel Simulator is split into a typed backend workflow engine and a review-oriented frontend.

Core pipeline:

`ingestion -> parsing -> diffing -> classification -> retrieval -> simulation -> critique -> scoring -> UI`

## Backend Modules

### `services/ingestion.py`

- accepts uploaded files or pasted text
- stores metadata in `documents` and `document_versions`
- extracts text from PDF, DOCX, or TXT
- triggers clause parsing
- creates evidence snippets for playbook / precedent / fallback documents

### `services/parsing.py`

- normalizes line endings and whitespace
- detects headings and section numbers heuristically
- emits stable clause ids, section maps, and source spans

### `services/diffing.py`

- compares parsed clause sets across original and revised versions
- matches clauses by stable id first, then fuzzy similarity
- creates structured change candidates
- optionally uses an LLM adapter for semantic change summaries

### `services/classification.py`

- applies deterministic keyword heuristics first
- falls back to the model adapter only when heuristics are weak
- constrains output to one issue type

### `services/retrieval.py`

- indexes evidence snippets into Qdrant
- computes lexical relevance with BM25
- merges vector and lexical scores into a transparent rerank
- returns inspectable evidence hits with scores and metadata

### `services/simulation.py`

- runs clause by clause
- uses persona policy objects plus retrieved evidence
- can call a structured model adapter or deterministic fallback logic
- emits strict JSON shaped outputs

### `services/critique.py`

- validates persona consistency, rationale quality, and evidence grounding
- repairs weak outputs up to two times
- fails safely with escalation-oriented output

### `services/scoring.py`

- applies transparent heuristics for pushback probability, friction, delay risk, and severity
- explicitly avoids claiming predictive model accuracy

### `services/orchestration.py`

- coordinates the full pipeline for a run
- persists per-stage results
- supports synchronous execution for demo mode and Celery-backed async execution for background mode

### `services/demo.py`

- bootstraps a one-click sample matter
- seeds bundled contracts and evidence on demand
- creates a run against a built-in persona
- powers both the UI demo button and the CLI happy-path script

## Frontend Modules

### `src/components/features/simulator-workbench.tsx`

- matter intake and evidence library
- persona selector and run launcher
- one-click sample matter bootstrap
- overview metrics
- review queue with selected-clause detail
- evidence and scoring side panels

### `src/lib/api.ts`

- typed fetch wrappers
- Zod validation using `packages/schemas`

### `src/lib/hooks/use-run-polling.ts`

- status polling for long-running runs
- stops polling once a run completes or fails

## Persistence

- PostgreSQL stores runs, documents, parsed clauses, evidence metadata, retrieval hits, simulations, and scores.
- Redis backs Celery.
- Qdrant stores dense vectors for evidence snippets.

## Failure Handling

- upload endpoints reject empty inputs
- parsing failures are isolated per document
- retrieval degrades gracefully to lexical only if vector search is unavailable
- simulation is critiqued and repaired before persistence
- orchestration marks failed runs with error text

## Why This Is Not A Toy Chatbot

- the system reasons at clause granularity
- model tasks are separated instead of merged into one prompt
- evidence is persisted and inspectable
- personas are structured policy objects, not plain-English vibes
- scoring is transparent and heuristic rather than fake ML
