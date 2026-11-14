import { apiPost } from "./client";

export interface UploadResult {
  success: boolean;
  filename?: string;
  total_records: number;
  valid_records: number;
  invalid_records: number;
  warning_records?: number;
  errors?: Array<string | Record<string, unknown>>;
  records: Array<Record<string, unknown>>;
}

export interface AgentResult {
  status: string;
  scoring_results: Array<{
    competitor_name: string;
    domain: string;
    preliminary_score: number;
    max_score: number;
    priority: string;
    evidence_count?: number;
    reasons?: string[];
  }>;
  research_results: unknown[];
  evidence_results: unknown[];
  battlecard_results: unknown[];
  errors: string[];
}

export async function uploadCompetitorFile(file: File): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file);
  return apiPost<UploadResult>("/uploads", form);
}

export async function runCompetitorAgent(records: Array<Record<string, unknown>>) {
  return apiPost<AgentResult>("/agent/run", { records });
}
