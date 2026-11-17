import {
  useCallback,
  useMemo,
  useState,
} from "react";
import {
  ArrowRight,
  ExternalLink,
  MoreHorizontal,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";
import { Link } from "react-router-dom";
import {
  deleteEvidence,
  getEvidence,
  resolveWarningEvidence,
} from "../api/evidence";
import { useApi } from "../hooks/useApi";
import {
  EmptyState,
  ErrorMessage,
  Loading,
  StatusBadge,
} from "../components/common/Feedback";

export default function EvidenceHub() {
  const { data, loading, refreshing, error, refresh } = useApi(getEvidence);
  const [query, setQuery] = useState("");
  const [expandedSignalId, setExpandedSignalId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [reviewingId, setReviewingId] = useState<number | null>(null);
  const [reviewComment, setReviewComment] = useState("");
  const [reviewSourceUrl, setReviewSourceUrl] = useState("");
  const [resolvingId, setResolvingId] = useState<number | null>(null);
  const [actionError, setActionError] = useState("");

  const rows = useMemo(
    () =>
      (data ?? []).filter((item) =>
        `${item.competitor_name} ${item.domain} ${item.signal_text} ${item.source_type}`
          .toLowerCase()
          .includes(query.toLowerCase()),
      ),
    [data, query],
  );

  const handleDelete = useCallback(
    async (id: number) => {
      setDeletingId(id);
      try {
        await deleteEvidence(id);
        setConfirmDeleteId(null);
        await refresh();
      } catch {
        setDeletingId(null);
        setConfirmDeleteId(null);
        alert("Failed to delete evidence.");
      }
    },
    [refresh],
  );

  async function resolveWarning(id: number, decision: "confirm_valid" | "mark_invalid") {
    setResolvingId(id);
    setActionError("");
    try {
      await resolveWarningEvidence(id, decision, reviewComment, reviewSourceUrl);
      setReviewingId(null);
      setReviewComment("");
      setReviewSourceUrl("");
      await refresh();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not resolve evidence.");
    } finally {
      setResolvingId(null);
    }
  }

  if (loading) return <Loading text="Loading evidence..." />;
  return (
    <div className="page-stack">
      <ErrorMessage text={[error, actionError].filter(Boolean).join(" · ")} />
      <p className="muted">Evidence records are the source material behind competitor scores and battlecards. Removing evidence does not delete existing battlecard drafts or audit history.</p>
      <div className="toolbar">
        <div className="search-box">
          <Search size={16} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search evidence"
          />
        </div>
        <button className="button secondary" onClick={() => void refresh()} disabled={refreshing} title="Reload saved evidence records. This does not rerun research or analysis.">
          <RefreshCw size={14} className={refreshing ? "refresh-icon-spin" : ""} /> {refreshing ? "Reloading…" : "Reload evidence"}
        </button>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h3>Evidence records</h3>
            <p>{rows.length} records</p>
          </div>
        </div>
        {rows.length ? (
          <>
            <div className="table-wrap">
              <table className="evidence-record-table">
                <colgroup>
                  <col style={{ width: "15%" }} />
                  <col style={{ width: "30%" }} />
                  <col style={{ width: "10%" }} />
                  <col style={{ width: "9%" }} />
                  <col style={{ width: "9%" }} />
                  <col style={{ width: "8%" }} />
                  <col style={{ width: "9%" }} />
                  <col style={{ width: "10%" }} />
                </colgroup>
                <thead>
                  <tr>
                    <th>Competitor</th>
                    <th>Signal</th>
                    <th>Type</th>
                    <th>Sentiment</th>
                    <th>Status</th>
                    <th>Frequency</th>
                    <th>Source</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <b>{item.competitor_name}</b>
                        <small>{item.domain}</small>
                      </td>
                      <td className="evidence-signal-cell">
                        <div className={`evidence-signal-preview ${expandedSignalId === item.id ? "expanded" : ""}`}>
                          {item.signal_text}
                        </div>
                        {item.signal_text.length > 110 && (
                          <button
                            className="evidence-signal-toggle"
                            type="button"
                            aria-expanded={expandedSignalId === item.id}
                            onClick={() => setExpandedSignalId(expandedSignalId === item.id ? null : item.id)}
                          >
                            {expandedSignalId === item.id ? "Show less" : "Read full signal"}
                          </button>
                        )}
                      </td>
                      <td>{item.signal_type}</td>
                      <td><StatusBadge value={item.sentiment} /></td>
                      <td><StatusBadge value={item.status} /></td>
                      <td>{item.frequency ?? "—"}</td>
                      <td className="evidence-source-cell">
                        {item.source_url ? (
                          <a className="text-link" href={item.source_url} target="_blank" rel="noreferrer">
                            Open <ExternalLink size={12} />
                          </a>
                        ) : (
                          <span className="muted">Source unavailable</span>
                        )}
                      </td>
                      <td>
                        <div className="button-row" style={{ gap: 6 }}>
                          {item.status === "warning" && reviewingId !== item.id && (
                            <button
                              className="button secondary"
                              onClick={() => { setReviewingId(item.id); setReviewComment(""); setReviewSourceUrl(item.source_url || ""); setActionError(""); }}
                            >
                              Review warning
                            </button>
                          )}
                          {reviewingId === item.id && (
                            <div className="evidence-review-actions">
                              <input
                                aria-label="Evidence source URL"
                                value={reviewSourceUrl}
                                onChange={event => setReviewSourceUrl(event.target.value)}
                                placeholder="Source URL (required to confirm valid)"
                              />
                              <input
                                aria-label="Reviewer comment"
                                value={reviewComment}
                                onChange={event => setReviewComment(event.target.value)}
                                placeholder="Optional review note"
                              />
                              <button
                                className="button primary"
                                disabled={resolvingId === item.id || !/^https?:\/\//i.test(reviewSourceUrl)}
                                onClick={() => void resolveWarning(item.id, "confirm_valid")}
                              >
                                Confirm valid
                              </button>
                              <button
                                className="button danger"
                                disabled={resolvingId === item.id}
                                onClick={() => void resolveWarning(item.id, "mark_invalid")}
                              >
                                Mark invalid
                              </button>
                              <button className="button ghost" onClick={() => setReviewingId(null)}>Cancel</button>
                              {!/^https?:\/\//i.test(reviewSourceUrl) && <small>A valid HTTP/HTTPS source URL is required before confirming this record.</small>}
                            </div>
                          )}
                          {confirmDeleteId === item.id ? (
                            <>
                              <button
                                className="button primary"
                                onClick={() => void handleDelete(item.id)}
                                disabled={deletingId === item.id}
                              >
                                {deletingId === item.id
                                  ? "Deleting..."
                                  : <><Trash2 size={13} /> Delete</>}
                              </button>
                              <button
                                className="button ghost"
                                onClick={() => setConfirmDeleteId(null)}
                              >
                                Cancel
                              </button>
                            </>
                          ) : (
                            <div className="relative">
                              <button
                                className="button ghost"
                                onClick={() => setConfirmDeleteId(item.id)}
                                title="Delete"
                              >
                                <MoreHorizontal size={16} />
                              </button>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="button-row mt-4">
              <Link className="button primary" to="/competitors">
                <ArrowRight size={14} /> Next: Review competitors
              </Link>
              <Link className="button secondary" to="/import">
                Import More Sources
              </Link>
            </div>
          </>
        ) : (
          <EmptyState
            title={query ? "No matching evidence" : "No evidence yet"}
            text={query ? "Try a different competitor, source type or signal keyword." : "Upload a CSV or XLSX source and run an analysis. Source records will appear here for review."}
          >
            <Link className="button primary mt-4" to="/import">
              Go to Import Sources <ArrowRight size={14} />
            </Link>
          </EmptyState>
        )}
      </section>
    </div>
  );
}
