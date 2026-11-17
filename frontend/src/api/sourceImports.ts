import { apiDelete, apiGet } from "./client";
import type { UploadResult } from "./uploads";

export interface SourceImportRecord {
  import_id: string;
  original_filename: string;
  total_records: number;
  valid_records: number;
  warning_records: number;
  invalid_records: number;
  status: string;
  current_stage: string;
  stage_progress: Record<string, { status: string; message?: string }>;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export async function getSourceImports(): Promise<SourceImportRecord[]> {
  const response = await apiGet<unknown>("/uploads", { limit: 200 });
  return Array.isArray(response) ? response as SourceImportRecord[] : [];
}

export async function getSourceImport(importId: string): Promise<UploadResult & SourceImportRecord> {
  return apiGet<UploadResult & SourceImportRecord>(`/uploads/${encodeURIComponent(importId)}`);
}

export async function deleteSourceImport(importId: string): Promise<void> {
  await apiDelete(`/uploads/${encodeURIComponent(importId)}`);
}
