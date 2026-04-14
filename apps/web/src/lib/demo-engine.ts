/**
 * Local demo engine — no backend, no API keys required.
 *
 * The demo contracts are fixed strings, so all parsing, diffing, and
 * classification is pre-baked here as static data. Only simulation and
 * scoring are computed at runtime because they depend on the selected persona.
 */
import type {
  ClauseChange,
  ClauseResultsResponse,
  ClauseReviewResult,
  EvidenceSource,
  Persona,
  RetrievalHit,
  Run,
  RunOverview,
  RunStatusResponse,
  RunSummaryResponse,
  ScoringResult,
  SimulationResult,
} from "@ocs/schemas";

import {
  demoDefaultPersonaSlug,
  demoFallback,
  demoMatterName,
  demoOriginalContract,
  demoPersonas,
  demoPlaybook,
  demoPrecedent,
  demoRevisedContract,
} from "@/lib/demo-data";

export type DemoRunBundle = {
  message: string;
  matterName: string;
  persona: Persona;
  originalContract: string;
  revisedContract: string;
  evidenceDocuments: Array<{ id: string; label: string; type: string; title: string; text: string; uploadedVersionId: string }>;
  runStatus: RunStatusResponse;
  runSummary: RunSummaryResponse;
  clauseResults: ClauseResultsResponse;
};

type IssueType = "payment_terms" | "confidentiality" | "limitation_of_liability" | "indemnity" | "termination";

// ─── Static IDs ─────────────────────────────────────────────────────────────

const TS = "2026-04-13T12:00:00.000Z";
const RUN_ID = "4af6ee07-ed2b-4cff-8665-7ff876143c71";
const DOC = {
  original: "7a7f67e6-dcc0-4937-8cac-3f117f0ce675",
  revised:  "119f2f50-e8e1-4d4c-88e3-e4a9ebc4f2c7",
  playbook: "dc37614b-1fd0-44eb-8c0c-58df88865db3",
  precedent:"df7fe66d-ac77-410f-b2e8-c4f3244ddf57",
  fallback: "25daa6ac-0b3e-4b63-ba81-a3a335404a58",
} as const;

// ─── Pre-baked clause data ───────────────────────────────────────────────────
// Clause text is fixed — no runtime parsing needed.

type ClauseSpec = {
  clauseNumber: string;
  heading: string;
  originalText: string;
  revisedText: string;
  summary: string;
};

const CLAUSES: Record<IssueType, ClauseSpec> = {
  payment_terms: {
    clauseNumber: "1",
    heading: "Payment Terms",
    originalText: "1. Payment Terms. Customer will pay undisputed invoices within thirty (30) days after receipt. Vendor may suspend access to the Services if an undisputed invoice remains unpaid for more than fifteen (15) days after written notice.",
    revisedText: "1. Payment Terms. Customer will pay undisputed invoices within forty-five (45) days after receipt. Customer may withhold any disputed amount until the parties resolve the dispute in good faith. Vendor may not suspend the Services unless an undisputed invoice remains unpaid for more than forty-five (45) days after written notice to Customer's finance contact.",
    summary: "Payment timing moved from net 30 to net 45, added a broad invoice withholding right, and delayed suspension remedies.",
  },
  confidentiality: {
    clauseNumber: "2",
    heading: "Confidentiality",
    originalText: "2. Confidentiality. Each party will protect the other party's Confidential Information using at least reasonable care and will not disclose such information except to its employees, contractors, and advisors who have a need to know and are bound by written confidentiality obligations. Confidentiality obligations survive for three (3) years after termination, except for trade secrets, which remain protected for so long as they qualify as trade secrets under applicable law.",
    revisedText: "2. Confidentiality. Each party will protect the other party's Confidential Information using no less than industry-standard safeguards and will not disclose such information except to personnel with a strict need to know. Vendor may not use Customer Confidential Information for analytics, benchmarking, or model training without Customer's prior written consent. Confidentiality obligations survive for five (5) years after termination, and Customer may seek injunctive relief for any threatened or actual unauthorized use or disclosure.",
    summary: "Confidentiality obligations were tightened, analytics use was prohibited, survival was extended to five years, and Customer added explicit injunctive relief.",
  },
  limitation_of_liability: {
    clauseNumber: "3",
    heading: "Limitation of Liability",
    originalText: "3. Limitation of Liability. Except for fraud, willful misconduct, or a party's breach of Section 2 (Confidentiality), each party's aggregate liability arising out of or related to this Agreement will not exceed the fees paid or payable by Customer under this Agreement during the twelve (12) months preceding the event giving rise to the claim. Neither party will be liable for any indirect, incidental, special, or consequential damages.",
    revisedText: "3. Limitation of Liability. Except for Customer's payment obligations, each party's aggregate liability arising out of or related to this Agreement will not exceed two (2) times the fees paid or payable by Customer under this Agreement during the twelve (12) months preceding the event giving rise to the claim. The foregoing cap will not apply to breaches of confidentiality, data security incidents, privacy violations, indemnity obligations, gross negligence, or willful misconduct. Neither party will be liable for any indirect, incidental, special, or consequential damages.",
    summary: "The general liability cap moved from 12 months of fees to 24 months and added broad carve-outs for confidentiality, privacy, security, indemnity, and gross negligence.",
  },
  indemnity: {
    clauseNumber: "4",
    heading: "Indemnity",
    originalText: "4. Indemnity. Vendor will defend Customer against any third-party claim alleging that the Services infringe that third party's intellectual property rights, and Vendor will indemnify Customer against any damages, costs, and reasonable attorneys' fees finally awarded by a court or agreed in settlement by Vendor. Customer will promptly notify Vendor of the claim and provide reasonable cooperation.",
    revisedText: "4. Indemnity. Vendor will defend, indemnify, and hold harmless Customer, its affiliates, and their respective officers, directors, employees, and contractors from and against any third-party claim, demand, investigation, or proceeding arising from or relating to (a) alleged infringement or misappropriation by the Services, (b) Vendor's breach of confidentiality obligations, (c) any security incident or violation of data protection law attributable to Vendor, or (d) bodily injury, death, or tangible property damage caused by Vendor. Vendor's indemnity obligations will be in addition to, and not limited by, any limitation of liability in this Agreement.",
    summary: "Indemnity expanded beyond IP claims to cover confidentiality, security, privacy, bodily injury, and property damage, and was made uncapped.",
  },
  termination: {
    clauseNumber: "5",
    heading: "Term and Termination",
    originalText: "5. Term and Termination. The initial subscription term is twelve (12) months and will automatically renew for successive one-year terms unless either party gives at least thirty (30) days' notice of non-renewal before the end of the then-current term. Either party may terminate this Agreement for material breach if the breach remains uncured for thirty (30) days after written notice.",
    revisedText: "5. Term and Termination. The initial subscription term is twelve (12) months and will automatically renew for successive one-year terms unless either party gives at least sixty (60) days' notice of non-renewal before the end of the then-current term. Customer may terminate this Agreement for convenience on thirty (30) days' written notice after the first ninety (90) days of the initial term. Either party may terminate this Agreement for material breach if the breach remains uncured for fifteen (15) days after written notice. Upon any expiration or termination, Vendor will provide transition assistance for up to sixty (60) days at no additional charge.",
    summary: "Customer added convenience termination, shortened the breach cure period, lengthened the non-renewal notice period, and required free transition support.",
  },
};

// ─── Pre-baked evidence per issue type ──────────────────────────────────────

const EVIDENCE: Record<IssueType, Array<{ id: string; docVersionId: keyof typeof DOC; type: "playbook" | "precedent" | "fallback"; title: string; section: string; snippet: string }>> = {
  payment_terms: [
    { id: "fd26831e-f895-4ea5-9e6d-2a321029dc9a", docVersionId: "playbook",  type: "playbook",  title: "Negotiation Playbook",     section: "Payment Terms",      snippet: "Net 30 for undisputed invoices is standard." },
    { id: "c38ff278-eb15-4fe0-8b17-e9584b03c676", docVersionId: "precedent", type: "precedent", title: "Vendor Precedent Notes",    section: "Payment Benchmark",  snippet: "Suspension rights typically require written notice and only apply to undisputed overdue amounts." },
  ],
  confidentiality: [
    { id: "4494dc0f-b14f-40f6-b9b4-cde518fd8605", docVersionId: "playbook",  type: "playbook",  title: "Negotiation Playbook",     section: "Confidentiality",          snippet: "Permit use of de-identified service data for analytics and do not accept blanket bans on internal service improvement." },
    { id: "2a4f8d55-4883-4769-a2d1-584cf9e9c817", docVersionId: "precedent", type: "precedent", title: "Vendor Precedent Notes",    section: "Confidentiality Benchmark", snippet: "Analytics use is generally acceptable if the data is aggregated and de-identified." },
  ],
  limitation_of_liability: [
    { id: "04150976-f208-4795-b9b5-a098d29b5341", docVersionId: "playbook",  type: "playbook",  title: "Negotiation Playbook",     section: "Liability",          snippet: "Standard liability is 6-12 months of fees." },
    { id: "17eafe9d-c8dc-4e80-8960-73e6a28d8de8", docVersionId: "precedent", type: "precedent", title: "Vendor Precedent Notes",    section: "Liability Benchmark", snippet: "Vendor-friendly SaaS paper commonly caps liability at fees paid in the prior 12 months." },
  ],
  indemnity: [
    { id: "9935b228-4e4a-4c36-b19b-bb5d54aee35b", docVersionId: "playbook",  type: "playbook",  title: "Negotiation Playbook",     section: "Indemnity",               snippet: "Indemnity should be mutual for SaaS contracts." },
    { id: "95f51e03-15b7-4da8-b673-278ce3e343f7", docVersionId: "fallback",  type: "fallback",  title: "Approved Fallback Clauses", section: "Mutual Indemnity Fallback", snippet: "Indemnity obligations should remain tied to third-party claims and proportionate to the risk controlled by the indemnifying party." },
  ],
  termination: [
    { id: "d0cb4f7a-b7f5-43ed-ba51-8b4f14f4563b", docVersionId: "playbook",  type: "playbook",  title: "Negotiation Playbook",     section: "Termination",          snippet: "Avoid customer termination for convenience during the committed subscription term unless stranded implementation costs are recovered." },
    { id: "9377e8b7-d010-40e6-b0ec-ffdfaf19a16d", docVersionId: "fallback",  type: "fallback",  title: "Approved Fallback Clauses", section: "Termination Fallback",  snippet: "Either party may terminate for material breach if the breach remains uncured for thirty (30) days after written notice." },
  ],
};

const BASE_SCORES: Record<IssueType, { pushback: number; friction: number; delay: number; severity: number }> = {
  payment_terms:           { pushback: 0.61, friction: 0.54, delay: 0.44, severity: 0.52 },
  confidentiality:         { pushback: 0.66, friction: 0.59, delay: 0.48, severity: 0.60 },
  limitation_of_liability: { pushback: 0.89, friction: 0.90, delay: 0.75, severity: 0.94 },
  indemnity:               { pushback: 0.84, friction: 0.83, delay: 0.70, severity: 0.89 },
  termination:             { pushback: 0.74, friction: 0.72, delay: 0.64, severity: 0.77 },
};

const COUNTERPROPOSALS: Record<IssueType, { vendorSide: string; customerSide: string }> = {
  payment_terms: {
    vendorSide:   "Invoices are due within thirty (30) days after receipt, Customer may withhold only specifically disputed amounts, and suspension applies only to undisputed overdue amounts after written notice.",
    customerSide: "Customer may withhold only the specifically disputed portion of an invoice, and undisputed invoices remain due within forty-five (45) days after receipt.",
  },
  confidentiality: {
    vendorSide:   "Confidentiality obligations survive for three (3) years after termination, and Vendor may use aggregated, de-identified service data for internal analytics and product improvement.",
    customerSide: "Vendor may use de-identified service data for internal analytics and service improvement, but not for model training or external benchmarking without Customer approval.",
  },
  limitation_of_liability: {
    vendorSide:   "Except for fraud, willful misconduct, and third-party IP indemnity obligations, each party's aggregate liability will not exceed the fees paid or payable in the twelve (12) months preceding the claim, with any confidentiality or data protection carve-out subject to a separate super-cap.",
    customerSide: "Each party's aggregate liability will be capped at two (2) times the fees paid or payable in the preceding twelve (12) months, with targeted carve-outs for confidentiality, data protection, indemnity obligations, fraud, and willful misconduct.",
  },
  indemnity: {
    vendorSide:   "Indemnity will remain limited to third-party claims and mutual where each party controls the relevant risk. Vendor covers IP infringement; data and confidentiality obligations remain subject to negotiated fault-based remedies.",
    customerSide: "Vendor will indemnify Customer for IP infringement, confidentiality breaches, and Vendor-caused data protection claims, while the parties remain open to mutual indemnity for risks each party controls.",
  },
  termination: {
    vendorSide:   "Either party may terminate for material breach if the breach remains uncured for thirty (30) days after written notice. Customer convenience termination during the initial term requires at least sixty (60) days' notice and payment of committed fees through the termination date.",
    customerSide: "Customer may terminate for convenience on sixty (60) days' notice after go-live, and Vendor will provide commercially reasonable transition assistance at standard rates unless termination is caused by Vendor breach.",
  },
};

// ─── Builder helpers ─────────────────────────────────────────────────────────

function id(seed: string): string {
  const n = Array.from(seed).reduce((t, c, i) => t + c.charCodeAt(0) * (i + 17), 0);
  return `00000000-0000-4000-8000-${n.toString(16).padStart(12, "0").slice(0, 12)}`;
}

function clamp(v: number) { return Math.max(0.12, Math.min(0.96, v)); }
function r2(v: number)    { return Number(v.toFixed(2)); }

function frictionLabel(v: number): "low" | "medium" | "high" {
  return v >= 0.75 ? "high" : v >= 0.55 ? "medium" : "low";
}

function buildHits(runId: string, issueType: IssueType, changeId: string): RetrievalHit[] {
  const fullTextByDoc: Record<keyof typeof DOC, string> = {
    original: demoOriginalContract, revised: demoRevisedContract,
    playbook: demoPlaybook, precedent: demoPrecedent, fallback: demoFallback,
  };
  return EVIDENCE[issueType].map((entry, i) => {
    const source: EvidenceSource = {
      id: entry.id, created_at: TS, updated_at: TS,
      document_version_id: DOC[entry.docVersionId],
      evidence_type: entry.type, title: entry.title,
      section_label: entry.section, snippet_text: entry.snippet,
      full_text: fullTextByDoc[entry.docVersionId],
      token_count: entry.snippet.split(" ").length,
      metadata_json: { local_demo: true, issue_type: issueType },
      vector_id: null,
    };
    return {
      id: id(`hit-${issueType}-${i}`), created_at: TS, updated_at: TS,
      negotiation_run_id: runId, clause_change_id: changeId,
      evidence_source_id: source.id, rank: i + 1,
      vector_score: r2(0.81 - i * 0.06), lexical_score: r2(0.78 - i * 0.05),
      rerank_score: r2(0.84 - i * 0.04), snippet_text: entry.snippet,
      metadata_json: { local_demo: true },
      evidence_source: source,
    };
  });
}

function buildSimulation(runId: string, issueType: IssueType, changeId: string, persona: Persona, hits: RetrievalHit[]): SimulationResult {
  const vendorSide = persona.slug === "startup-counsel";
  const label = CLAUSES[issueType].heading.toLowerCase();
  const evidence = hits[0]?.snippet_text ?? "Fallback guidance supports a balanced vendor position.";
  const cp = vendorSide ? COUNTERPROPOSALS[issueType].vendorSide : COUNTERPROPOSALS[issueType].customerSide;

  const decision = ((): SimulationResult["decision"] => {
    if (vendorSide) {
      if (issueType === "limitation_of_liability") return "escalate";
      if (issueType === "termination") return "push_back";
      return "counter";
    }
    if (issueType === "payment_terms" || issueType === "confidentiality") return "accept";
    return "counter";
  })();

  return {
    id: id(`sim-${issueType}`), created_at: TS, updated_at: TS,
    negotiation_run_id: runId, clause_change_id: changeId,
    decision,
    stance_strength: vendorSide ? 0.86 : 0.66,
    business_reason: vendorSide
      ? `${persona.name} sees the revised ${label} language as materially shifting commercial and balance-sheet risk onto the vendor beyond what is usually acceptable for a growth-stage SaaS company.`
      : `${persona.name} views the revised ${label} language as directionally aligned with enterprise risk controls, but still wants tighter drafting where the operational obligation is too open-ended.`,
    legal_reason: vendorSide
      ? `The redline overreaches relative to SaaS market norms and should be moved back toward a balanced fallback. ${evidence}`
      : `The redline is broadly supportable, but the clause should still be tied back to market guardrails and clearer drafting. ${evidence}`,
    pushback_points: vendorSide
      ? [`The current edit changes risk allocation beyond ${persona.name}'s default posture.`, `A narrower fallback is available and should be proposed instead of accepting the full redline.`]
      : [`The change is directionally supportable but needs tighter drafting.`, `Playbook and precedent evidence supports a narrower fallback.`],
    counterproposal_text: cp,
    strategy: vendorSide
      ? "Acknowledge the business ask, rely on precedent, and move quickly to a balanced fallback that still protects execution risk."
      : "Preserve the customer-friendly direction while narrowing ambiguities that could slow review.",
    confidence: vendorSide ? 0.84 : 0.78,
    critique_status: "passed",
    grounded_evidence_count: hits.length,
    raw_model_output: { mode: "local_demo", issue_type: issueType },
  };
}

function buildScoring(runId: string, issueType: IssueType, changeId: string, persona: Persona, sim: SimulationResult): ScoringResult {
  const base = BASE_SCORES[issueType];
  const la = (persona.leverage - 3) * 0.025;
  const sa = (persona.liability_strictness - 3) * 0.035;
  const sp = (persona.speed_priority - 3) * -0.02;
  const oa = persona.slug === "startup-counsel" ? 0.04 : -0.02;

  const friction = clamp(base.friction + sa + sp);
  return {
    id: id(`score-${issueType}`), created_at: TS, updated_at: TS,
    negotiation_run_id: runId, clause_change_id: changeId,
    pushback_probability: r2(clamp(base.pushback + la + sa + oa)),
    negotiation_friction: r2(friction),
    delay_risk: r2(clamp(base.delay + la + sp / 2)),
    severity: r2(clamp(base.severity + sa / 2 + oa / 2)),
    friction_label: frictionLabel(friction),
    explanation: sim.decision === "accept"
      ? "The selected persona is generally aligned with the revised clause, so the expected friction is modest."
      : "This clause changes core economic or risk-allocation terms, so it is likely to draw structured pushback and require fallback drafting.",
    heuristic_details: { issue_type: issueType, persona_slug: persona.slug, local_demo: true },
  };
}

// ─── Main export ─────────────────────────────────────────────────────────────

export async function runDemo(options?: { personaSlug?: string }): Promise<DemoRunBundle> {
  const persona = demoPersonas.find((p) => p.slug === (options?.personaSlug ?? demoDefaultPersonaSlug)) ?? demoPersonas[2];

  const results: ClauseReviewResult[] = (Object.keys(CLAUSES) as IssueType[]).map((issueType) => {
    const spec = CLAUSES[issueType];
    const changeId = id(`change-${issueType}`);
    const hits = buildHits(RUN_ID, issueType, changeId);
    const sim = buildSimulation(RUN_ID, issueType, changeId, persona, hits);
    const score = buildScoring(RUN_ID, issueType, changeId, persona, sim);

    const clauseChange: ClauseChange = {
      id: changeId, created_at: TS, updated_at: TS,
      negotiation_run_id: RUN_ID,
      original_clause_id: id(`orig-${issueType}`),
      revised_clause_id: id(`rev-${issueType}`),
      clause_key: `clause-${spec.clauseNumber}`,
      change_type: "modified", issue_type: issueType,
      change_direction: "customer_favorable",
      semantic_summary: spec.summary,
      diff_details: { original_excerpt: spec.originalText, revised_excerpt: spec.revisedText, heading: spec.heading },
      changed_tokens_count: Math.abs(spec.revisedText.split(" ").length - spec.originalText.split(" ").length) + 18,
      status: "completed",
    };

    return {
      clause_change: clauseChange,
      original_clause: { id: id(`orig-${issueType}`), created_at: TS, updated_at: TS, document_version_id: DOC.original, stable_clause_id: `clause-${spec.clauseNumber}`, heading: spec.heading, heading_path: `${spec.clauseNumber}. ${spec.heading}`, clause_number: spec.clauseNumber, order_index: Number(spec.clauseNumber) - 1, text: spec.originalText, normalized_text: spec.originalText.toLowerCase(), source_span: { start_line: 1, end_line: 3 } },
      revised_clause:  { id: id(`rev-${issueType}`),  created_at: TS, updated_at: TS, document_version_id: DOC.revised,   stable_clause_id: `clause-${spec.clauseNumber}`, heading: spec.heading, heading_path: `${spec.clauseNumber}. ${spec.heading}`, clause_number: spec.clauseNumber, order_index: Number(spec.clauseNumber) - 1, text: spec.revisedText,  normalized_text: spec.revisedText.toLowerCase(),  source_span: { start_line: 1, end_line: 3 } },
      simulation_result: sim,
      scoring_result: score,
      retrieval_hits: hits,
    };
  });

  const overview: RunOverview = {
    total_changed_clauses: results.length,
    likely_pushback_count: results.filter((r) => r.simulation_result?.decision !== "accept").length,
    high_friction_clauses: results.filter((r) => r.scoring_result?.friction_label === "high").length,
    overall_negotiation_difficulty: r2(results.reduce((s, r) => s + (r.scoring_result?.severity ?? 0), 0) / results.length),
  };

  const run: Run = {
    id: RUN_ID, created_at: TS, updated_at: TS,
    original_document_version_id: DOC.original, revised_document_version_id: DOC.revised,
    persona_id: persona.id, status: "completed", stage: "completed",
    error_message: null,
    input_snapshot: { mode: "local_demo", evidence_document_version_ids: [DOC.playbook, DOC.precedent, DOC.fallback] },
    summary_json: overview, total_changed_clauses: results.length,
    started_at: TS, completed_at: TS,
  };

  return {
    message: "Demo matter loaded and simulation completed locally.",
    matterName: demoMatterName,
    persona,
    originalContract: demoOriginalContract,
    revisedContract: demoRevisedContract,
    evidenceDocuments: [
      { id: "5f0c6cd3-64a2-4dc8-bc5d-5f87cf30ac1d", label: "Customer Playbook", type: "playbook",  title: "Negotiation Playbook",     text: demoPlaybook,  uploadedVersionId: DOC.playbook  },
      { id: "ca27dd5f-2bc4-4f2b-b718-e18d5b28ec6c", label: "Vendor Precedent",  type: "precedent", title: "Vendor Precedent Notes",    text: demoPrecedent, uploadedVersionId: DOC.precedent },
      { id: "2cf72afd-b8a7-454e-9c16-3690ba55589f", label: "Fallback Clauses",  type: "fallback",  title: "Approved Fallback Clauses", text: demoFallback,  uploadedVersionId: DOC.fallback  },
    ],
    runStatus: { run },
    runSummary: { run, persona, overview },
    clauseResults: { run, results },
  };
}
