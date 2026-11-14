import { getEvidence, type Evidence } from "./evidence";
import type { CompetitorRecord } from "../types";
export type Competitor = CompetitorRecord;
export async function getCompetitors(): Promise<Competitor[]> {
  const records: Evidence[] = await getEvidence();
  const grouped = new Map<string, Evidence[]>();
  for (const record of records) {
    const key = record.domain || "unknown";
    grouped.set(key, [...(grouped.get(key) ?? []), record]);
  }
  return [...grouped.entries()].map(([domain, evidence]) => ({
    domain, competitor_name: evidence[0]?.competitor_name ?? domain, evidence,
  }));
}
