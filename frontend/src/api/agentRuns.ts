import { apiDelete, apiGet } from "./client";

export interface AgentRunRecord {
  run_id: string;
  import_id?: string | null;
  source_name?: string;
  status: string;
  uploaded_count: number;
  valid_count: number;
  warning_count: number;
  invalid_count: number;
  scoring_results: Array<{
    competitor_name?: string;
    domain?: string;
    preliminary_score?: number;
    max_score?: number;
    priority?: string;
    reasons?: string[];
    missing_data?: string[];
    evidence_count?: number;
    breakdown?: { review_pain?: number; seo_gap?: number; product_overlap?: number; recency?: number };
  }>;
  research_targets: Array<{ competitor_name?: string; domain?: string; preliminary_score?: number }>;
  research_results: Array<{ competitor_name?: string; status?: string; sources?: Array<{ url?: string; title?: string }> }>;
  source_urls: string[];
  battlecard_ids: number[];
  errors: string[];
  created_at: string;
  completed_at?: string | null;
}

export async function getAgentRuns(): Promise<AgentRunRecord[]> {
  const response = await apiGet<unknown>("/agent/runs", { limit: 200 });
  if (Array.isArray(response)) return response as AgentRunRecord[];
  return [];
}

export async function deleteAgentRun(runId: string): Promise<void> {
  await apiDelete(`/agent/runs/${encodeURIComponent(runId)}`);
}
