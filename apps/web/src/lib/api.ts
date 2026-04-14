import {
  clauseResultsResponseSchema,
  demoHappyPathResponseSchema,
  personaSchema,
  runAcceptedResponseSchema,
  runStatusResponseSchema,
  runSummaryResponseSchema,
  uploadDocumentResponseSchema,
  type ClauseResultsResponse,
  type DemoHappyPathResponse,
  type RunAcceptedResponse,
  type RunStatusResponse,
  type RunSummaryResponse,
  type UploadDocumentResponse,
  type Persona,
} from "@ocs/schemas";

import { demoPersonas } from "@/lib/demo-data";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function readPayload(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  const text = await response.text();
  return { detail: text || response.statusText };
}

async function request<T>(path: string, init: RequestInit, parser: { parse: (value: unknown) => T }): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, init);
  const payload = await readPayload(response);
  if (!response.ok) {
    const detail =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? String(payload.detail)
        : "Request failed";
    throw new Error(detail);
  }
  return parser.parse(payload);
}

export async function fetchPersonas(): Promise<Persona[]> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/personas`, { cache: "no-store" });
    const payload = await readPayload(response);
    if (!response.ok) {
      const detail =
        typeof payload === "object" && payload !== null && "detail" in payload
          ? String(payload.detail)
          : "Failed to load personas";
      throw new Error(detail);
    }
    return personaSchema.array().parse(payload);
  } catch {
    return demoPersonas;
  }
}

export async function uploadDocument(options: {
  path: "/api/documents/original" | "/api/documents/revised" | "/api/documents/evidence";
  name?: string;
  textContent?: string;
  file?: File | null;
  evidenceType?: string;
}): Promise<UploadDocumentResponse> {
  const formData = new FormData();
  if (options.name) {
    formData.append("name", options.name);
  }
  if (options.textContent) {
    formData.append("text_content", options.textContent);
  }
  if (options.file) {
    formData.append("file", options.file);
  }
  if (options.evidenceType) {
    formData.append("evidence_type", options.evidenceType);
  }
  return request(options.path, { method: "POST", body: formData }, uploadDocumentResponseSchema);
}

export async function createRun(payload: {
  original_document_version_id: string;
  revised_document_version_id: string;
  persona_id: string;
  evidence_document_version_ids: string[];
  run_async: boolean;
}): Promise<RunAcceptedResponse> {
  return request(
    "/api/runs",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    runAcceptedResponseSchema,
  );
}

export async function fetchRunStatus(runId: string): Promise<RunStatusResponse> {
  return request(`/api/runs/${runId}/status`, { method: "GET", cache: "no-store" }, runStatusResponseSchema);
}

export async function fetchRunSummary(runId: string): Promise<RunSummaryResponse> {
  return request(`/api/runs/${runId}/summary`, { method: "GET", cache: "no-store" }, runSummaryResponseSchema);
}

export async function fetchClauseResults(runId: string): Promise<ClauseResultsResponse> {
  return request(`/api/runs/${runId}/clauses`, { method: "GET", cache: "no-store" }, clauseResultsResponseSchema);
}

export async function bootstrapDemoHappyPath(payload?: {
  persona_slug?: string;
  run_async?: boolean;
}): Promise<DemoHappyPathResponse> {
  return request(
    "/api/demo/happy-path",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload ?? {}),
    },
    demoHappyPathResponseSchema,
  );
}
