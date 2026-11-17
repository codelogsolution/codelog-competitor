export interface EvidenceRecord {
  id: number;
  competitor_name: string;
  domain: string;
  source_type: string;
  source_url: string;
  category: string;
  signal_type: string;
  signal_text: string;
  signal_date?: string;
  sentiment?: string;
  frequency?: number;
  keyword_gap?: string;
  keyword_volume?: number | null;
  ranking_gap?: number | null;
  product_area?: string;
  status?: string;
  created_at?: string;
}
export interface CompetitorRecord {
  domain: string;
  competitor_name: string;
  evidence: EvidenceRecord[];
}
export interface BattlecardRecord {
  id: number;
  competitor_name: string;
  domain: string;
  status: string;
  content: Record<string, unknown> | string;
  evidence_urls?: string[] | string;
  created_at?: string;
}
export interface ApprovalRecord {
  id: number;
  competitor_name?: string;
  domain?: string;
  status: string;
  [key: string]: unknown;
}
export interface AuditRecord {
  id?: number;
  action?: string;
  entity_type?: string;
  entity_id?: number;
  previous_status?: string;
  new_status?: string;
  actor?: string;
  comment?: string;
  created_at?: string;
}
