import { apiPost, apiStreamPost } from "./client";

export interface UploadResult {
  success: boolean;
  import_id?: string;
  original_filename?: string;
  stored_filename?: string;
  filename?: string;
  total_records: number;
  valid_records: number;
  invalid_records: number;
  warning_records?: number;
  errors?: Array<string | Record<string, unknown>>;
  warnings?: Array<string | Record<string, unknown>>;
  records: Array<Record<string, unknown>>;
}

export interface AgentResult {
  run_id?: string;
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
  research_results: Array<{
    competitor_name?: string;
    domain?: string;
    status?: string;
    message?: string;
    sources?: Array<{ title?: string; url?: string; content?: string }>;
  }>;
  evidence_results: unknown[];
  battlecard_results: unknown[];
  errors: string[];
}

export interface AgentProgressEvent {
  type: "started" | "progress" | "completed" | "failed";
  run_id?: string;
  stage?: string;
  status?: "started" | "completed" | "skipped";
  message?: string;
  result?: AgentResult;
}

export async function uploadCompetitorFile(file: File): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file);
  return apiPost<UploadResult>("/uploads", form);
}

export async function runCompetitorAgent(
  records: Array<Record<string, unknown>>,
  onProgress: (event: AgentProgressEvent) => void,
  importId?: string,
  sourceName?: string,
) {
  return apiStreamPost<AgentResult, AgentProgressEvent>("/agent/run/stream", {
    records,
    import_id: importId,
    source_name: sourceName,
  }, onProgress);
}
