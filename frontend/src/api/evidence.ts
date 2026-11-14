import { apiGet } from "./client";
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
export async function getEvidence(domain?: string): Promise<Evidence[]> {
  return unwrapList<Evidence>(await apiGet<unknown>("/evidence/", { limit: 100, domain }));
}
export async function getEvidenceSummary(domain: string) {
  return apiGet<Record<string, unknown>>(`/evidence/summary/${encodeURIComponent(domain)}`);
}
