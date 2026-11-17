import { useCallback, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { RefreshCw, Trash2 } from "lucide-react";
import { getAuditLogs } from "../api/approvals";
import { deleteAgentRun, getAgentRuns } from "../api/agentRuns";
import { getBattlecards } from "../api/battlecards";
import { Link } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import { EmptyState, ErrorMessage, Loading, StatusBadge } from "../components/common/Feedback";

export default function AuditLogs() {
  const [searchParams] = useSearchParams();
  const [auditPage, setAuditPage] = useState(1);
  const auditOffset = (auditPage - 1) * 25;
  const loadAuditPage = useCallback(() => getAuditLogs(25, auditOffset), [auditOffset]);
  const audit = useApi(loadAuditPage);
  const runs = useApi(getAgentRuns);
  const battlecards = useApi(getBattlecards);
  const [deletingRun, setDeletingRun] = useState<string | null>(null);
  const [actionError, setActionError] = useState("");
  const isRefreshing = audit.refreshing || runs.refreshing || battlecards.refreshing;

  if (audit.loading || runs.loading || battlecards.loading) return <Loading text="Loading workspace history..." />;
  const cardsById = new Map((battlecards.data ?? []).map(card => [card.id, card]));
  const legacyOnly = searchParams.get("legacy") === "1";
  const selectedImportId = searchParams.get("import_id");
  const visibleRuns = (runs.data ?? []).filter(run => legacyOnly ? !run.import_id : selectedImportId ? run.import_id === selectedImportId : true);
  const auditTotal = audit.data?.total ?? 0;
  const auditItems = audit.data?.items ?? [];
  const auditPages = Math.max(1, Math.ceil(auditTotal / 25));
  const firstAuditItem = auditTotal === 0 ? 0 : auditOffset + 1;
  const lastAuditItem = Math.min(auditTotal, auditOffset + auditItems.length);
  const actionLabels: Record<string, string> = { generated_by_ai: "AI draft created", approve: "Approved by reviewer", reject: "Rejected by reviewer", request_changes: "Changes requested", resubmit: "Returned for review", delete_analysis: "Analysis data deleted", delete_source: "Source and linked data deleted" };
  const actionLabel = (action: string) => actionLabels[action] ?? action.replaceAll("_", " ");
  const removeRun = async (runId: string) => {
    const confirmed = window.confirm(`Permanently delete run ${runId.slice(0, 8)}? This removes its scores, generated battlecards, and evidence created only by this run. The uploaded source file and audit trail stay saved.`);
    if (!confirmed) return;
    setDeletingRun(runId);
    setActionError("");
    try {
      await deleteAgentRun(runId);
      await Promise.all([runs.refresh(), audit.refresh(), battlecards.refresh()]);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not delete this analysis run.");
    } finally {
      setDeletingRun(null);
    }
  };

  return (
    <div className="page-stack">
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h3>Analysis runs</h3>
            <p>Each run stores its scores and outputs. Delete an incorrect or test run here; its data is removed and the action remains audited.</p>
          </div>
          <button className="button secondary" onClick={() => { void Promise.all([audit.refresh(), runs.refresh(), battlecards.refresh()]); }} disabled={isRefreshing} title="Reload saved run and review history. This does not start a new analysis."><RefreshCw size={14} className={isRefreshing ? "refresh-icon-spin" : ""}/> {isRefreshing ? "Reloading…" : "Reload history"}</button>
        </div>
        <ErrorMessage text={[audit.error, runs.error, actionError].filter(Boolean).join(" · ")} />
        {visibleRuns.length ? (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Source file</th><th>Started</th><th>Run ID</th><th>Status</th><th>Rows</th><th>Scored</th><th>Research targets</th><th>Drafts</th><th>Actions</th></tr></thead>
              <tbody>
                {visibleRuns.map(run => (
                  <tr key={run.run_id}>
                    <td><b>{run.source_name || "Manual analysis"}</b><small>{run.import_id ? `Source ${run.import_id.slice(0, 8)}` : "Legacy run"}</small></td>
                    <td>{run.created_at ? new Date(run.created_at).toLocaleString() : "—"}</td>
                    <td><code>{run.run_id.slice(0, 8)}</code></td>
                    <td><StatusBadge value={run.status} /></td>
                    <td>{run.uploaded_count} <small>({run.valid_count} valid · {run.warning_count} warnings · {run.invalid_count} invalid)</small></td>
                    <td>{run.scoring_results?.length ?? 0}</td>
                    <td>{run.research_targets?.length ?? 0}</td>
                    <td>{run.battlecard_ids?.length ?? 0}</td>
                    <td><button className="button source-delete-button" onClick={() => void removeRun(run.run_id)} disabled={run.status === "running" || deletingRun === run.run_id} title="Permanently delete analysis data" aria-label={`Delete run ${run.run_id}`}><Trash2 size={14}/></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState title={legacyOnly ? "No unlinked legacy runs" : "No analysis runs yet"} text={legacyOnly ? "All earlier runs without an uploaded source file have been removed." : "After you upload a file and run competitor analysis, each run will be recorded here."} />
        )}
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div><h3>Battlecard audit trail</h3><p>AI draft creation and every human approval, rejection, or change request.</p></div>
        </div>
        {auditItems.length ? (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Event</th><th>Battlecard</th><th>Previous</th><th>New status</th><th>Actor</th><th>Timestamp</th></tr></thead>
              <tbody>
                {auditItems.map((item, index) => (
                  <tr key={String(item.id ?? index)}>
                    <td><b>{actionLabel(String(item.action ?? "—"))}</b><small>{String(item.comment ?? "")}</small></td>
                    <td>{item.entity_type === "battlecard" && cardsById.has(Number(item.entity_id)) ? <Link to={`/battlecards/${item.entity_id}`}>{cardsById.get(Number(item.entity_id))?.competitor_name} · {cardsById.get(Number(item.entity_id))?.domain}</Link> : item.entity_type === "battlecard" ? `Deleted battlecard #${String(item.entity_id ?? "—")}` : item.entity_type === "analysis_run" ? `Analysis run #${String(item.entity_id ?? "—")}` : `${String(item.entity_type ?? "—")} #${String(item.entity_id ?? "—")}`}</td>
                    <td><StatusBadge value={String(item.previous_status ?? "")} /></td>
                    <td><StatusBadge value={String(item.new_status ?? "")} /></td>
                    <td>{String(item.actor ?? "System")}</td>
                    <td>{item.created_at ? new Date(String(item.created_at)).toLocaleString() : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState title="No battlecard events yet" text="When KOMP creates a battlecard draft, and when a reviewer approves, rejects, or requests changes, the event will appear here." />
        )}
        {auditTotal > 0 && <div className="queue-pagination">
          <span>Showing {firstAuditItem}–{lastAuditItem} of {auditTotal} audit events</span>
          <div>
            <button className="button secondary" disabled={auditPage <= 1 || audit.refreshing} onClick={() => setAuditPage(page => Math.max(1, page - 1))}>Previous</button>
            <span>Page {auditPage} of {auditPages}</span>
            <button className="button secondary" disabled={auditPage >= auditPages || audit.refreshing} onClick={() => setAuditPage(page => Math.min(auditPages, page + 1))}>Next</button>
          </div>
        </div>}
      </section>
    </div>
  );
}
