import type {
  Clause,
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

type DemoIssueType =
  | "payment_terms"
  | "confidentiality"
  | "limitation_of_liability"
  | "indemnity"
  | "termination";

type DemoSeed = {
  matterName: string;
  originalContract: string;
  revisedContract: string;
  evidenceDocuments: DemoEvidenceDocument[];
  personas: Persona[];
  defaultPersona: Persona;
};

type DemoEvidenceDocument = {
  id: string;
  label: string;
  type: "playbook" | "precedent" | "fallback";
  title: string;
  text: string;
};

type MockEvidenceDefinition = {
  id: string;
  documentVersionId: string;
  evidenceType: "playbook" | "precedent" | "fallback";
  title: string;
  sectionLabel: string;
  snippetText: string;
  fullText: string;
  issueTypes: DemoIssueType[];
};

type ParsedClauseBlock = {
  clauseNumber: string;
  heading: string;
  text: string;
  orderIndex: number;
};

export type DemoRunBundle = {
  message: string;
  matterName: string;
  persona: Persona;
  originalContract: string;
  revisedContract: string;
  evidenceDocuments: Array<DemoEvidenceDocument & { uploadedVersionId: string }>;
  runStatus: RunStatusResponse;
  runSummary: RunSummaryResponse;
  clauseResults: ClauseResultsResponse;
};

const demoTimestamp = "2026-04-13T12:00:00.000Z";
const demoDocumentVersionIds = {
  original: "7a7f67e6-dcc0-4937-8cac-3f117f0ce675",
  revised: "119f2f50-e8e1-4d4c-88e3-e4a9ebc4f2c7",
  playbook: "dc37614b-1fd0-44eb-8c0c-58df88865db3",
  precedent: "df7fe66d-ac77-410f-b2e8-c4f3244ddf57",
  fallback: "25daa6ac-0b3e-4b63-ba81-a3a335404a58",
} as const;

const issueLabels: Record<DemoIssueType, string> = {
  payment_terms: "Payment Terms",
  confidentiality: "Confidentiality",
  limitation_of_liability: "Limitation of Liability",
  indemnity: "Indemnity",
  termination: "Termination",
};

const clauseSummaries: Record<DemoIssueType, string> = {
  payment_terms:
    "Payment timing moved from net 30 to net 45, added a broad invoice withholding right, and delayed suspension remedies.",
  confidentiality:
    "Confidentiality obligations were tightened, analytics use was prohibited, survival was extended to five years, and Customer added explicit injunctive relief.",
  limitation_of_liability:
    "The general liability cap moved from 12 months of fees to 24 months and added broad carve-outs for confidentiality, privacy, security, indemnity, and gross negligence.",
  indemnity:
    "Indemnity expanded beyond IP claims to cover confidentiality, security, privacy, bodily injury, and property damage, and was made uncapped.",
  termination:
    "Customer added convenience termination, shortened the breach cure period, lengthened the non-renewal notice period, and required free transition support.",
};

const directionByIssue: Record<DemoIssueType, string> = {
  payment_terms: "customer_favorable",
  confidentiality: "customer_favorable",
  limitation_of_liability: "customer_favorable",
  indemnity: "customer_favorable",
  termination: "customer_favorable",
};

const baseScoring: Record<
  DemoIssueType,
  {
    pushback: number;
    friction: number;
    delay: number;
    severity: number;
  }
> = {
  payment_terms: { pushback: 0.61, friction: 0.54, delay: 0.44, severity: 0.52 },
  confidentiality: { pushback: 0.66, friction: 0.59, delay: 0.48, severity: 0.6 },
  limitation_of_liability: { pushback: 0.89, friction: 0.9, delay: 0.75, severity: 0.94 },
  indemnity: { pushback: 0.84, friction: 0.83, delay: 0.7, severity: 0.89 },
  termination: { pushback: 0.74, friction: 0.72, delay: 0.64, severity: 0.77 },
};

const evidenceCatalog: MockEvidenceDefinition[] = [
  {
    id: "04150976-f208-4795-b9b5-a098d29b5341",
    documentVersionId: demoDocumentVersionIds.playbook,
    evidenceType: "playbook",
    title: "Negotiation Playbook",
    sectionLabel: "Liability",
    snippetText: "Standard liability is 6-12 months of fees.",
    fullText: demoPlaybook,
    issueTypes: ["limitation_of_liability"],
  },
  {
    id: "17eafe9d-c8dc-4e80-8960-73e6a28d8de8",
    documentVersionId: demoDocumentVersionIds.precedent,
    evidenceType: "precedent",
    title: "Vendor Precedent Notes",
    sectionLabel: "Liability Benchmark",
    snippetText: "Vendor-friendly SaaS paper commonly caps liability at fees paid in the prior 12 months.",
    fullText: demoPrecedent,
    issueTypes: ["limitation_of_liability"],
  },
  {
    id: "9935b228-4e4a-4c36-b19b-bb5d54aee35b",
    documentVersionId: demoDocumentVersionIds.playbook,
    evidenceType: "playbook",
    title: "Negotiation Playbook",
    sectionLabel: "Indemnity",
    snippetText: "Indemnity should be mutual for SaaS contracts.",
    fullText: demoPlaybook,
    issueTypes: ["indemnity"],
  },
  {
    id: "95f51e03-15b7-4da8-b673-278ce3e343f7",
    documentVersionId: demoDocumentVersionIds.fallback,
    evidenceType: "fallback",
    title: "Approved Fallback Clauses",
    sectionLabel: "Mutual Indemnity Fallback",
    snippetText:
      "Indemnity obligations should remain tied to third-party claims and proportionate to the risk controlled by the indemnifying party.",
    fullText: demoFallback,
    issueTypes: ["indemnity"],
  },
  {
    id: "fd26831e-f895-4ea5-9e6d-2a321029dc9a",
    documentVersionId: demoDocumentVersionIds.playbook,
    evidenceType: "playbook",
    title: "Negotiation Playbook",
    sectionLabel: "Payment Terms",
    snippetText: "Net 30 for undisputed invoices is standard.",
    fullText: demoPlaybook,
    issueTypes: ["payment_terms"],
  },
  {
    id: "c38ff278-eb15-4fe0-8b17-e9584b03c676",
    documentVersionId: demoDocumentVersionIds.precedent,
    evidenceType: "precedent",
    title: "Vendor Precedent Notes",
    sectionLabel: "Payment Benchmark",
    snippetText:
      "Suspension rights typically require written notice and only apply to undisputed overdue amounts.",
    fullText: demoPrecedent,
    issueTypes: ["payment_terms"],
  },
  {
    id: "4494dc0f-b14f-40f6-b9b4-cde518fd8605",
    documentVersionId: demoDocumentVersionIds.playbook,
    evidenceType: "playbook",
    title: "Negotiation Playbook",
    sectionLabel: "Confidentiality",
    snippetText:
      "Permit use of de-identified service data for analytics and do not accept blanket bans on internal service improvement.",
    fullText: demoPlaybook,
    issueTypes: ["confidentiality"],
  },
  {
    id: "2a4f8d55-4883-4769-a2d1-584cf9e9c817",
    documentVersionId: demoDocumentVersionIds.precedent,
    evidenceType: "precedent",
    title: "Vendor Precedent Notes",
    sectionLabel: "Confidentiality Benchmark",
    snippetText:
      "Confidentiality obligations usually survive three to five years, and analytics use is generally acceptable if the data is aggregated and de-identified.",
    fullText: demoPrecedent,
    issueTypes: ["confidentiality"],
  },
  {
    id: "d0cb4f7a-b7f5-43ed-ba51-8b4f14f4563b",
    documentVersionId: demoDocumentVersionIds.playbook,
    evidenceType: "playbook",
    title: "Negotiation Playbook",
    sectionLabel: "Termination",
    snippetText:
      "Avoid customer termination for convenience during the committed subscription term unless stranded implementation costs are recovered.",
    fullText: demoPlaybook,
    issueTypes: ["termination"],
  },
  {
    id: "9377e8b7-d010-40e6-b0ec-ffdfaf19a16d",
    documentVersionId: demoDocumentVersionIds.fallback,
    evidenceType: "fallback",
    title: "Approved Fallback Clauses",
    sectionLabel: "Termination Fallback",
    snippetText:
      "Either party may terminate for material breach if the breach remains uncured for thirty (30) days after written notice.",
    fullText: demoFallback,
    issueTypes: ["termination"],
  },
];

export function seedDemoData(personaSlug = demoDefaultPersonaSlug): DemoSeed {
  return {
    matterName: demoMatterName,
    originalContract: demoOriginalContract,
    revisedContract: demoRevisedContract,
    evidenceDocuments: [
      {
        id: "5f0c6cd3-64a2-4dc8-bc5d-5f87cf30ac1d",
        label: "Customer Playbook",
        type: "playbook",
        title: "Negotiation Playbook",
        text: demoPlaybook,
      },
      {
        id: "ca27dd5f-2bc4-4f2b-b718-e18d5b28ec6c",
        label: "Vendor Precedent",
        type: "precedent",
        title: "Vendor Precedent Notes",
        text: demoPrecedent,
      },
      {
        id: "2cf72afd-b8a7-454e-9c16-3690ba55589f",
        label: "Fallback Clauses",
        type: "fallback",
        title: "Approved Fallback Clauses",
        text: demoFallback,
      },
    ],
    personas: demoPersonas,
    defaultPersona: demoPersonas.find((persona) => persona.slug === personaSlug) ?? demoPersonas[2],
  };
}

export async function runDemo(options?: { personaSlug?: string }): Promise<DemoRunBundle> {
  try {
    const seed = seedDemoData(options?.personaSlug);
    const runId = "4af6ee07-ed2b-4cff-8665-7ff876143c71";
    const run = buildRun(runId, seed.defaultPersona.id);
    const originalClauses = buildClauses(seed.originalContract, demoDocumentVersionIds.original, "original");
    const revisedClauses = buildClauses(seed.revisedContract, demoDocumentVersionIds.revised, "revised");
    const results = buildClauseResults({
      run,
      persona: seed.defaultPersona,
      originalClauses,
      revisedClauses,
    });
    const overview = buildOverview(results);

    return {
      message: "Demo matter loaded and simulation completed locally.",
      matterName: seed.matterName,
      persona: seed.defaultPersona,
      originalContract: seed.originalContract,
      revisedContract: seed.revisedContract,
      evidenceDocuments: seed.evidenceDocuments.map((document) => ({
        ...document,
        uploadedVersionId: mapEvidenceVersionId(document.type),
      })),
      runStatus: { run: { ...run, summary_json: overview, total_changed_clauses: results.length } },
      runSummary: {
        run: { ...run, summary_json: overview, total_changed_clauses: results.length },
        persona: seed.defaultPersona,
        overview,
      },
      clauseResults: {
        run: { ...run, summary_json: overview, total_changed_clauses: results.length },
        results,
      },
    };
  } catch {
    return buildFailsafeDemoBundle(options?.personaSlug ?? demoDefaultPersonaSlug);
  }
}

function buildFailsafeDemoBundle(personaSlug: string): DemoRunBundle {
  const seed = seedDemoData(personaSlug);
  const run = buildRun("1d36408b-54f4-45bd-a3a3-9c16f96cb6c3", seed.defaultPersona.id);
  const results = buildFallbackResults(run.id, seed.defaultPersona);
  const overview = buildOverview(results);

  return {
    message: "Demo matter loaded from the built-in fallback scenario.",
    matterName: seed.matterName,
    persona: seed.defaultPersona,
    originalContract: seed.originalContract,
    revisedContract: seed.revisedContract,
    evidenceDocuments: seed.evidenceDocuments.map((document) => ({
      ...document,
      uploadedVersionId: mapEvidenceVersionId(document.type),
    })),
    runStatus: { run: { ...run, summary_json: overview, total_changed_clauses: results.length } },
    runSummary: {
      run: { ...run, summary_json: overview, total_changed_clauses: results.length },
      persona: seed.defaultPersona,
      overview,
    },
    clauseResults: {
      run: { ...run, summary_json: overview, total_changed_clauses: results.length },
      results,
    },
  };
}

function buildRun(runId: string, personaId: string): Run {
  return {
    id: runId,
    created_at: demoTimestamp,
    updated_at: demoTimestamp,
    original_document_version_id: demoDocumentVersionIds.original,
    revised_document_version_id: demoDocumentVersionIds.revised,
    persona_id: personaId,
    status: "completed",
    stage: "completed",
    error_message: null,
    input_snapshot: {
      mode: "local_demo",
      evidence_document_version_ids: [
        demoDocumentVersionIds.playbook,
        demoDocumentVersionIds.precedent,
        demoDocumentVersionIds.fallback,
      ],
    },
    summary_json: {},
    total_changed_clauses: 0,
    started_at: demoTimestamp,
    completed_at: demoTimestamp,
  };
}

function buildClauses(
  contractText: string,
  documentVersionId: string,
  variant: "original" | "revised",
): Clause[] {
  return parseClauseBlocks(contractText).map((block) => ({
    id: makeId(`${variant}-${block.clauseNumber}`),
    created_at: demoTimestamp,
    updated_at: demoTimestamp,
    document_version_id: documentVersionId,
    stable_clause_id: `clause-${block.clauseNumber}`,
    heading: block.heading,
    heading_path: `${block.clauseNumber}. ${block.heading}`,
    clause_number: block.clauseNumber,
    order_index: block.orderIndex,
    text: block.text,
    normalized_text: normalizeText(block.text),
    source_span: {
      start_line: block.orderIndex * 3 + 1,
      end_line: block.orderIndex * 3 + 3,
    },
  }));
}

function parseClauseBlocks(contractText: string): ParsedClauseBlock[] {
  return contractText
    .split(/\n\s*\n/g)
    .map((block) => block.trim())
    .filter((block) => /^\d+\.\s+/.test(block))
    .map((block, index) => {
      const match = block.match(/^(\d+)\.\s+([^.]+)\.\s+([\s\S]+)$/);
      if (!match) {
        throw new Error(`Unable to parse demo clause block: ${block}`);
      }

      return {
        clauseNumber: match[1],
        heading: match[2].trim(),
        text: `${match[1]}. ${match[2].trim()}. ${match[3].trim().replace(/\s+/g, " ")}`,
        orderIndex: index,
      };
    });
}

function buildClauseResults(options: {
  run: Run;
  persona: Persona;
  originalClauses: Clause[];
  revisedClauses: Clause[];
}): ClauseReviewResult[] {
  return options.revisedClauses.flatMap((revisedClause) => {
      const originalClause = options.originalClauses.find(
        (candidate) => candidate.clause_number === revisedClause.clause_number,
      );
      if (!originalClause || normalizeText(originalClause.text) === normalizeText(revisedClause.text)) {
        return [];
      }

      const issueType = classifyIssueType(revisedClause.heading, revisedClause.text);
      const retrievalHits = buildRetrievalHits(options.run.id, revisedClause, issueType);
      const clauseChange = buildClauseChange(options.run.id, originalClause, revisedClause, issueType);
      const simulationResult = buildSimulationResult(
        options.run.id,
        clauseChange,
        options.persona,
        originalClause,
        revisedClause,
        retrievalHits,
      );
      const scoringResult = buildScoringResult(options.run.id, clauseChange, options.persona, simulationResult);

      return [{
        clause_change: clauseChange,
        original_clause: originalClause,
        revised_clause: revisedClause,
        simulation_result: simulationResult,
        scoring_result: scoringResult,
        retrieval_hits: retrievalHits,
      }];
    });
}

function buildClauseChange(
  runId: string,
  originalClause: Clause,
  revisedClause: Clause,
  issueType: DemoIssueType,
): ClauseChange {
  const changedTokens = Math.max(
    12,
    Math.abs(normalizeText(revisedClause.text).split(" ").length - normalizeText(originalClause.text).split(" ").length) +
      18,
  );

  return {
    id: makeId(`change-${revisedClause.clause_number}`),
    created_at: demoTimestamp,
    updated_at: demoTimestamp,
    negotiation_run_id: runId,
    original_clause_id: originalClause.id,
    revised_clause_id: revisedClause.id,
    clause_key: revisedClause.stable_clause_id,
    change_type: "modified",
    issue_type: issueType,
    change_direction: directionByIssue[issueType],
    semantic_summary: clauseSummaries[issueType],
    diff_details: {
      original_excerpt: originalClause.text,
      revised_excerpt: revisedClause.text,
      heading: revisedClause.heading,
    },
    changed_tokens_count: changedTokens,
    status: "completed",
  };
}

function buildRetrievalHits(
  runId: string,
  revisedClause: Clause,
  issueType: DemoIssueType,
): RetrievalHit[] {
  return evidenceCatalog
    .filter((entry) => entry.issueTypes.includes(issueType))
    .slice(0, 2)
    .map((entry, index) => {
      const evidenceSource: EvidenceSource = {
        id: entry.id,
        created_at: demoTimestamp,
        updated_at: demoTimestamp,
        document_version_id: entry.documentVersionId,
        evidence_type: entry.evidenceType,
        title: entry.title,
        section_label: entry.sectionLabel,
        snippet_text: entry.snippetText,
        full_text: entry.fullText,
        token_count: entry.snippetText.split(" ").length,
        metadata_json: {
          local_demo: true,
          issue_type: issueType,
        },
        vector_id: null,
      };

      return {
        id: makeId(`hit-${revisedClause.clause_number}-${index}`),
        created_at: demoTimestamp,
        updated_at: demoTimestamp,
        negotiation_run_id: runId,
        clause_change_id: makeId(`change-${revisedClause.clause_number}`),
        evidence_source_id: evidenceSource.id,
        rank: index + 1,
        vector_score: round(0.81 - index * 0.06),
        lexical_score: round(0.78 - index * 0.05),
        rerank_score: round(0.84 - index * 0.04),
        snippet_text: entry.snippetText,
        metadata_json: {
          local_demo: true,
        },
        evidence_source: evidenceSource,
      };
    });
}

function buildSimulationResult(
  runId: string,
  clauseChange: ClauseChange,
  persona: Persona,
  originalClause: Clause,
  revisedClause: Clause,
  retrievalHits: RetrievalHit[],
): SimulationResult {
  const issueType = clauseChange.issue_type as DemoIssueType;
  const customerSide = persona.slug !== "startup-counsel";
  const issueLabel = issueLabels[issueType];
  const evidenceLead = retrievalHits[0]?.snippet_text ?? "Fallback guidance supports a balanced vendor position.";
  const decision = determineDecision(issueType, customerSide);
  const counterproposalText = buildCounterproposal(issueType, customerSide);

  return {
    id: makeId(`simulation-${revisedClause.clause_number}`),
    created_at: demoTimestamp,
    updated_at: demoTimestamp,
    negotiation_run_id: runId,
    clause_change_id: clauseChange.id,
    decision,
    stance_strength: customerSide ? 0.66 : 0.86,
    business_reason: customerSide
      ? `${persona.name} views the revised ${issueLabel.toLowerCase()} language as directionally aligned with enterprise risk controls, but still wants tighter drafting where the operational obligation is too open-ended.`
      : `${persona.name} sees the revised ${issueLabel.toLowerCase()} language as materially shifting commercial and balance-sheet risk onto the vendor beyond what is usually acceptable for a growth-stage SaaS company.`,
    legal_reason: customerSide
      ? `The redline is broadly supportable, but the clause should still be tied back to market guardrails and clearer drafting. ${evidenceLead}`
      : `The redline overreaches relative to SaaS market norms and should be moved back toward a balanced fallback. ${evidenceLead}`,
    pushback_points: buildPushbackPoints(issueType, customerSide, originalClause, revisedClause),
    counterproposal_text: counterproposalText,
    strategy: customerSide
      ? "Preserve the customer-friendly direction while narrowing ambiguities that could slow review."
      : "Acknowledge the business ask, rely on precedent, and move quickly to a balanced fallback that still protects execution risk.",
    confidence: customerSide ? 0.78 : 0.84,
    critique_status: "passed",
    grounded_evidence_count: retrievalHits.length,
    raw_model_output: {
      mode: "local_demo",
      issue_type: issueType,
    },
  };
}

function buildScoringResult(
  runId: string,
  clauseChange: ClauseChange,
  persona: Persona,
  simulationResult: SimulationResult,
): ScoringResult {
  const issueType = clauseChange.issue_type as DemoIssueType;
  const base = baseScoring[issueType];
  const leverageAdjustment = (persona.leverage - 3) * 0.025;
  const strictnessAdjustment = (persona.liability_strictness - 3) * 0.035;
  const speedAdjustment = (persona.speed_priority - 3) * -0.02;
  const orientationAdjustment = persona.slug === "startup-counsel" ? 0.04 : -0.02;

  const pushbackProbability = clamp(base.pushback + leverageAdjustment + strictnessAdjustment + orientationAdjustment);
  const negotiationFriction = clamp(base.friction + strictnessAdjustment + speedAdjustment);
  const delayRisk = clamp(base.delay + leverageAdjustment + speedAdjustment / 2);
  const severity = clamp(base.severity + strictnessAdjustment / 2 + orientationAdjustment / 2);

  return {
    id: makeId(`score-${clauseChange.clause_key}`),
    created_at: demoTimestamp,
    updated_at: demoTimestamp,
    negotiation_run_id: runId,
    clause_change_id: clauseChange.id,
    pushback_probability: round(pushbackProbability),
    negotiation_friction: round(negotiationFriction),
    delay_risk: round(delayRisk),
    severity: round(severity),
    friction_label: frictionLabelFor(negotiationFriction),
    explanation:
      simulationResult.decision === "accept"
        ? "The selected persona is generally aligned with the revised clause, so the expected friction is modest."
        : "This clause changes core economic or risk-allocation terms, so it is likely to draw structured pushback and require fallback drafting.",
    heuristic_details: {
      issue_type: issueType,
      persona_slug: persona.slug,
      local_demo: true,
    },
  };
}

function buildOverview(results: ClauseReviewResult[]): RunOverview {
  const highFriction = results.filter((result) => result.scoring_result?.friction_label === "high").length;
  const likelyPushback = results.filter((result) => {
    const decision = result.simulation_result?.decision;
    return decision === "counter" || decision === "push_back" || decision === "escalate";
  }).length;
  const totalDifficulty =
    results.reduce((sum, result) => sum + (result.scoring_result?.severity ?? 0), 0) /
    Math.max(results.length, 1);

  return {
    total_changed_clauses: results.length,
    likely_pushback_count: likelyPushback,
    high_friction_clauses: highFriction,
    overall_negotiation_difficulty: round(totalDifficulty),
  };
}

function buildFallbackResults(runId: string, persona: Persona): ClauseReviewResult[] {
  const originalClauses = buildClauses(demoOriginalContract, demoDocumentVersionIds.original, "original");
  const revisedClauses = buildClauses(demoRevisedContract, demoDocumentVersionIds.revised, "revised");
  return buildClauseResults({
    run: buildRun(runId, persona.id),
    persona,
    originalClauses,
    revisedClauses,
  });
}

function classifyIssueType(heading: string, text: string): DemoIssueType {
  const normalizedHeading = heading.toLowerCase();
  const combined = `${heading} ${text}`.toLowerCase();

  if (normalizedHeading.includes("liability")) return "limitation_of_liability";
  if (normalizedHeading.includes("indemn")) return "indemnity";
  if (normalizedHeading.includes("payment")) return "payment_terms";
  if (normalizedHeading.includes("confidential")) return "confidentiality";
  if (normalizedHeading.includes("termination")) return "termination";

  if (combined.includes("liability")) return "limitation_of_liability";
  if (combined.includes("indemn")) return "indemnity";
  if (combined.includes("payment")) return "payment_terms";
  if (combined.includes("confidential")) return "confidentiality";
  return "termination";
}

function determineDecision(issueType: DemoIssueType, customerSide: boolean): SimulationResult["decision"] {
  if (customerSide) {
    if (issueType === "payment_terms" || issueType === "confidentiality") return "accept";
    return "counter";
  }

  if (issueType === "limitation_of_liability") return "escalate";
  if (issueType === "termination") return "push_back";
  return "counter";
}

function buildCounterproposal(issueType: DemoIssueType, customerSide: boolean): string {
  if (customerSide) {
    switch (issueType) {
      case "payment_terms":
        return "Customer may withhold only the specifically disputed portion of an invoice, and undisputed invoices remain due within forty-five (45) days after receipt.";
      case "confidentiality":
        return "Vendor may use de-identified service data for internal analytics and service improvement, but not for model training or external benchmarking without Customer approval.";
      case "limitation_of_liability":
        return "Each party's aggregate liability will be capped at two (2) times the fees paid or payable in the preceding twelve (12) months, with targeted carve-outs for confidentiality, data protection, indemnity obligations, fraud, and willful misconduct.";
      case "indemnity":
        return "Vendor will indemnify Customer for IP infringement, confidentiality breaches, and Vendor-caused data protection claims, while the parties remain open to mutual indemnity for risks each party controls.";
      case "termination":
        return "Customer may terminate for convenience on sixty (60) days' notice after go-live, and Vendor will provide commercially reasonable transition assistance at standard rates unless termination is caused by Vendor breach.";
    }
  }

  switch (issueType) {
    case "payment_terms":
      return "Invoices are due within thirty (30) days after receipt, Customer may withhold only specifically disputed amounts, and suspension applies only to undisputed overdue amounts after written notice.";
    case "confidentiality":
      return "Confidentiality obligations survive for three (3) years after termination, and Vendor may use aggregated, de-identified service data for internal analytics and product improvement.";
    case "limitation_of_liability":
      return "Except for fraud, willful misconduct, and third-party IP indemnity obligations, each party's aggregate liability under this Agreement will not exceed the fees paid or payable in the twelve (12) months preceding the claim, with any confidentiality or data protection carve-out subject to a separate super-cap.";
    case "indemnity":
      return "Indemnity will remain limited to third-party claims and mutual where each party controls the relevant risk. Vendor's obligations cover IP infringement claims, while data and confidentiality obligations remain subject to negotiated fault-based remedies.";
    case "termination":
      return "Either party may terminate for material breach if the breach remains uncured for thirty (30) days after written notice. Customer convenience termination during the initial term requires at least sixty (60) days' notice and payment of committed fees through the termination date.";
  }
}

function buildPushbackPoints(
  issueType: DemoIssueType,
  customerSide: boolean,
  originalClause: Clause,
  revisedClause: Clause,
): string[] {
  if (customerSide) {
    switch (issueType) {
      case "payment_terms":
        return [
          "The disputed-amount withholding right should be narrowed so only the contested line items are delayed.",
          "Suspension timing can be extended, but the notice mechanics should still preserve a practical payment remedy.",
        ];
      case "confidentiality":
        return [
          "The no-analytics restriction is directionally right, but it should expressly allow de-identified service-improvement use.",
          "Injunctive relief language should remain standard and avoid creating a broader remedies regime than necessary.",
        ];
      case "limitation_of_liability":
        return [
          "The higher cap is supportable for a strategic customer, but the carve-outs should be listed precisely rather than drafted as an open category.",
          "Customer should keep enhanced protection for data, confidentiality, and indemnity without creating unnecessary ambiguity around indirect damages.",
        ];
      case "indemnity":
        return [
          "Coverage should remain tied to third-party claims and avoid accidental first-party indemnity.",
          "Customer can keep expanded data and confidentiality coverage while still clarifying causation and defense control.",
        ];
      case "termination":
        return [
          "Convenience termination is useful, but the operational transition obligations should be calibrated to the deal size and implementation state.",
          "The 15-day cure period may be too short for noncritical breaches and could be tiered by breach type.",
        ];
    }
  }

  const originalSummary = originalClause.text.slice(0, 130);
  const revisedSummary = revisedClause.text.slice(0, 130);

  switch (issueType) {
    case "payment_terms":
      return [
        "Net 45 plus a broad withholding right materially extends vendor credit exposure beyond the original payment position.",
        `Original position: ${originalSummary}... Revised position: ${revisedSummary}...`,
      ];
    case "confidentiality":
      return [
        "The redline removes normal de-identified analytics flexibility and expands remedies beyond the operational risk actually being allocated.",
        "The five-year survival period is workable, but the internal-use restriction should be tied to identifiable data only.",
      ];
    case "limitation_of_liability":
      return [
        "The revised clause doubles the economic cap and then strips the cap away for several of the vendor's core operational risks.",
        "A startup vendor can usually move on carve-outs, but not to an uncapped or effectively uncapped exposure profile.",
      ];
    case "indemnity":
      return [
        "The expanded indemnity reaches far beyond the normal third-party IP construct and shifts broad operational liability into a single uncapped remedy.",
        "If Customer wants broader protection, the cleaner path is a mutual, fault-based indemnity tied to third-party claims and insurance-backed risks.",
      ];
    case "termination":
      return [
        "Convenience termination during the initial term undermines committed revenue and implementation recovery for the vendor.",
        "A 15-day cure period and free transition support are both more aggressive than standard SaaS practice for an annual subscription.",
      ];
  }
}

function mapEvidenceVersionId(type: DemoEvidenceDocument["type"]): string {
  if (type === "playbook") return demoDocumentVersionIds.playbook;
  if (type === "precedent") return demoDocumentVersionIds.precedent;
  return demoDocumentVersionIds.fallback;
}

function frictionLabelFor(value: number): "low" | "medium" | "high" {
  if (value >= 0.75) return "high";
  if (value >= 0.55) return "medium";
  return "low";
}

function normalizeText(value: string): string {
  return value.toLowerCase().replace(/\s+/g, " ").trim();
}

function makeId(seed: string): string {
  const numeric = Array.from(seed).reduce((total, character, index) => total + character.charCodeAt(0) * (index + 17), 0);
  const fragment = numeric.toString(16).padStart(12, "0").slice(0, 12);
  return `00000000-0000-4000-8000-${fragment}`;
}

function clamp(value: number): number {
  return Math.max(0.12, Math.min(0.96, value));
}

function round(value: number): number {
  return Number(value.toFixed(2));
}
