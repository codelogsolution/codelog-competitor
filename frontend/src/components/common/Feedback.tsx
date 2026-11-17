import { AlertCircle, Inbox, LoaderCircle } from "lucide-react";

export function Loading({ text = "Loading..." }: { text?: string }) {
  return <div className="feedback"><LoaderCircle className="spin" size={23}/><span>{text}</span></div>;
}
export function ErrorMessage({ text }: { text?: string }) {
  return text ? <div className="alert" role="alert"><AlertCircle size={16}/><span>{text}</span></div> : null;
}
export function EmptyState({ title = "No records yet", text = "No records have been added yet.", children }: { title?: string; text?: string; children?: React.ReactNode }) {
  return <div className="empty-state"><Inbox size={25}/><b>{title}</b><p>{text}</p>{children}</div>;
}
export function StatusBadge({ value }: { value?: string }) {
  const label = (value || "unknown").replaceAll("_", " ");
  const key = label.toLowerCase();
  const tone = ["approved", "valid", "completed", "high"].includes(key) ? "green"
    : ["pending_review", "pending review", "medium", "warning", "changes_requested", "changes requested"].includes(key) ? "amber"
    : ["rejected", "invalid", "failed", "low"].includes(key) ? "red" : "";
  return <span className={`status-badge ${tone}`}>{label}</span>;
}
