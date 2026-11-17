import { useState } from "react";
import { ArrowRight, Check, MessageSquare, X } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";
import { API_BASE_URL } from "../api/client";
import { submitApprovalAction } from "../api/approvals";
import { getBattlecards } from "../api/battlecards";
import { getAgentRuns } from "../api/agentRuns";
import { useApi } from "../hooks/useApi";
import {
  EmptyState,
  ErrorMessage,
  Loading,
  StatusBadge,
} from "../components/common/Feedback";

type ReviewFilter =
  | "all"
  | "needs_review"
  | "approved"
  | "rejected"
  | "changes_requested";
const needsReview = new Set(["pending_review", "pending", "changes_requested"]);
const filters: Array<{ id: ReviewFilter; label: string }> = [
  { id: "all", label: "All cards" },
  { id: "needs_review", label: "Needs review" },
  { id: "approved", label: "Approved" },
  { id: "rejected", label: "Rejected" },
  { id: "changes_requested", label: "Changes requested" },
];

export default function Approvals() {
  const [searchParams] = useSearchParams();
  const selectedRunId = searchParams.get("run_id");
  const battlecards = useApi(getBattlecards);
  const runs = useApi(getAgentRuns);
  const [filter, setFilter] = useState<ReviewFilter>("all");
  const [comments, setComments] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState<number | null>(null);
  const [message, setMessage] = useState("");

  if (battlecards.loading || (selectedRunId !== null && runs.loading))
    return <Loading text="Loading review workspace..." />;

  const cards = battlecards.data ?? [];
  const selectedRun = selectedRunId
    ? runs.data?.find((run) => run.run_id === selectedRunId)
    : undefined;
  const selectedCardIds = new Set(selectedRun?.battlecard_ids ?? []);
  const sourceCards = selectedRunId
    ? cards.filter((card) => selectedCardIds.has(card.id))
    : cards;
  const counts: Record<ReviewFilter, number> = {
    all: sourceCards.length,
    needs_review: sourceCards.filter((card) => needsReview.has(card.status))
      .length,
    approved: sourceCards.filter((card) => card.status === "approved").length,
    rejected: sourceCards.filter((card) => card.status === "rejected").length,
    changes_requested: sourceCards.filter(
      (card) => card.status === "changes_requested",
    ).length,
  };
  const visibleCards = sourceCards.filter((card) => {
    if (filter === "all") return true;
    if (filter === "needs_review") return needsReview.has(card.status);
    return card.status === filter;
  });
  const approvedCount = cards.filter(
    (card) => card.status === "approved",
  ).length;
  const exportUrl = `${API_BASE_URL}/battlecards/export/approved`;

  async function act(
    id: number,
    action: "approve" | "reject" | "request-changes",
  ) {
    setBusy(id);
    setMessage("");
    try {
      await submitApprovalAction(id, action, comments[id] ?? "");
      setMessage(
        action === "approve"
          ? "Battlecard approved and saved."
          : action === "reject"
            ? "Battlecard rejected and saved."
            : "Changes requested and saved.",
      );
      await battlecards.refresh();
    } catch (err) {
      setMessage(
        err instanceof Error
          ? err.message
          : "Could not save this review decision.",
      );
    } finally {
      setBusy(null);
    }
  }

  const error = [battlecards.error, selectedRunId ? runs.error : ""]
    .filter(Boolean)
    .join(" · ");

  return (
    <div className="page-stack">
      <ErrorMessage text={error} />
      {selectedRunId && (
        <div className="review-run-context">
          <b>{selectedRun?.source_name || "Selected source analysis"}</b>
          <span>Showing this source's saved battlecards</span>
          <Link to="/workflow">Back to files</Link>
        </div>
      )}
      {message && <div className="alert">{message}</div>}

      <section className="panel review-workspace-panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">HUMAN DECISION</span>
            <h3>Review & export</h3>
            <p>
              All battlecards and their saved decisions are listed here. Only
              approved cards can be exported.
            </p>
          </div>
          {approvedCount > 0 ? (
            <a className="button primary" href={exportUrl}>
              Export {approvedCount} approved battlecard
              {approvedCount === 1 ? "" : "s"}
            </a>
          ) : (
            <span className="review-export-hint">
              Export unlocks when a card is approved.
            </span>
          )}
        </div>

        <div className="review-summary-grid">
          <div>
            <small>Needs review</small>
            <b>
              {
                sourceCards.filter((card) => needsReview.has(card.status))
                  .length
              }
            </b>
          </div>
          <div>
            <small>Approved</small>
            <b>
              {sourceCards.filter((card) => card.status === "approved").length}
            </b>
          </div>
          <div>
            <small>Rejected</small>
            <b>
              {sourceCards.filter((card) => card.status === "rejected").length}
            </b>
          </div>
        </div>

        <div
          className="review-filter-row"
          role="tablist"
          aria-label="Filter battlecards by decision"
        >
          {filters.map((item) => (
            <button
              key={item.id}
              className={`review-filter ${filter === item.id ? "is-active" : ""}`}
              role="tab"
              aria-selected={filter === item.id}
              onClick={() => setFilter(item.id)}
            >
              {item.label}
              <span>{counts[item.id]}</span>
            </button>
          ))}
        </div>

        {visibleCards.length ? (
          <div className="table-wrap review-table-wrap">
            <table className="review-table">
              <thead>
                <tr>
                  <th>Competitor</th>
                  <th>Decision</th>
                  <th>Evidence links</th>
                  <th>Created</th>
                  <th>Review note & action</th>
                </tr>
              </thead>
              <tbody>
                {visibleCards.map((card) => {
                  const canReview = needsReview.has(card.status);
                  const evidenceCount = Array.isArray(card.evidence_urls)
                    ? card.evidence_urls.length
                    : 0;
                  return (
                    <tr key={card.id}>
                      <td>
                        <b>{card.competitor_name}</b>
                        <small>{card.domain}</small>
                      </td>
                      <td>
                        <StatusBadge value={card.status} />
                      </td>
                      <td>
                        {evidenceCount ? (
                          `${evidenceCount} source${evidenceCount === 1 ? "" : "s"}`
                        ) : (
                          <span className="muted">No links</span>
                        )}
                      </td>
                      <td>
                        {card.created_at
                          ? new Date(card.created_at).toLocaleDateString()
                          : "—"}
                      </td>
                      <td>
                        <div className="review-row-actions">
                          <Link
                            className="button secondary review-open-button"
                            to={`/battlecards/${card.id}`}
                          >
                            View draft <ArrowRight size={12} />
                          </Link>
                          {canReview && (
                            <>
                              <input
                                aria-label={`Optional note for ${card.competitor_name}`}
                                value={comments[card.id] ?? ""}
                                onChange={(event) =>
                                  setComments((current) => ({
                                    ...current,
                                    [card.id]: event.target.value,
                                  }))
                                }
                                placeholder="Optional review note"
                              />
                              <button
                                className="button primary"
                                onClick={() => void act(card.id, "approve")}
                                disabled={busy === card.id}
                              >
                                <Check size={13} /> Approve
                              </button>
                              <button
                                className="button secondary"
                                onClick={() =>
                                  void act(card.id, "request-changes")
                                }
                                disabled={busy === card.id}
                              >
                                <MessageSquare size={13} /> Request changes
                              </button>
                              <button
                                className="button danger"
                                onClick={() => void act(card.id, "reject")}
                                disabled={busy === card.id}
                              >
                                <X size={13} /> Reject
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : cards.length === 0 ? (
          <EmptyState
            title="No battlecards saved yet"
            text="Once analysis finds an eligible competitor, its evidence-backed draft will appear here for a human decision."
          >
            <div className="button-row mt-4">
              <Link className="button primary" to="/workflow">
                View source workflow <ArrowRight size={14} />
              </Link>
              <Link className="button secondary" to="/import">
                Start an analysis
              </Link>
            </div>
          </EmptyState>
        ) : (
          <EmptyState
            title={`No ${filter === "needs_review" ? "battlecards need review" : filter.replaceAll("_", " ") + " battlecards"}`}
            text="Choose another decision filter to view the rest of your saved cards."
          />
        )}
      </section>

      <p className="review-governance-note">
        KOMP prepares sourced drafts. Your team owns approval, rejection, and
        export decisions.
      </p>
    </div>
  );
}
