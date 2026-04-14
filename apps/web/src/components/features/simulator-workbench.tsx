"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { type ReactNode, useEffect, useMemo, useState } from "react";

import {
  createRun,
  fetchClauseResults,
  fetchPersonas,
  fetchRunSummary,
  uploadDocument,
} from "@/lib/api";
import { demoDefaultPersonaSlug, demoPersonas } from "@/lib/demo-data";
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

export function SimulatorWorkbench() {
  const personasQuery = useQuery({ queryKey: ["personas"], queryFn: fetchPersonas });

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
    { label: "Customer Playbook", type: "playbook",  text: "", file: null, uploadedVersionId: null },
    { label: "Vendor Precedent",  type: "precedent", text: "", file: null, uploadedVersionId: null },
    { label: "Fallback Clauses",  type: "fallback",  text: "", file: null, uploadedVersionId: null },
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
    () => availablePersonas.find((p) => p.id === selectedPersonaId) ?? null,
    [availablePersonas, selectedPersonaId],
  );
  const runSummaryData = demoBundle?.runSummary ?? runSummaryQuery.data ?? null;
  const reviewResults = useMemo(
    () => demoBundle?.clauseResults.results ?? clauseResultsQuery.data?.results ?? [],
    [clauseResultsQuery.data, demoBundle],
  );
  const selectedResult = useMemo(
    () => reviewResults.find((r) => r.clause_change.id === selectedClauseId) ?? reviewResults[0] ?? null,
    [reviewResults, selectedClauseId],
  );

  const uploadMutation    = useMutation({ mutationFn: uploadDocument });
  const createRunMutation = useMutation({
    mutationFn: createRun,
    onSuccess: (result) => { setDemoBundle(null); setActiveRunId(result.run.id); },
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
        { label: "Customer Playbook", type: "playbook",  text: result.evidenceDocuments[0]?.text ?? "", file: null, uploadedVersionId: result.evidenceDocuments[0]?.uploadedVersionId ?? null },
        { label: "Vendor Precedent",  type: "precedent", text: result.evidenceDocuments[1]?.text ?? "", file: null, uploadedVersionId: result.evidenceDocuments[1]?.uploadedVersionId ?? null },
        { label: "Fallback Clauses",  type: "fallback",  text: result.evidenceDocuments[2]?.text ?? "", file: null, uploadedVersionId: result.evidenceDocuments[2]?.uploadedVersionId ?? null },
      ]);
    },
  });

  const uiError =
    (uploadMutation.error as Error | null)?.message ??
    (createRunMutation.error as Error | null)?.message ??
    (demoRunMutation.error as Error | null)?.message ??
    (runStatusQuery.error as Error | null)?.message ??
    null;

  useEffect(() => {
    if (!reviewResults.length) { setSelectedClauseId(null); return; }
    if (!selectedClauseId || !reviewResults.some((r) => r.clause_change.id === selectedClauseId)) {
      setSelectedClauseId(reviewResults[0].clause_change.id);
    }
  }, [reviewResults, selectedClauseId]);

  async function uploadContractsAndEvidence() {
    setDemoBundle(null);
    const original = await uploadMutation.mutateAsync({ path: "/api/documents/original", name: `${contractName} Original`, textContent: originalText, file: originalFile });
    const revised  = await uploadMutation.mutateAsync({ path: "/api/documents/revised",  name: `${contractName} Revised`,  textContent: revisedText,  file: revisedFile  });
    const next = [...evidenceDrafts];
    for (let i = 0; i < next.length; i++) {
      const d = next[i];
      if (!d.text.trim() && !d.file) continue;
      const up = await uploadMutation.mutateAsync({ path: "/api/documents/evidence", name: d.label, textContent: d.text, evidenceType: d.type, file: d.file });
      next[i] = { ...d, uploadedVersionId: up.version.id };
    }
    setEvidenceDrafts(next);
    setOriginalUpload(original);
    setRevisedUpload(revised);
  }

  async function runAnalysis() {
    if (!selectedPersonaId || !originalUpload || !revisedUpload) return;
    setDemoBundle(null); setActiveRunId(null); setSelectedClauseId(null);
    await createRunMutation.mutateAsync({
      original_document_version_id: originalUpload.version.id,
      revised_document_version_id:  revisedUpload.version.id,
      persona_id: selectedPersonaId,
      evidence_document_version_ids: evidenceDrafts.map((d) => d.uploadedVersionId).filter((v): v is string => Boolean(v)),
      run_async: false,
    });
  }

  async function runDemoFlow() {
    setActiveRunId(null); setSelectedClauseId(null);
    await demoRunMutation.mutateAsync();
  }

  const overview = runSummaryData?.overview;

  return (
    <main className="mx-auto max-w-[1680px] px-4 py-8 md:px-8">

      {/* Header */}
      <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Opposing Counsel Simulator</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Clause-level contract negotiation review. No backend required for demo.
          </p>
        </div>
        <Button onClick={runDemoFlow} disabled={demoRunMutation.isPending}>
          {demoRunMutation.isPending ? "Running..." : "Run Demo"}
        </Button>
      </header>

      {/* Metrics */}
      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Metric label="Changed clauses"  value={overview?.total_changed_clauses  ?? "–"} />
        <Metric label="Likely pushback"  value={overview?.likely_pushback_count  ?? "–"} />
        <Metric label="High friction"    value={overview?.high_friction_clauses  ?? "–"} />
        <Metric label="Difficulty"       value={formatDifficulty(overview?.overall_negotiation_difficulty)} />
      </div>

      {/* Main */}
      <div className="grid gap-5 xl:grid-cols-[340px_1fr]">

        {/* ── Setup panel ── */}
        <Card padding="lg" className="space-y-6">

          <Section label="Contracts">
            <div className="space-y-2">
              <Label htmlFor="contract-name">Matter name</Label>
              <Input id="contract-name" value={contractName} onChange={(e) => setContractName(e.target.value)} placeholder="Cloud Platform MSA" />
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <ContractInput
                label="Original" badge={<Badge variant="neutral">Baseline</Badge>}
                file={originalFile} onFile={setOriginalFile}
                text={originalText} onText={setOriginalText}
                placeholder="Paste original contract text."
              />
              <ContractInput
                label="Revised" badge={<Badge variant="decision">Redline</Badge>}
                file={revisedFile} onFile={setRevisedFile}
                text={revisedText} onText={setRevisedText}
                placeholder="Paste revised contract text."
              />
            </div>

            <Button
              onClick={uploadContractsAndEvidence}
              disabled={((!originalText.trim() && !originalFile) || (!revisedText.trim() && !revisedFile)) || uploadMutation.isPending}
            >
              {uploadMutation.isPending ? "Uploading..." : "Upload contracts"}
            </Button>
          </Section>

          <div className="border-t border-border/50" />

          <Section label="Evidence">
            <p className="text-sm text-muted-foreground">Optional — paste playbook, precedent, or fallback clauses to ground retrieval.</p>
            {evidenceDrafts.map((draft, i) => (
              <div key={draft.type} className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label>{draft.label}</Label>
                  <Badge variant={draft.uploadedVersionId ? "low" : "neutral"} className="text-xs">
                    {draft.uploadedVersionId ? "Indexed" : "Optional"}
                  </Badge>
                </div>
                <Textarea
                  className="min-h-20 text-xs"
                  value={draft.text}
                  onChange={(e) => setEvidenceDrafts((cur) => cur.map((item, j) => j === i ? { ...item, text: e.target.value, uploadedVersionId: null } : item))}
                  placeholder={`Paste ${draft.label.toLowerCase()}.`}
                />
              </div>
            ))}
          </Section>

          <div className="border-t border-border/50" />

          <Section label="Counsel persona">
            <Select value={selectedPersonaId} onChange={(e) => setSelectedPersonaId(e.target.value)}>
              <option value="">Select a persona</option>
              {availablePersonas.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </Select>

            {selectedPersona && (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">{selectedPersona.description}</p>
                <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                  <span>Leverage {selectedPersona.leverage}/5</span>
                  <span>·</span>
                  <span>Strictness {selectedPersona.liability_strictness}/5</span>
                  <span>·</span>
                  <span>Speed {selectedPersona.speed_priority}/5</span>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Button
                onClick={runAnalysis}
                disabled={!selectedPersonaId || !originalUpload || !revisedUpload || createRunMutation.isPending}
                className="w-full"
              >
                {createRunMutation.isPending ? "Running analysis..." : "Run analysis"}
              </Button>
              <Button variant="secondary" onClick={runDemoFlow} disabled={demoRunMutation.isPending} className="w-full">
                {demoRunMutation.isPending ? "Running demo..." : "Run Demo"}
              </Button>
            </div>

            {uiError && <StatusBanner tone="error" text={uiError} />}
            {!uiError && demoBundle?.message && <StatusBanner tone="success" text={demoBundle.message} />}
          </Section>

        </Card>

        {/* ── Results panel ── */}
        <div className="grid gap-5 xl:grid-cols-[260px_1fr]">

          {/* Queue */}
          <Card padding="lg" className="space-y-3">
            <p className="text-sm font-semibold text-foreground">Changed clauses</p>
            {reviewResults.length ? (
              <div className="space-y-2">
                {reviewResults.map((result) => {
                  const isSelected = result.clause_change.id === selectedResult?.clause_change.id;
                  const heading = result.revised_clause?.heading ?? result.original_clause?.heading ?? "Clause";
                  return (
                    <button
                      key={result.clause_change.id}
                      type="button"
                      onClick={() => setSelectedClauseId(result.clause_change.id)}
                      className={cn(
                        "w-full rounded-xl border px-3 py-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                        isSelected
                          ? "border-ring/30 bg-accent/60"
                          : "border-border/60 bg-background/20 hover:border-border hover:bg-muted/40",
                      )}
                    >
                      <div className="flex flex-wrap gap-1.5">
                        <Badge variant="decision" className="text-xs">{result.clause_change.issue_type.replaceAll("_", " ")}</Badge>
                        <Badge variant={frictionVariant(result.scoring_result?.friction_label)} className="text-xs">
                          {result.scoring_result?.friction_label ?? "pending"}
                        </Badge>
                      </div>
                      <p className="mt-2 text-sm font-medium text-foreground">{heading}</p>
                    </button>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Run a demo to populate the queue.</p>
            )}
          </Card>

          {/* Detail */}
          <Card padding="lg">
            {selectedResult ? (
              <div className="space-y-6">

                {/* Status badges */}
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="decision">{selectedResult.simulation_result?.decision ?? "pending"}</Badge>
                  <Badge variant="neutral">{selectedResult.clause_change.issue_type.replaceAll("_", " ")}</Badge>
                  <Badge variant={frictionVariant(selectedResult.scoring_result?.friction_label)}>
                    {selectedResult.scoring_result?.friction_label ?? "pending"}
                  </Badge>
                  <span className="ml-auto text-xs text-muted-foreground">
                    Confidence {selectedResult.simulation_result?.confidence ?? "–"}
                  </span>
                </div>

                <p className="text-sm leading-7 text-muted-foreground">
                  {selectedResult.clause_change.semantic_summary}
                </p>

                {/* Clause text */}
                <div className="grid gap-4 sm:grid-cols-2">
                  <ClauseText label="Original" text={selectedResult.original_clause?.text ?? "—"} />
                  <ClauseText label="Revised"  text={selectedResult.revised_clause?.text  ?? "—"} />
                </div>

                <div className="border-t border-border/50" />

                {/* Simulation response */}
                <div className="space-y-3">
                  <p className="text-sm font-semibold text-foreground">Opposing counsel response</p>
                  <p className="text-sm leading-7 text-foreground">
                    {selectedResult.simulation_result?.business_reason ?? "—"}
                  </p>
                  <p className="text-sm leading-7 text-muted-foreground">
                    {selectedResult.simulation_result?.legal_reason ?? "—"}
                  </p>
                </div>

                {/* Counterproposal */}
                {selectedResult.simulation_result?.counterproposal_text && (
                  <Card tone="muted" padding="sm" className="space-y-2 rounded-xl">
                    <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Counterproposal</p>
                    <p className="text-sm leading-7">{selectedResult.simulation_result.counterproposal_text}</p>
                  </Card>
                )}

                {/* Pushback points */}
                {(selectedResult.simulation_result?.pushback_points ?? []).length > 0 && (
                  <div className="space-y-1.5">
                    <p className="text-sm font-semibold text-foreground">Pushback points</p>
                    {(selectedResult.simulation_result?.pushback_points ?? []).map((point, i) => (
                      <p key={i} className="pl-3 text-sm leading-7 text-muted-foreground border-l-2 border-border/50">
                        {point}
                      </p>
                    ))}
                  </div>
                )}

                <div className="border-t border-border/50" />

                {/* Scores */}
                <div className="grid grid-cols-4 gap-2">
                  <ScoreTile label="Pushback" value={String(selectedResult.scoring_result?.pushback_probability ?? "–")} />
                  <ScoreTile label="Friction"  value={String(selectedResult.scoring_result?.negotiation_friction  ?? "–")} />
                  <ScoreTile label="Delay"     value={String(selectedResult.scoring_result?.delay_risk            ?? "–")} />
                  <ScoreTile label="Severity"  value={String(selectedResult.scoring_result?.severity              ?? "–")} />
                </div>

                {/* Evidence */}
                {selectedResult.retrieval_hits.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-semibold text-foreground">Evidence</p>
                    {selectedResult.retrieval_hits.slice(0, 3).map((hit) => (
                      <div key={hit.id} className="border-l-2 border-border/50 pl-3">
                        <p className="text-xs font-semibold text-muted-foreground">
                          {hit.evidence_source.title} · {hit.evidence_source.section_label}
                        </p>
                        <p className="mt-1 text-sm leading-6 text-muted-foreground">{hit.snippet_text}</p>
                      </div>
                    ))}
                  </div>
                )}

              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Select a clause to review the redline, rationale, and counterproposal.</p>
            )}
          </Card>

        </div>
      </div>
    </main>
  );
}

// ─── Small helpers ────────────────────────────────────────────────────────────

function Section({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-4">
      <p className="text-sm font-semibold text-foreground">{label}</p>
      {children}
    </div>
  );
}

function Label({ children, htmlFor }: { children: ReactNode; htmlFor?: string }) {
  return (
    <label htmlFor={htmlFor} className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
      {children}
    </label>
  );
}

function ContractInput({
  label, badge, file, onFile, text, onText, placeholder,
}: {
  label: string; badge: ReactNode;
  file: File | null; onFile: (f: File | null) => void;
  text: string; onText: (t: string) => void;
  placeholder: string;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label>{label}</Label>
        {badge}
      </div>
      {file && <p className="text-xs text-muted-foreground">{file.name}</p>}
      <Input type="file" accept=".txt,.docx,.pdf" onChange={(e) => onFile(e.target.files?.[0] ?? null)} />
      <Textarea
        className="min-h-40 text-xs"
        value={text}
        onChange={(e) => onText(e.target.value)}
        placeholder={placeholder}
      />
    </div>
  );
}

function ClauseText({ label, text }: { label: string; text: string }) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="text-sm leading-7 text-foreground">{text}</p>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <Card padding="sm" className="space-y-1 rounded-xl p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-2xl font-semibold text-foreground">{value}</p>
    </Card>
  );
}

function ScoreTile({ label, value }: { label: string; value: string }) {
  return (
    <Card tone="muted" padding="sm" className="space-y-1 rounded-xl">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-semibold text-foreground">{value}</p>
    </Card>
  );
}

function StatusBanner({ tone, text }: { tone: "error" | "success"; text: string }) {
  return (
    <div className={cn(
      "rounded-xl border px-3 py-2 text-sm",
      tone === "error"   && "border-rose-500/30 bg-rose-500/10 text-rose-200",
      tone === "success" && "border-emerald-500/30 bg-emerald-500/10 text-emerald-200",
    )}>
      {text}
    </div>
  );
}
