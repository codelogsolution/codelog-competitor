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
export async function getAuditLogs(): Promise<AuditRecord[]> {
  return unwrapList<AuditRecord>(await apiGet<unknown>("/audit/"));
}
