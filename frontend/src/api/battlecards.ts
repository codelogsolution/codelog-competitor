import { apiDelete, apiGet } from "./client";
import type { BattlecardRecord } from "../types";
export type Battlecard = BattlecardRecord;
export interface BattlecardContent {
  overview?: string; positioning?: string; strengths?: string[]; weaknesses?: string[];
  product_gaps?: string[]; pricing?: string; opportunities?: string[];
  threat_level?: string; recommended_actions?: string[]; evidence_notes?: string[];
}
function unwrapList<T>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[];
  if (value && typeof value === "object") {
    const obj = value as { items?: T[]; results?: T[]; records?: T[] };
    return obj.items ?? obj.results ?? obj.records ?? [];
  }
  return [];
}
export async function getBattlecards(): Promise<Battlecard[]> {
  return unwrapList<Battlecard>(await apiGet<unknown>("/battlecards/"));
}
export async function getBattlecard(id: number | string): Promise<Battlecard> {
  return apiGet<Battlecard>(`/battlecards/${id}`);
}

export async function deleteBattlecard(id: number | string) {
  return apiDelete(`/battlecards/${id}`);
}
