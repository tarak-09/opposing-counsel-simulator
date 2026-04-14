import { z } from "zod";

export const personaSchema = z.object({
  id: z.string().uuid(),
  created_at: z.string(),
  updated_at: z.string(),
  slug: z.string(),
  name: z.string(),
  description: z.string(),
  risk_tolerance: z.number(),
  leverage: z.number(),
  speed_priority: z.number(),
  privacy_sensitivity: z.number(),
  liability_strictness: z.number(),
  fallback_flexibility: z.number(),
  tone: z.string(),
  issue_positions: z.record(z.any()),
  is_builtin: z.boolean(),
  is_active: z.boolean(),
});

export const documentSchema = z.object({
  id: z.string().uuid(),
  created_at: z.string(),
  updated_at: z.string(),
  name: z.string(),
  role: z.string(),
  document_type: z.string(),
  source_kind: z.string(),
  status: z.string(),
  metadata_json: z.record(z.any()),
});

export const documentVersionSchema = z.object({
  id: z.string().uuid(),
  created_at: z.string(),
  updated_at: z.string(),
  document_id: z.string().uuid(),
  version_number: z.number(),
  filename: z.string().nullable(),
  mime_type: z.string().nullable(),
  storage_path: z.string().nullable(),
  checksum: z.string().nullable(),
  extracted_text: z.string(),
  normalized_text: z.string(),
  section_map: z.array(z.record(z.any())),
  parser_status: z.string(),
  is_active: z.boolean(),
});

export const clauseSchema = z.object({
  id: z.string().uuid(),
  created_at: z.string(),
  updated_at: z.string(),
  document_version_id: z.string().uuid(),
  stable_clause_id: z.string(),
  heading: z.string(),
  heading_path: z.string(),
  clause_number: z.string(),
  order_index: z.number(),
  text: z.string(),
  normalized_text: z.string(),
  source_span: z.record(z.any()),
});

export const evidenceSourceSchema = z.object({
  id: z.string().uuid(),
  created_at: z.string(),
  updated_at: z.string(),
  document_version_id: z.string().uuid(),
  evidence_type: z.string(),
  title: z.string(),
  section_label: z.string(),
  snippet_text: z.string(),
  full_text: z.string(),
  token_count: z.number(),
  metadata_json: z.record(z.any()),
  vector_id: z.string().nullable(),
});

export const uploadDocumentResponseSchema = z.object({
  document: documentSchema,
  version: documentVersionSchema,
  clauses: z.array(clauseSchema),
  evidence_sources: z.array(evidenceSourceSchema),
});

export const runSchema = z.object({
  id: z.string().uuid(),
  created_at: z.string(),
  updated_at: z.string(),
  original_document_version_id: z.string().uuid(),
  revised_document_version_id: z.string().uuid(),
  persona_id: z.string().uuid(),
  status: z.string(),
  stage: z.string(),
  error_message: z.string().nullable(),
  input_snapshot: z.record(z.any()),
  summary_json: z.record(z.any()),
  total_changed_clauses: z.number(),
  started_at: z.string().nullable(),
  completed_at: z.string().nullable(),
});

export const simulationResultSchema = z.object({
  id: z.string().uuid(),
  created_at: z.string(),
  updated_at: z.string(),
  negotiation_run_id: z.string().uuid(),
  clause_change_id: z.string().uuid(),
  decision: z.string(),
  stance_strength: z.number(),
  business_reason: z.string(),
  legal_reason: z.string(),
  pushback_points: z.array(z.string()),
  counterproposal_text: z.string(),
  strategy: z.string(),
  confidence: z.number(),
  critique_status: z.string(),
  grounded_evidence_count: z.number(),
  raw_model_output: z.record(z.any()),
});

export const scoringResultSchema = z.object({
  id: z.string().uuid(),
  created_at: z.string(),
  updated_at: z.string(),
  negotiation_run_id: z.string().uuid(),
  clause_change_id: z.string().uuid(),
  pushback_probability: z.number(),
  negotiation_friction: z.number(),
  delay_risk: z.number(),
  severity: z.number(),
  friction_label: z.string(),
  explanation: z.string(),
  heuristic_details: z.record(z.any()),
});

export const clauseChangeSchema = z.object({
  id: z.string().uuid(),
  created_at: z.string(),
  updated_at: z.string(),
  negotiation_run_id: z.string().uuid(),
  original_clause_id: z.string().uuid().nullable(),
  revised_clause_id: z.string().uuid().nullable(),
  clause_key: z.string(),
  change_type: z.string(),
  issue_type: z.string(),
  change_direction: z.string(),
  semantic_summary: z.string(),
  diff_details: z.record(z.any()),
  changed_tokens_count: z.number(),
  status: z.string(),
});

export const retrievalHitSchema = z.object({
  id: z.string().uuid(),
  created_at: z.string(),
  updated_at: z.string(),
  negotiation_run_id: z.string().uuid(),
  clause_change_id: z.string().uuid(),
  evidence_source_id: z.string().uuid(),
  rank: z.number(),
  vector_score: z.number(),
  lexical_score: z.number(),
  rerank_score: z.number(),
  snippet_text: z.string(),
  metadata_json: z.record(z.any()),
  evidence_source: evidenceSourceSchema,
});

export const clauseReviewResultSchema = z.object({
  clause_change: clauseChangeSchema,
  original_clause: clauseSchema.nullable(),
  revised_clause: clauseSchema.nullable(),
  simulation_result: simulationResultSchema.nullable(),
  scoring_result: scoringResultSchema.nullable(),
  retrieval_hits: z.array(retrievalHitSchema),
});

export const runAcceptedResponseSchema = z.object({
  run: runSchema,
  task_mode: z.enum(["async", "sync"]),
});

export const runStatusResponseSchema = z.object({
  run: runSchema,
});

export const runOverviewSchema = z.object({
  total_changed_clauses: z.number(),
  likely_pushback_count: z.number(),
  high_friction_clauses: z.number(),
  overall_negotiation_difficulty: z.number(),
});

export const runSummaryResponseSchema = z.object({
  run: runSchema,
  persona: personaSchema,
  overview: runOverviewSchema,
});

export const clauseResultsResponseSchema = z.object({
  run: runSchema,
  results: z.array(clauseReviewResultSchema),
});

export const evidenceForClauseResponseSchema = z.object({
  clause_change_id: z.string().uuid(),
  hits: z.array(retrievalHitSchema),
});

export const demoHappyPathResponseSchema = z.object({
  message: z.string(),
  task_mode: z.enum(["async", "sync"]),
  persona: personaSchema,
  original_document_version: documentVersionSchema,
  revised_document_version: documentVersionSchema,
  evidence_document_versions: z.array(documentVersionSchema),
  run: runSchema,
  overview: runOverviewSchema,
});

export type Persona = z.infer<typeof personaSchema>;
export type Document = z.infer<typeof documentSchema>;
export type DocumentVersion = z.infer<typeof documentVersionSchema>;
export type Clause = z.infer<typeof clauseSchema>;
export type EvidenceSource = z.infer<typeof evidenceSourceSchema>;
export type Run = z.infer<typeof runSchema>;
export type SimulationResult = z.infer<typeof simulationResultSchema>;
export type ScoringResult = z.infer<typeof scoringResultSchema>;
export type ClauseChange = z.infer<typeof clauseChangeSchema>;
export type RetrievalHit = z.infer<typeof retrievalHitSchema>;
export type ClauseReviewResult = z.infer<typeof clauseReviewResultSchema>;
export type UploadDocumentResponse = z.infer<typeof uploadDocumentResponseSchema>;
export type RunAcceptedResponse = z.infer<typeof runAcceptedResponseSchema>;
export type RunStatusResponse = z.infer<typeof runStatusResponseSchema>;
export type RunSummaryResponse = z.infer<typeof runSummaryResponseSchema>;
export type ClauseResultsResponse = z.infer<typeof clauseResultsResponseSchema>;
export type DemoHappyPathResponse = z.infer<typeof demoHappyPathResponseSchema>;
export type RunOverview = z.infer<typeof runOverviewSchema>;
