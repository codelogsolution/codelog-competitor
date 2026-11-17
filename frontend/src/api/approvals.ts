import { apiGet, apiPost } from "./client";
import type { ApprovalRecord, AuditRecord } from "../types";
export type ApprovalItem = ApprovalRecord;
function unwrapList<T>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[];
  if (value && typeof value === "object") {
    const obj = value as { items?: T[]; results?: T[]; records?: T[] };
    return obj.items ?? obj.results ?? obj.records ?? [];
  }
  return [];
}
export async function getApprovals(): Promise<ApprovalItem[]> {
  return unwrapList<ApprovalItem>(await apiGet<unknown>("/approvals/"));
}
export async function submitApprovalAction(id: number, action: "approve" | "reject" | "request-changes" | "resubmit", comment = "") {
  return apiPost(`/approvals/${id}/${action}`, { comment });
}
export interface AuditLogPage {
  items: AuditRecord[];
  total: number;
  limit: number;
  offset: number;
}

export async function getAuditLogs(limit = 25, offset = 0): Promise<AuditLogPage> {
  const response = await apiGet<unknown>("/audit/", { limit, offset });
  if (response && typeof response === "object" && "items" in response) {
    return response as AuditLogPage;
  }
  const items = unwrapList<AuditRecord>(response);
  return { items, total: items.length, limit, offset };
}
