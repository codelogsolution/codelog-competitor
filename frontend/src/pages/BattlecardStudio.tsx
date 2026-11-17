import { useCallback, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { ArrowRight, MoreHorizontal, Trash2 } from "lucide-react";
import {
  deleteBattlecard,
  getBattlecard,
  getBattlecards,
  type BattlecardContent,
} from "../api/battlecards";
import { getAgentRuns } from "../api/agentRuns";
import { useApi } from "../hooks/useApi";
import {
  EmptyState,
  ErrorMessage,
  Loading,
  StatusBadge,
} from "../components/common/Feedback";

function BattlecardDetail({ id }: { id: string }) {
  const loadBattlecard = useCallback(() => getBattlecard(id), [id]);

  const { data, loading, error } = useApi(loadBattlecard);
  if (loading) return <Loading text="Loading battlecard..." />;
  if (error || !data)
    return <ErrorMessage text={error || "Battlecard not found"} />;
  let content: BattlecardContent;
  try {
    content =
      typeof data.content === "string"
        ? (JSON.parse(data.content) as BattlecardContent)
        : data.content;
  } catch {
    content = {} as BattlecardContent;
  }
  const sections: Array<[string, string | string[] | undefined]> = [
    ["Overview", content.overview],
    ["Positioning", content.positioning],
    ["Strengths", content.strengths],
    ["Weaknesses", content.weaknesses],
    ["Product gaps", content.product_gaps],
    ["Pricing", content.pricing],
    ["Opportunities", content.opportunities],
    ["Recommended actions", content.recommended_actions],
    ["Evidence notes", content.evidence_notes],
  ];
  return (
    <div className="page-stack">
      <Link className="text-link" to="/battlecards">
        ← Back to battlecards
      </Link>
      <section className="panel">
        <StatusBadge value={data.status} />
        <h2>{data.competitor_name}</h2>
        <p className="muted">{data.domain}</p>
        <p>
          Threat level: <StatusBadge value={content.threat_level} />
        </p>
      </section>
      <div className="card-grid">
        {sections.map(([title, value]) => (
          <article className="panel" key={title}>
            <h3>{title}</h3>
            {Array.isArray(value) ? (
              value.length ? (
                <ul>
                  {value.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="muted">Not available in supplied evidence</p>
              )
            ) : (
              <p>{value || "Not available in supplied evidence"}</p>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}

export default function BattlecardStudio() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const selectedRunId = searchParams.get("run_id");
  const selectedStatus = searchParams.get("status");
  const { data, loading, error, refresh } = useApi(getBattlecards);
  const runs = useApi(getAgentRuns);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);

  const handleDelete = useCallback(
    async (id: number) => {
      setDeletingId(id);
      try {
        await deleteBattlecard(id);
        setConfirmDeleteId(null);
        await refresh();
      } catch {
        setDeletingId(null);
        setConfirmDeleteId(null);
        alert("Failed to delete battlecard.");
      }
    },
    [refresh],
  );

  if (id) return <BattlecardDetail id={id} />;
  if (loading || (selectedRunId !== null && runs.loading)) return <Loading text="Loading battlecards..." />;
  const selectedRun = selectedRunId ? runs.data?.find(run => run.run_id === selectedRunId) : undefined;
  const runCards = selectedRunId
    ? (data ?? []).filter(card => selectedRun?.battlecard_ids.includes(card.id))
    : data ?? [];
  const visibleCards = selectedStatus ? runCards.filter(card => card.status === selectedStatus) : runCards;
  return (
    <div className="page-stack">
      {selectedRunId && <div className="review-run-context"><b>{selectedRun?.source_name || "Selected source analysis"}</b><span>Battlecards saved for this source only</span><Link to="/">Back to workspace</Link></div>}
      {selectedStatus && <div className="review-run-context"><b>{selectedStatus === "approved" ? "Approved battlecards" : `${selectedStatus} battlecards`}</b><span>Showing {visibleCards.length} saved decision{visibleCards.length === 1 ? "" : "s"}</span><Link to="/battlecards">Show all battlecards</Link></div>}
      <p className="muted">
        Battlecard drafts are separate from source evidence. Deleting a draft
        does not remove competitor records, evidence or analysis history.
      </p>
      <ErrorMessage text={[error, selectedRunId ? runs.error : ""].filter(Boolean).join(" · ")} />
      {visibleCards.length ? (
        <>
          <div className="card-grid m-2">
            {visibleCards.map((card) => (
              <article
                className="mini-card panel"
                key={card.id}
              >
                <div className="mini-card-head">
                  <StatusBadge value={card.status} />
                  <button className="mini-card-menu" onClick={() => setConfirmDeleteId(card.id)} title="Delete this battlecard" aria-label={`Delete ${card.competitor_name} battlecard`}><MoreHorizontal size={17}/></button>
                </div>
                <Link className="mini-card-main" to={`/battlecards/${card.id}`}>
                  <b>{card.competitor_name}</b>
                  <small>{card.domain}</small>
                  <span>Open battlecard <ArrowRight size={13}/></span>
                </Link>
                {confirmDeleteId === card.id ? (
                  <div className="button-row mini-card-confirm">
                    <button
                      className="button primary"
                      onClick={() => void handleDelete(card.id)}
                      disabled={deletingId === card.id}
                    >
                      {deletingId === card.id ? (
                        "Deleting..."
                      ) : (
                        <>
                          <Trash2 size={13} /> Delete
                        </>
                      )}
                    </button>
                    <button
                      className="button ghost"
                      onClick={() => setConfirmDeleteId(null)}
                    >
                      Cancel
                    </button>
                  </div>
                ) : null}
              </article>
            ))}
          </div>
          <div className="button-row mt-4">
            <Link className="button primary" to="/approvals">
              <ArrowRight size={14} /> Next: Review & Approve Battlecards
            </Link>
            <Link className="button secondary" to="/import">
              Run New Analysis
            </Link>
          </div>
        </>
      ) : selectedStatus ? <div className="workspace-empty"><span>No {selectedStatus} battlecards found.</span><Link to="/approvals">Open review history <ArrowRight size={13}/></Link></div> : (
        <EmptyState
          title="No battlecard drafts yet"
          text="Battlecards are created only for high-priority competitors with a score of 70 or higher and usable evidence. Upload data and run an analysis to get started."
        >
          <div className="button-row mt-4">
            <Link className="button primary" to="/import">
              Run Competitor Analysis <ArrowRight size={14} />
            </Link>
            <Link className="button secondary" to="/evidence">
              View Evidence <ArrowRight size={14} />
            </Link>
          </div>
        </EmptyState>
      )}
    </div>
  );
}
