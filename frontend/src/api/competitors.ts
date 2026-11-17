import { apiDelete } from "./client";
import { getEvidence, type Evidence } from "./evidence";
import type { CompetitorRecord } from "../types";
export type Competitor = CompetitorRecord;
export async function getCompetitors(runId?: string): Promise<Competitor[]> {
  const records: Evidence[] = await getEvidence(undefined, runId);
  const grouped = new Map<string, Evidence[]>();
  for (const record of records) {
    const key = record.domain || "unknown";
    grouped.set(key, [...(grouped.get(key) ?? []), record]);
  }
  return [...grouped.entries()].map(([domain, evidence]) => ({
    domain, competitor_name: evidence[0]?.competitor_name ?? domain, evidence,
  }));
}

export async function deleteCompetitor(domain: string) {
  return apiDelete(`/evidence/domain/${encodeURIComponent(domain)}`);
}
