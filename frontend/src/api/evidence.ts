import { apiDelete, apiGet, apiPost } from "./client";
import type { EvidenceRecord } from "../types";

export type Evidence = EvidenceRecord;
function unwrapList<T>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[];
  if (value && typeof value === "object") {
    const obj = value as { items?: T[]; results?: T[]; records?: T[] };
    return obj.items ?? obj.results ?? obj.records ?? [];
  }
  return [];
}
export async function getEvidence(domain?: string, runId?: string): Promise<Evidence[]> {
  return unwrapList<Evidence>(await apiGet<unknown>("/evidence/", { limit: 1000, domain, run_id: runId }));
}
export async function getEvidenceSummary(domain: string) {
  return apiGet<Record<string, unknown>>(`/evidence/summary/${encodeURIComponent(domain)}`);
}

export async function deleteEvidence(id: number) {
  return apiDelete(`/evidence/${id}`);
}

export async function deleteEvidenceByDomain(domain: string) {
  return apiDelete(`/evidence/domain/${encodeURIComponent(domain)}`);
}

export async function resolveWarningEvidence(
  id: number,
  decision: "confirm_valid" | "mark_invalid",
  comment = "",
  sourceUrl = "",
) {
  return apiPost(`/evidence/${id}/resolve`, {
    decision,
    actor: "workspace_reviewer",
    comment,
    source_url: sourceUrl || undefined,
  });
}
