# Data Model

## Tables

### `documents`

Logical document record.

- `id`
- `name`
- `role` (`original`, `revised`, `evidence`)
- `document_type` (`contract`, `playbook`, `precedent`, `fallback`, `benchmark`)
- `source_kind` (`file`, `text`)
- `status`
- `metadata_json`
- timestamps

### `document_versions`

Stored version of a document with extracted and normalized text.

- `id`
- `document_id`
- `version_number`
- `filename`
- `mime_type`
- `storage_path`
- `checksum`
- `raw_text_input`
- `extracted_text`
- `normalized_text`
- `section_map`
- `parser_status`
- `is_active`
- timestamps

### `clauses`

Normalized clause records derived from a `document_version`.

- `id`
- `document_version_id`
- `stable_clause_id`
- `heading`
- `heading_path`
- `clause_number`
- `order_index`
- `text`
- `normalized_text`
- `source_span`
- timestamps

### `personas`

Structured negotiating personas.

- `id`
- `slug`
- `name`
- `description`
- `risk_tolerance`
- `leverage`
- `speed_priority`
- `privacy_sensitivity`
- `liability_strictness`
- `fallback_flexibility`
- `tone`
- `issue_positions`
- `is_builtin`
- `is_active`
- timestamps

### `negotiation_runs`

One analysis run over a contract pair and persona.

- `id`
- `original_document_version_id`
- `revised_document_version_id`
- `persona_id`
- `status`
- `stage`
- `error_message`
- `input_snapshot`
- `summary_json`
- `total_changed_clauses`
- `started_at`
- `completed_at`
- timestamps

### `clause_changes`

Changed clause records within a run.

- `id`
- `negotiation_run_id`
- `original_clause_id`
- `revised_clause_id`
- `clause_key`
- `change_type`
- `issue_type`
- `change_direction`
- `semantic_summary`
- `diff_details`
- `changed_tokens_count`
- `status`
- timestamps

### `evidence_sources`

Indexed snippets derived from evidence documents.

- `id`
- `document_version_id`
- `evidence_type`
- `title`
- `section_label`
- `snippet_text`
- `full_text`
- `token_count`
- `metadata_json`
- `vector_id`
- timestamps

### `retrieval_hits`

Per-clause evidence hits persisted for inspectability.

- `id`
- `negotiation_run_id`
- `clause_change_id`
- `evidence_source_id`
- `rank`
- `vector_score`
- `lexical_score`
- `rerank_score`
- `snippet_text`
- `metadata_json`
- timestamps

### `simulation_results`

Structured opposing-counsel output for a clause.

- `id`
- `negotiation_run_id`
- `clause_change_id`
- `decision`
- `stance_strength`
- `business_reason`
- `legal_reason`
- `pushback_points`
- `counterproposal_text`
- `strategy`
- `confidence`
- `critique_status`
- `grounded_evidence_count`
- `raw_model_output`
- timestamps

### `scoring_results`

Transparent heuristic scoring output for a clause.

- `id`
- `negotiation_run_id`
- `clause_change_id`
- `pushback_probability`
- `negotiation_friction`
- `delay_risk`
- `severity`
- `friction_label`
- `explanation`
- `heuristic_details`
- timestamps

## Relationships

- `documents 1 -> many document_versions`
- `document_versions 1 -> many clauses`
- `document_versions 1 -> many evidence_sources`
- `personas 1 -> many negotiation_runs`
- `negotiation_runs 1 -> many clause_changes`
- `clause_changes 1 -> many retrieval_hits`
- `clause_changes 1 -> 1 simulation_results`
- `clause_changes 1 -> 1 scoring_results`

## Migration

Initial schema lives at:

- [apps/api/alembic/versions/20260413_0001_initial_schema.py](../apps/api/alembic/versions/20260413_0001_initial_schema.py)
