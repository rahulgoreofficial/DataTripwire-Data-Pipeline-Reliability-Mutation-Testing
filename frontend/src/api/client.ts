/**
 * DataTripwire API client.
 *
 * All communication with the FastAPI backend is centralized here.
 * Base URL is configurable via the VITE_API_BASE_URL env variable.
 */

import type {
  DatasetResponse,
  EvaluationCreateRequest,
  EvaluationReport,
  EvaluationSummaryItem,
  HealthResponse,
} from "../types/api";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  let res: Response;
  try {
    res = await fetch(url, {
      headers: {
        Accept: "application/json",
        ...(init?.headers ?? {}),
      },
      ...init,
    });
  } catch (err: unknown) {
    if (
      err instanceof TypeError &&
      (err.message.includes("fetch") ||
        err.message.includes("network") ||
        err.message.includes("Load failed") ||
        err.message.includes("NetworkError"))
    ) {
      throw new Error(
        `Unable to reach DataTripwire backend at ${BASE_URL}. Ensure the backend server is running and accessible.`
      );
    }
    throw err;
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = (await res.json()) as { detail?: string; error?: string };
      detail = body.detail ?? body.error ?? detail;
    } catch {
      // ignore parse error
    }
    throw new Error(detail);
  }

  return res.json() as Promise<T>;
}

// ─── Health ───────────────────────────────────────────────────────────────────

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

// ─── Datasets ─────────────────────────────────────────────────────────────────

export async function loadSampleDataset(): Promise<DatasetResponse> {
  return request<DatasetResponse>("/api/v1/datasets/sample", { method: "POST" });
}

export async function loadSampleManufacturingDataset(): Promise<DatasetResponse> {
  return request<DatasetResponse>("/api/v1/datasets/sample-manufacturing", { method: "POST" });
}

export async function getDomains(): Promise<any[]> {
  return request<any[]>("/api/v1/domains");
}

export async function uploadDataset(file: File): Promise<DatasetResponse> {
  const form = new FormData();
  form.append("file", file);
  return request<DatasetResponse>("/api/v1/datasets", {
    method: "POST",
    body: form,
  });
}

export async function listDatasets(): Promise<DatasetResponse[]> {
  return request<DatasetResponse[]>("/api/v1/datasets");
}

export async function getDataset(datasetId: string): Promise<DatasetResponse> {
  return request<DatasetResponse>(`/api/v1/datasets/${datasetId}`);
}

export async function listDatasetEvaluations(datasetId: string): Promise<EvaluationSummaryItem[]> {
  return request<EvaluationSummaryItem[]>(`/api/v1/datasets/${datasetId}/evaluations`);
}

// ─── Evaluations ──────────────────────────────────────────────────────────────

export async function runEvaluation(
  datasetId: string,
  payload: EvaluationCreateRequest
): Promise<EvaluationReport> {
  return request<EvaluationReport>(`/api/v1/datasets/${datasetId}/evaluations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getEvaluationReport(evaluationId: string): Promise<EvaluationReport> {
  return request<EvaluationReport>(`/api/v1/evaluations/${evaluationId}`);
}
