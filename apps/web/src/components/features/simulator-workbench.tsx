"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  BotMessageSquare,
  BriefcaseBusiness,
  FileStack,
  Gavel,
  Scale,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import { type ReactNode, useEffect, useMemo, useState } from "react";

import {
  createRun,
  fetchClauseResults,
  fetchPersonas,
  fetchRunSummary,
  uploadDocument,
} from "@/lib/api";
import {
  demoDefaultPersonaSlug,
  demoPersonas,
} from "@/lib/demo-data";
import { runDemo, type DemoRunBundle } from "@/lib/demo-engine";
import { useRunPolling } from "@/lib/hooks/use-run-polling";
import { formatDifficulty, frictionVariant } from "@/lib/presenters";
import { cn } from "@/lib/utils";
import type { UploadDocumentResponse } from "@ocs/schemas";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

type EvidenceDraft = {
  label: string;
  type: "playbook" | "precedent" | "fallback";
  text: string;
  file: File | null;
  uploadedVersionId: string | null;
};

const workflowLabels = [
  "queued",
  "diffing",
  "classification",
  "retrieval",
  "simulation",
  "completed",
] as const;

export function SimulatorWorkbench() {
  const personasQuery = useQuery({
    queryKey: ["personas"],
    queryFn: fetchPersonas,
  });

  const [contractName, setContractName] = useState("Cloud Platform MSA");
  const [originalText, setOriginalText] = useState("");
  const [revisedText, setRevisedText] = useState("");
  const [originalFile, setOriginalFile] = useState<File | null>(null);
  const [revisedFile, setRevisedFile] = useState<File | null>(null);
  const [selectedPersonaId, setSelectedPersonaId] = useState("");
  const [selectedClauseId, setSelectedClauseId] = useState<string | null>(null);
  const [originalUpload, setOriginalUpload] = useState<UploadDocumentResponse | null>(null);
  const [revisedUpload, setRevisedUpload] = useState<UploadDocumentResponse | null>(null);
  const [evidenceDrafts, setEvidenceDrafts] = useState<EvidenceDraft[]>([
    { label: "Customer Playbook", type: "playbook", text: "", file: null, uploadedVersionId: null },
    { label: "Vendor Precedent", type: "precedent", text: "", file: null, uploadedVersionId: null },
    { label: "Fallback Clauses", type: "fallback", text: "", file: null, uploadedVersionId: null },
  ]);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [demoBundle, setDemoBundle] = useState<DemoRunBundle | null>(null);

  const runStatusQuery = useRunPolling(activeRunId);
  const runSummaryQuery = useQuery({
    queryKey: ["run-summary", activeRunId],
    queryFn: () => fetchRunSummary(activeRunId as string),
    enabled: Boolean(activeRunId) && runStatusQuery.data?.run.status === "completed",
  });
  const clauseResultsQuery = useQuery({
    queryKey: ["clause-results", activeRunId],
    queryFn: () => fetchClauseResults(activeRunId as string),
    enabled: Boolean(activeRunId) && runStatusQuery.data?.run.status === "completed",
  });

  const availablePersonas = personasQuery.data?.length ? personasQuery.data : demoPersonas;
  const selectedPersona = useMemo(
    () => availablePersonas.find((persona) => persona.id === selectedPersonaId) ?? null,
    [availablePersonas, selectedPersonaId],
  );
  const runStatusData = demoBundle?.runStatus ?? runStatusQuery.data ?? null;
  const runSummaryData = demoBundle?.runSummary ?? runSummaryQuery.data ?? null;
  const reviewResults = useMemo(
    () => demoBundle?.clauseResults.results ?? clauseResultsQuery.data?.results ?? [],
    [clauseResultsQuery.data, demoBundle],
  );
  const selectedResult = useMemo(
    () => reviewResults.find((result) => result.clause_change.id === selectedClauseId) ?? reviewResults[0] ?? null,
    [reviewResults, selectedClauseId],
  );

  const uploadMutation = useMutation({
    mutationFn: uploadDocument,
  });

  const createRunMutation = useMutation({
    mutationFn: createRun,
    onSuccess: (result) => {
      setDemoBundle(null);
      setActiveRunId(result.run.id);
    },
  });

  const demoRunMutation = useMutation({
    mutationFn: () => runDemo({ personaSlug: selectedPersona?.slug ?? demoDefaultPersonaSlug }),
    onSuccess: (result) => {
      setDemoBundle(result);
      setActiveRunId(null);
      setSelectedPersonaId(result.persona.id);
      setContractName(result.matterName);
      setOriginalText(result.originalContract);
      setRevisedText(result.revisedContract);
      setOriginalFile(null);
      setRevisedFile(null);
      setOriginalUpload(null);
      setRevisedUpload(null);
      setEvidenceDrafts([
        {
          label: "Customer Playbook",
          type: "playbook",
          text: result.evidenceDocuments[0]?.text ?? "",
          file: null,
          uploadedVersionId: result.evidenceDocuments[0]?.uploadedVersionId ?? null,
        },
        {
          label: "Vendor Precedent",
          type: "precedent",
          text: result.evidenceDocuments[1]?.text ?? "",
          file: null,
          uploadedVersionId: result.evidenceDocuments[1]?.uploadedVersionId ?? null,
        },
        {
          label: "Fallback Clauses",
          type: "fallback",
          text: result.evidenceDocuments[2]?.text ?? "",
          file: null,
          uploadedVersionId: result.evidenceDocuments[2]?.uploadedVersionId ?? null,
        },
      ]);
    },
  });

  const uiError =
    (uploadMutation.error as Error | null)?.message ??
    (createRunMutation.error as Error | null)?.message ??
    (demoRunMutation.error as Error | null)?.message ??
    (runStatusQuery.error as Error | null)?.message ??
    (runSummaryQuery.error as Error | null)?.message ??
    (clauseResultsQuery.error as Error | null)?.message ??
    null;
  const indexedEvidenceCount = evidenceDrafts.filter((item) => item.uploadedVersionId).length;
  const hasMatterLoaded = Boolean(demoBundle) || Boolean(originalUpload && revisedUpload);
  const currentStage = runStatusData?.run.stage ?? "queued";
  const currentStageIndex = workflowLabels.indexOf(currentStage as (typeof workflowLabels)[number]);

  useEffect(() => {
    if (!reviewResults.length) {
      setSelectedClauseId(null);
      return;
    }
    if (!selectedClauseId || !reviewResults.some((result) => result.clause_change.id === selectedClauseId)) {
      setSelectedClauseId(reviewResults[0].clause_change.id);
    }
  }, [reviewResults, selectedClauseId]);

  async function uploadContractsAndEvidence() {
    setDemoBundle(null);
    const original = await uploadMutation.mutateAsync({
      path: "/api/documents/original",
      name: `${contractName} Original`,
      textContent: originalText,
      file: originalFile,
    });
    const revised = await uploadMutation.mutateAsync({
      path: "/api/documents/revised",
      name: `${contractName} Revised`,
      textContent: revisedText,
      file: revisedFile,
    });

    const nextEvidenceDrafts = [...evidenceDrafts];
    for (let index = 0; index < nextEvidenceDrafts.length; index += 1) {
      const draft = nextEvidenceDrafts[index];
      if (!draft.text.trim() && !draft.file) continue;
      const uploaded = await uploadMutation.mutateAsync({
        path: "/api/documents/evidence",
        name: draft.label,
        textContent: draft.text,
        evidenceType: draft.type,
        file: draft.file,
      });
      nextEvidenceDrafts[index] = {
        ...draft,
        uploadedVersionId: uploaded.version.id,
      };
    }

    setEvidenceDrafts(nextEvidenceDrafts);
    setOriginalUpload(original);
    setRevisedUpload(revised);
  }

  async function runAnalysis() {
    if (!selectedPersonaId || !originalUpload || !revisedUpload) return;
    setDemoBundle(null);
    setActiveRunId(null);
    setSelectedClauseId(null);
    await createRunMutation.mutateAsync({
      original_document_version_id: originalUpload.version.id,
      revised_document_version_id: revisedUpload.version.id,
      persona_id: selectedPersonaId,
      evidence_document_version_ids: evidenceDrafts
        .map((draft) => draft.uploadedVersionId)
        .filter((value): value is string => Boolean(value)),
      run_async: false,
    });
  }

  async function runDemoFlow() {
    setActiveRunId(null);
    setSelectedClauseId(null);
    await demoRunMutation.mutateAsync();
  }

  return (
    <main className="app-shell mx-auto flex min-h-screen max-w-[1680px] flex-col gap-7 px-4 py-6 md:px-6 xl:px-8 xl:py-9">
      <header className="hero-panel rounded-[32px] border border-border/90 px-6 py-6 shadow-panel md:px-8 md:py-8 xl:px-10 xl:py-9">
        <div className="flex flex-col gap-9 xl:flex-row xl:items-end xl:justify-between">
          <div className="max-w-4xl space-y-6">
            <div className="flex flex-wrap items-center gap-3">
              <Badge className="border-border/80 bg-card/60 text-foreground" variant="neutral">
                Opposing Counsel Simulator
              </Badge>
              <Badge className="border-emerald-400/20 bg-emerald-500/12 text-emerald-100" variant="low">
                Demo-ready workflow
              </Badge>
            </div>
            <div className="space-y-4">
              <p className="max-w-3xl text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                Clause-level negotiation review for product, legal, and revenue teams
              </p>
              <h1 className="max-w-4xl text-4xl font-semibold leading-[1.05] text-foreground md:text-5xl">
                Negotiation review built as a clause engine, not a chatbot.
              </h1>
              <p className="max-w-3xl text-base leading-8 text-muted-foreground">
                Upload contract versions, ground redlines in playbooks and precedent, simulate a
                structured opposing-counsel response, and review the output in a high-trust legal-tech
                console.
              </p>
            </div>
          </div>

          <div className="flex w-full flex-col gap-4 xl:max-w-[430px]">
            <Card tone="ghost" className="rounded-[26px] bg-background/24 p-6 backdrop-blur-sm">
              <p className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                Quick Start
              </p>
              <p className="mt-3 text-sm leading-7 text-foreground">
                Run a complete bundled negotiation scenario with realistic contracts, evidence, and clause-by-clause output.
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                <Button onClick={runDemoFlow} disabled={demoRunMutation.isPending}>
                  {demoRunMutation.isPending ? "Running demo..." : "Run Demo"}
                </Button>
              </div>
              <div className="mt-5 grid grid-cols-2 gap-3">
                <QuickStat label="Workflow" value="Clause-by-clause" />
                <QuickStat label="Mode" value="No backend required" />
              </div>
            </Card>
          </div>
        </div>

        <div className="mt-7 flex flex-wrap gap-2">
          {workflowLabels.map((label) => (
            <Badge key={label} className="border-border/70 bg-background/40 text-muted-foreground" variant="neutral">
              {label.replace("_", " ")}
            </Badge>
          ))}
        </div>
      </header>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          icon={FileStack}
          label="Changed Clauses"
          value={runSummaryData?.overview.total_changed_clauses ?? "–"}
          supporting="Clauses currently in scope"
        />
        <MetricCard
          icon={AlertTriangle}
          label="Likely Pushback"
          value={runSummaryData?.overview.likely_pushback_count ?? "–"}
          supporting="Counterparty objections expected"
        />
        <MetricCard
          icon={Gavel}
          label="High Friction"
          value={runSummaryData?.overview.high_friction_clauses ?? "–"}
          supporting="Clauses likely to stall paper"
        />
        <MetricCard
          icon={Scale}
          label="Difficulty"
          value={formatDifficulty(runSummaryData?.overview.overall_negotiation_difficulty)}
          supporting="Estimated negotiation complexity"
        />
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.25fr_0.75fr]">
        <Card className="grid gap-6 xl:grid-cols-[1.08fr_0.92fr]" padding="lg">
          <div className="space-y-5">
            <SectionHeader
              eyebrow="Matter Intake"
              title="Contract versions"
              description="Upload or paste the original and revised agreements before launching analysis."
            />

            <div className="space-y-2">
              <FieldLabel htmlFor="contract-name">Matter name</FieldLabel>
              <Input
                id="contract-name"
                value={contractName}
                onChange={(event) => setContractName(event.target.value)}
                placeholder="Cloud Platform MSA"
              />
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <Card tone="muted" className="space-y-4 rounded-[22px] p-5">
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-3">
                    <FieldLabel>Original contract</FieldLabel>
                    <Badge variant="neutral">Baseline</Badge>
                  </div>
                  <p className="text-sm leading-6 text-muted-foreground">
                    Baseline version used to trace clause deltas and issue direction.
                  </p>
                </div>
                <UploadControl
                  label="Source document"
                  helper="PDF, DOCX, or TXT"
                  fileName={originalFile?.name ?? null}
                >
                  <Input
                    type="file"
                    accept=".txt,.docx,.pdf"
                    onChange={(event) => setOriginalFile(event.target.files?.[0] ?? null)}
                  />
                </UploadControl>
                <Textarea
                  className="min-h-60"
                  value={originalText}
                  onChange={(event) => setOriginalText(event.target.value)}
                  placeholder="Paste the original agreement text or upload a document."
                />
              </Card>

              <Card tone="muted" className="space-y-4 rounded-[22px] p-5">
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-3">
                    <FieldLabel>Revised contract</FieldLabel>
                    <Badge variant="decision">Redline</Badge>
                  </div>
                  <p className="text-sm leading-6 text-muted-foreground">
                    Counterparty edits, redlines, or revised text that should be analyzed clause by clause.
                  </p>
                </div>
                <UploadControl
                  label="Source document"
                  helper="PDF, DOCX, or TXT"
                  fileName={revisedFile?.name ?? null}
                >
                  <Input
                    type="file"
                    accept=".txt,.docx,.pdf"
                    onChange={(event) => setRevisedFile(event.target.files?.[0] ?? null)}
                  />
                </UploadControl>
                <Textarea
                  className="min-h-60"
                  value={revisedText}
                  onChange={(event) => setRevisedText(event.target.value)}
                  placeholder="Paste the revised agreement text or upload a document."
                />
              </Card>
            </div>

            <div className="flex flex-wrap gap-3 pt-1">
              <Button
                onClick={uploadContractsAndEvidence}
                disabled={
                  ((!originalText.trim() && !originalFile) || (!revisedText.trim() && !revisedFile)) ||
                  uploadMutation.isPending
                }
              >
                {uploadMutation.isPending ? "Uploading matter..." : "Upload matter set"}
              </Button>
              <Button variant="secondary" onClick={runDemoFlow} disabled={demoRunMutation.isPending}>
                {demoRunMutation.isPending ? "Running demo..." : "Run Demo"}
              </Button>
            </div>
          </div>

          <div className="space-y-5">
            <SectionHeader
              eyebrow="Evidence Library"
              title="Playbooks and fallbacks"
              description="Attach the internal guidance that should inform retrieval and counterproposal strategy."
            />

            {evidenceDrafts.map((draft, index) => (
              <Card key={draft.type} tone="muted" className="space-y-4 rounded-[22px] p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-foreground">{draft.label}</p>
                    <p className="mt-1 text-sm leading-6 text-muted-foreground">
                      {draft.type === "playbook" &&
                        "Preferred fallback language and negotiation guardrails for customer-side review."}
                      {draft.type === "precedent" &&
                        "Comparable market language or prior paper that supports the negotiating position."}
                      {draft.type === "fallback" &&
                        "Approved fallback language to ground counterproposal generation."}
                    </p>
                  </div>
                  <Badge variant={draft.uploadedVersionId ? "low" : "neutral"}>
                    {draft.uploadedVersionId ? "Indexed" : "Optional"}
                  </Badge>
                </div>

                <UploadControl
                  label="Supporting document"
                  helper="Optional PDF, DOCX, or TXT"
                  fileName={draft.file?.name ?? null}
                >
                  <Input
                    type="file"
                    accept=".txt,.docx,.pdf"
                    onChange={(event) =>
                      setEvidenceDrafts((current) =>
                        current.map((item, itemIndex) =>
                          itemIndex === index
                            ? { ...item, file: event.target.files?.[0] ?? null, uploadedVersionId: null }
                            : item,
                        ),
                      )
                    }
                  />
                </UploadControl>
                <Textarea
                  className="min-h-32"
                  value={draft.text}
                  onChange={(event) =>
                    setEvidenceDrafts((current) =>
                      current.map((item, itemIndex) =>
                        itemIndex === index
                          ? { ...item, text: event.target.value, uploadedVersionId: null }
                          : item,
                      ),
                    )
                  }
                  placeholder={`Paste ${draft.label.toLowerCase()} guidance.`}
                />
              </Card>
            ))}
          </div>
        </Card>

        <Card className="space-y-5" padding="lg">
          <SectionHeader
            eyebrow="Run Control"
            title="Counsel policy and launch"
            description="Select the opposing-counsel posture and start a deterministic clause-by-clause review."
          />

          <div className="space-y-2">
            <FieldLabel htmlFor="persona-select">Opposing-counsel persona</FieldLabel>
            <Select
              id="persona-select"
              value={selectedPersonaId}
              onChange={(event) => setSelectedPersonaId(event.target.value)}
            >
              <option value="">Select an opposing-counsel persona</option>
              {availablePersonas.map((persona) => (
                <option key={persona.id} value={persona.id}>
                  {persona.name}
                </option>
              ))}
            </Select>
          </div>

          {selectedPersona ? (
            <Card tone="muted" className="space-y-5 rounded-[22px] p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-base font-semibold text-foreground">{selectedPersona.name}</p>
                  <p className="mt-2 text-sm leading-7 text-muted-foreground">
                    {selectedPersona.description}
                  </p>
                </div>
                <Badge variant="decision">{selectedPersona.tone}</Badge>
              </div>
              <div className="space-y-3">
                <PersonaScale label="Risk tolerance" value={selectedPersona.risk_tolerance} />
                <PersonaScale label="Leverage" value={selectedPersona.leverage} />
                <PersonaScale label="Speed priority" value={selectedPersona.speed_priority} />
                <PersonaScale label="Liability strictness" value={selectedPersona.liability_strictness} />
              </div>
            </Card>
          ) : (
            <EmptyState text="Choose a persona to shape the simulated negotiating posture." />
          )}

          <div className="space-y-3">
            <Button
              onClick={runAnalysis}
              disabled={!selectedPersonaId || !originalUpload || !revisedUpload || createRunMutation.isPending}
              className="w-full"
            >
              {createRunMutation.isPending ? "Running manual analysis..." : "Run manual analysis"}
            </Button>
            <Button
              variant="secondary"
              onClick={runDemoFlow}
              disabled={demoRunMutation.isPending}
              className="w-full"
            >
              {demoRunMutation.isPending ? "Running demo..." : "Run Demo"}
            </Button>
          </div>

          {uiError ? <StatusPanel tone="error" text={uiError} /> : null}
          {!uiError && demoBundle?.message ? <StatusPanel tone="success" text={demoBundle.message} /> : null}
          {!uiError && runStatusData?.run.error_message ? (
            <StatusPanel tone="error" text={runStatusData.run.error_message} />
          ) : null}

          <Card tone="muted" className="space-y-3 rounded-[22px] p-5">
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Matter Status
            </p>
            <div className="space-y-3">
              <SummaryRow label="Matter loaded" value={hasMatterLoaded ? "Ready" : "Pending"} />
              <SummaryRow label="Evidence indexed" value={String(indexedEvidenceCount)} />
              <SummaryRow label="Run stage" value={currentStage} />
              <SummaryRow label="Run status" value={runStatusData?.run.status ?? "Idle"} />
            </div>
          </Card>

          <Card tone="ghost" className="rounded-[22px] bg-background/18 p-5">
            <p className="text-sm leading-7 text-muted-foreground">
              Outputs are framed as negotiation simulation for a product prototype and should not be treated
              as legal advice.
            </p>
          </Card>
        </Card>
      </section>

      <section className="grid gap-5 xl:grid-cols-[0.82fr_1.48fr_0.7fr]">
        <Card className="space-y-4" padding="lg">
          <SectionHeader
            eyebrow="Review Queue"
            title="Changed clauses"
            description="Prioritized clause changes with friction and issue tagging."
          />

          {reviewResults.length ? (
            <div className="space-y-2">
              {reviewResults.map((result) => {
                const isSelected = result.clause_change.id === selectedResult?.clause_change.id;
                const heading =
                  result.revised_clause?.heading ?? result.original_clause?.heading ?? "Changed clause";

                return (
                  <button
                    key={result.clause_change.id}
                    type="button"
                    onClick={() => setSelectedClauseId(result.clause_change.id)}
                    className={cn(
                      "w-full rounded-[20px] border px-4 py-4 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                      isSelected
                        ? "border-ring/35 bg-accent/65 shadow-subtle"
                        : "border-border/70 bg-background/28 hover:border-border hover:bg-muted/48",
                    )}
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="decision">{result.clause_change.issue_type.replaceAll("_", " ")}</Badge>
                      <Badge variant={frictionVariant(result.scoring_result?.friction_label)}>
                        {result.scoring_result?.friction_label ?? "pending"}
                      </Badge>
                    </div>
                    <p className="mt-3 text-sm font-semibold text-foreground">{heading}</p>
                    <p className="mt-2 text-sm leading-7 text-muted-foreground">
                      {result.clause_change.semantic_summary}
                    </p>
                  </button>
                );
              })}
            </div>
          ) : (
            <EmptyState text="Launch a run to populate the clause review queue." />
          )}
        </Card>

        <Card className="space-y-5" padding="lg">
          <SectionHeader
            eyebrow="Clause Detail"
            title={
              selectedResult
                ? selectedResult.revised_clause?.heading ??
                  selectedResult.original_clause?.heading ??
                  "Selected clause"
                : "Review detail"
            }
            description="Inspect the original language, revised language, evidence, and simulated response."
          />

          {selectedResult ? (
            <>
              <div className="flex flex-wrap gap-2">
                <Badge variant="decision">{selectedResult.simulation_result?.decision ?? "pending"}</Badge>
                <Badge variant="neutral">
                  {selectedResult.clause_change.issue_type.replaceAll("_", " ")}
                </Badge>
                <Badge variant={frictionVariant(selectedResult.scoring_result?.friction_label)}>
                  {selectedResult.scoring_result?.friction_label ?? "pending"}
                </Badge>
              </div>

              <p className="text-sm leading-7 text-muted-foreground">
                {selectedResult.clause_change.semantic_summary}
              </p>

              <div className="grid gap-4 xl:grid-cols-2">
                <ClausePanel
                  title="Original clause"
                  text={selectedResult.original_clause?.text ?? "No original clause"}
                />
                <ClausePanel
                  title="Revised clause"
                  text={selectedResult.revised_clause?.text ?? "No revised clause"}
                />
              </div>

              <div className="grid gap-4 xl:grid-cols-[1.08fr_0.92fr]">
                <Card tone="muted" className="space-y-4 rounded-[22px] p-5">
                  <PanelTitle icon={BotMessageSquare} title="Opposing counsel response" />
                  <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                    Confidence {selectedResult.simulation_result?.confidence ?? "–"}
                  </p>
                  <p className="text-sm leading-7 text-foreground">
                    {selectedResult.simulation_result?.business_reason ?? "Awaiting simulation output."}
                  </p>
                  <p className="text-sm leading-7 text-muted-foreground">
                    {selectedResult.simulation_result?.legal_reason ?? "Awaiting rationale."}
                  </p>

                  <Card tone="inset" className="rounded-[18px] p-5">
                    <p className="text-sm font-semibold text-foreground">Counterproposal</p>
                    <p className="mt-3 text-sm leading-7 text-muted-foreground">
                      {selectedResult.simulation_result?.counterproposal_text ?? "No counterproposal yet."}
                    </p>
                  </Card>

                  <div className="space-y-2">
                    <p className="text-sm font-semibold text-foreground">Pushback points</p>
                    {(selectedResult.simulation_result?.pushback_points ?? []).length ? (
                      <div className="space-y-2">
                        {(selectedResult.simulation_result?.pushback_points ?? []).map((point, index) => (
                          <Card
                            key={`${selectedResult.clause_change.id}-${index}`}
                            tone="inset"
                            padding="sm"
                            className="rounded-[16px]"
                          >
                            <p className="text-sm leading-6 text-muted-foreground">{point}</p>
                          </Card>
                        ))}
                      </div>
                    ) : (
                      <EmptyState text="No pushback points were generated for this clause." compact />
                    )}
                  </div>
                </Card>

                <div className="space-y-4">
                  <Card tone="muted" className="space-y-4 rounded-[22px] p-5">
                    <PanelTitle icon={ShieldCheck} title="Scoring" />
                    <div className="grid grid-cols-2 gap-3">
                      <StatTile
                        label="Pushback"
                        value={String(selectedResult.scoring_result?.pushback_probability ?? "–")}
                      />
                      <StatTile
                        label="Friction"
                        value={String(selectedResult.scoring_result?.negotiation_friction ?? "–")}
                      />
                      <StatTile
                        label="Delay"
                        value={String(selectedResult.scoring_result?.delay_risk ?? "–")}
                      />
                      <StatTile
                        label="Severity"
                        value={String(selectedResult.scoring_result?.severity ?? "–")}
                      />
                    </div>
                    <p className="text-sm leading-7 text-muted-foreground">
                      {selectedResult.scoring_result?.explanation ?? "Awaiting scoring explanation."}
                    </p>
                  </Card>

                  <Card tone="muted" className="space-y-4 rounded-[22px] p-5">
                    <PanelTitle icon={FileStack} title="Evidence citations" />
                    <div className="space-y-3">
                      {selectedResult.retrieval_hits.length ? (
                        selectedResult.retrieval_hits.slice(0, 3).map((hit) => (
                          <Card key={hit.id} tone="inset" className="rounded-[18px]">
                            <p className="text-sm font-semibold text-foreground">{hit.evidence_source.title}</p>
                            <p className="mt-1 text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                              {hit.evidence_source.section_label}
                            </p>
                            <p className="mt-3 text-sm leading-7 text-muted-foreground">{hit.snippet_text}</p>
                          </Card>
                        ))
                      ) : (
                        <EmptyState text="No evidence hits were stored for this clause." compact />
                      )}
                    </div>
                  </Card>
                </div>
              </div>
            </>
          ) : (
            <EmptyState text="Select a clause from the review queue to inspect the redline, rationale, evidence, and counterproposal." />
          )}
        </Card>

        <Card className="space-y-4" padding="lg">
          <SectionHeader
            eyebrow="Dossier"
            title="Persona and workflow"
            description="Operational context for the current matter, run, and workflow trace."
          />

          <Card tone="muted" className="space-y-4 rounded-[22px] p-5">
            <PanelTitle icon={BriefcaseBusiness} title="Matter profile" />
            <div className="space-y-3">
              <SummaryRow label="Matter" value={contractName || "Untitled matter"} />
              <SummaryRow
                label="Persona"
                value={selectedPersona?.name ?? demoBundle?.persona.name ?? "Not selected"}
              />
              <SummaryRow
                label="Run id"
                value={
                  demoBundle?.runStatus.run.id
                    ? `${demoBundle.runStatus.run.id.slice(0, 8)}...`
                    : activeRunId
                      ? `${activeRunId.slice(0, 8)}...`
                      : "Not created"
                }
              />
            </div>
          </Card>

          <Card tone="muted" className="space-y-4 rounded-[22px] p-5">
            <PanelTitle icon={Workflow} title="Workflow trace" />
            <div className="space-y-2">
              {workflowLabels.map((label, index) => {
                const isActive = currentStageIndex >= 0 ? index <= currentStageIndex : label === currentStage;
                return (
                  <Card
                    key={label}
                    tone="inset"
                    padding="sm"
                    className={cn(
                      "flex items-center justify-between gap-3 rounded-[16px]",
                      isActive && "border-ring/25 bg-accent/45",
                    )}
                  >
                    <span className="text-sm capitalize text-foreground">{label.replace("_", " ")}</span>
                    <Badge variant={isActive ? "decision" : "neutral"}>
                      {isActive ? "tracked" : "idle"}
                    </Badge>
                  </Card>
                );
              })}
            </div>
          </Card>

          <Card tone="muted" className="space-y-4 rounded-[22px] p-5">
            <PanelTitle icon={Gavel} title="Product posture" />
            <div className="space-y-2 text-sm leading-7 text-muted-foreground">
              <p>Clause changes are analyzed individually rather than through one document-level chat prompt.</p>
              <p>
                Issue classification is heuristic first, with model fallback available through structured
                adapters.
              </p>
              <p>Evidence hits are persisted so the review UI can show why the simulator took a given stance.</p>
            </div>
          </Card>
        </Card>
      </section>
    </main>
  );
}

function SectionHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="space-y-2">
      <p className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
        {eyebrow}
      </p>
      <div className="space-y-2">
        <h2 className="text-2xl font-semibold text-foreground">{title}</h2>
        {description ? <p className="max-w-3xl text-sm leading-7 text-muted-foreground">{description}</p> : null}
      </div>
    </div>
  );
}

function PanelTitle({
  icon: Icon,
  title,
}: {
  icon: typeof FileStack;
  title: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-border/80 bg-background/70 text-foreground">
        <Icon className="h-4 w-4" />
      </div>
      <p className="text-sm font-semibold text-foreground">{title}</p>
    </div>
  );
}

function FieldLabel({
  children,
  htmlFor,
}: {
  children: ReactNode;
  htmlFor?: string;
}) {
  return (
    <label htmlFor={htmlFor} className="text-sm font-semibold text-foreground">
      {children}
    </label>
  );
}

function QuickStat({ label, value }: { label: string; value: string }) {
  return (
    <Card tone="inset" padding="sm" className="rounded-[18px] bg-background/36">
      <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-2 text-sm font-semibold text-foreground">{value}</p>
    </Card>
  );
}

function UploadControl({
  label,
  helper,
  fileName,
  children,
}: {
  label: string;
  helper: string;
  fileName: string | null;
  children: ReactNode;
}) {
  return (
    <Card tone="inset" padding="sm" className="space-y-3 rounded-[18px] bg-background/42">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            {label}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">{helper}</p>
        </div>
        {fileName ? <Badge variant="neutral">{fileName}</Badge> : null}
      </div>
      {children}
    </Card>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  supporting,
}: {
  icon: typeof FileStack;
  label: string;
  value: string | number;
  supporting: string;
}) {
  return (
    <Card className="flex min-h-[166px] flex-col justify-between rounded-[24px] p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-border/80 bg-background/60 text-foreground">
          <Icon className="h-4 w-4" />
        </div>
        <p className="max-w-[160px] text-right text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          {supporting}
        </p>
      </div>
      <div className="mt-7 space-y-2">
        <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          {label}
        </p>
        <p className="text-[2rem] font-semibold tracking-tight text-foreground">{value}</p>
      </div>
    </Card>
  );
}

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <Card tone="inset" padding="sm" className="rounded-[16px]">
      <p className="text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-2 text-sm font-semibold text-foreground">{value}</p>
    </Card>
  );
}

function PersonaScale({ label, value }: { label: string; value: number }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-foreground">{label}</p>
        <p className="text-sm font-semibold text-foreground">{value}/5</p>
      </div>
      <div className="grid grid-cols-5 gap-1.5">
        {Array.from({ length: 5 }).map((_, index) => (
          <div
            key={`${label}-${index}`}
            className={cn(
              "h-2.5 rounded-full border transition-colors",
              index < value
                ? "border-ring/25 bg-foreground/85"
                : "border-border/70 bg-background/70",
            )}
          />
        ))}
      </div>
    </div>
  );
}

function ClausePanel({ title, text }: { title: string; text: string }) {
  return (
    <Card tone="muted" className="rounded-[20px]">
      <p className="text-sm font-semibold text-foreground">{title}</p>
      <p className="mt-3 text-sm leading-7 text-muted-foreground">{text}</p>
    </Card>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <Card tone="inset" padding="sm" className="flex items-center justify-between gap-3 rounded-[16px]">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="max-w-[60%] break-all text-right text-sm font-semibold text-foreground">{value}</span>
    </Card>
  );
}

function StatusPanel({ tone, text }: { tone: "error" | "success"; text: string }) {
  return (
    <div
      className={cn(
        "rounded-[18px] border px-4 py-3 text-sm leading-6",
        tone === "error" && "border-rose-500/30 bg-rose-500/12 text-rose-100",
        tone === "success" && "border-emerald-500/30 bg-emerald-500/12 text-emerald-100",
      )}
    >
      {text}
    </div>
  );
}

function EmptyState({ text, compact = false }: { text: string; compact?: boolean }) {
  return (
    <Card
      tone="ghost"
      className={cn(
        "border-dashed bg-background/20 text-muted-foreground",
        compact ? "rounded-[18px] p-4 text-sm leading-6" : "rounded-[20px] p-8 text-sm leading-7",
      )}
    >
      {text}
    </Card>
  );
}
