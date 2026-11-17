import { Fragment, useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Search,
  SlidersHorizontal,
} from "lucide-react";
import { getCompetitors } from "../api/competitors";
import { getAgentRuns, type AgentRunRecord } from "../api/agentRuns";
import { useApi } from "../hooks/useApi";
import {
  EmptyState,
  ErrorMessage,
  Loading,
  StatusBadge,
} from "../components/common/Feedback";

const PAGE_SIZE = 10;
type RunScore = AgentRunRecord["scoring_results"][number];

function runOptionLabel(run: AgentRunRecord) {
  const source = run.source_name || "Manual analysis";
  const date = run.created_at
    ? new Date(run.created_at).toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      })
    : "Date unavailable";
  return `${source} · ${date}`;
}

export default function CompetitorQueue() {
  const runs = useApi(getAgentRuns);
  const [selectedRunId, setSelectedRunId] = useState("");
  const activeRun = runs.data?.find((run) => run.run_id === selectedRunId)
    ?? runs.data?.[0];
  const loadCompetitors = useCallback(
    () => getCompetitors(activeRun?.run_id),
    [activeRun?.run_id],
  );
  const competitors = useApi(loadCompetitors);
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const scoreMap = useMemo(
    () => new Map((activeRun?.scoring_results ?? []).map((score) => [score.domain ?? "", score])),
    [activeRun],
  );
  const rows = useMemo(() => {
    const evidenceByDomain = new Map((competitors.data ?? []).map((item) => [item.domain, item]));
    const runScores = activeRun?.scoring_results ?? [];
    const selectedRows = activeRun
      ? runScores.map((score: RunScore) => {
          const evidence = evidenceByDomain.get(score.domain ?? "");
          return {
            domain: score.domain ?? "unknown",
            competitor_name: score.competitor_name ?? evidence?.competitor_name ?? score.domain ?? "Unknown competitor",
            evidence: evidence?.evidence ?? [],
          };
        })
      : (competitors.data ?? []);

    return selectedRows
      .filter((item) => `${item.competitor_name} ${item.domain}`.toLowerCase().includes(query.trim().toLowerCase()))
      .sort((a, b) => (scoreMap.get(b.domain)?.preliminary_score ?? -1) - (scoreMap.get(a.domain)?.preliminary_score ?? -1) || a.competitor_name.localeCompare(b.competitor_name));
  }, [activeRun, competitors.data, query, scoreMap]);

  const totalPages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const visible = rows.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const isRefreshing = runs.refreshing || competitors.refreshing;

  function updateQuery(value: string) {
    setQuery(value);
    setPage(1);
    setExpanded(null);
  }

  async function refreshResults() {
    await Promise.all([runs.refresh(), competitors.refresh()]);
  }

  if (runs.loading || competitors.loading) return <Loading text="Loading saved competitor results..." />;

  const scores = activeRun?.scoring_results ?? [];
  const highPriority = scores.filter((item) => item.priority === "high").length;
  const reviewBand = scores.filter((item) => (item.preliminary_score ?? 0) >= 50 && (item.preliminary_score ?? 0) < 70).length;
  const lowPriority = scores.filter((item) => (item.preliminary_score ?? 0) < 50).length;

  return (
    <div className="page-stack queue-page">
      <div className="queue-heading">
        <div>
          <span className="eyebrow">SAVED ANALYSIS</span>
          <h2>Competitors in this analysis</h2>
          <p className="heading-copy">View one saved analysis at a time. This page displays results; upload and start analyses from Import & validate.</p>
        </div>
        <div className="queue-heading-actions">
          {runs.data?.length ? <label className="queue-run-select">
            <span>Analysis run</span>
            <select value={selectedRunId} onChange={(event) => { setSelectedRunId(event.target.value); setPage(1); setExpanded(null); }}>
              <option value="">Latest analysis · {runs.data[0]?.source_name || "Most recent run"}</option>
              {runs.data.slice(1).map((run) => <option key={run.run_id} value={run.run_id}>{runOptionLabel(run)}</option>)}
            </select>
          </label> : null}
          <button className="button secondary" onClick={() => void refreshResults()} disabled={isRefreshing} title="Reload saved scores and evidence. This does not start a new analysis.">
            <RefreshCw size={14} className={isRefreshing ? "refresh-icon-spin" : ""}/>
            {isRefreshing ? "Reloading…" : "Reload results"}
          </button>
        </div>
      </div>

      <ErrorMessage text={[competitors.error, runs.error].filter(Boolean).join(" · ")}/>

      {activeRun ? <div className="queue-run-context">
        <span className="queue-run-context-icon"><SlidersHorizontal size={15}/></span>
        <span><b>{activeRun.source_name || "Manual analysis"}</b><small>{activeRun.scoring_results.length} competitors scored · {runOptionLabel(activeRun)}</small></span>
        <span className="queue-run-context-note">Upload another file from <Link to="/import">Import & validate</Link>.</span>
      </div> : null}

      <section className="panel queue-toolbar-panel">
        <div className="queue-toolbar">
          <label className="search-box queue-search"><Search size={16}/><input value={query} onChange={(event) => updateQuery(event.target.value)} placeholder="Search this analysis by competitor or domain"/></label>
          <div className="queue-toolbar-meta"><SlidersHorizontal size={15}/><span>{rows.length} {rows.length === 1 ? "competitor" : "competitors"} in this view</span></div>
        </div>
        <div className="queue-summary">
          <div><small>High priority · 70+</small><b>{highPriority}</b></div>
          <div><small>Review · 50–69</small><b>{reviewBand}</b></div>
          <div><small>Low priority · &lt;50</small><b>{lowPriority}</b></div>
          <div><small>Scored in this analysis</small><b>{scores.length}</b></div>
        </div>
      </section>

      <section className="panel queue-table-panel">
        <div className="panel-heading">
          <div><h3>Scored competitors</h3><p>Scores use evidence from this analysis only. Public research can add evidence but does not change a score.</p></div>
          <span className="queue-count">{rows.length} {rows.length === 1 ? "result" : "results"}</span>
        </div>
        {visible.length ? <>
          <div className="table-wrap queue-table-wrap">
            <table className="queue-table">
              <thead><tr><th className="expand-col"></th><th>Competitor</th><th>Score</th><th>Priority</th><th>Score drivers</th><th>Evidence in this run</th></tr></thead>
              <tbody>
                {visible.map((item) => {
                  const isOpen = expanded === item.domain;
                  const score = scoreMap.get(item.domain);
                  const latest = [...item.evidence].sort((a, b) => (b.signal_date || b.created_at || "").localeCompare(a.signal_date || a.created_at || ""))[0];
                  return <Fragment key={item.domain}>
                    <tr className={`queue-row ${isOpen ? "selected" : ""}`} onClick={() => setExpanded(isOpen ? null : item.domain)}>
                      <td className="expand-col">{isOpen ? <ChevronDown size={15}/> : <ChevronRight size={15}/>}</td>
                      <td><b>{item.competitor_name}</b><small>{item.domain}</small></td>
                      <td>{score ? <b>{score.preliminary_score}/{score.max_score ?? 95}</b> : <span className="muted">Not scored</span>}</td>
                      <td><StatusBadge value={score?.priority ?? "not scored"}/></td>
                      <td className="latest-signal">{score?.reasons?.[0] ?? latest?.signal_type?.replaceAll("_", " ") ?? "No score explanation"}</td>
                      <td><span className="evidence-count">{item.evidence.length}</span></td>
                    </tr>
                    {isOpen && <tr key={`${item.domain}-details`} className="queue-detail-row"><td colSpan={6}>
                      <div className="queue-detail">
                        <div className="queue-detail-heading"><div><b>Why {item.competitor_name} received this score</b><small>{score ? `${score.preliminary_score} of ${score.max_score ?? 95} · ${score.evidence_count ?? item.evidence.length} scoring records` : `${item.domain} · ${item.evidence.length} evidence records`}</small></div><span className="queue-detail-hint">Latest 5 signals in this run</span></div>
                        {score?.breakdown && <div className="score-breakdown">{[["Review pain", score.breakdown.review_pain], ["SEO gap", score.breakdown.seo_gap], ["Product overlap", score.breakdown.product_overlap], ["Recency", score.breakdown.recency]].map(([label, value]) => <div key={String(label)}><small>{label}</small><b>{value}</b></div>)}</div>}
                        {score?.reasons?.length ? <ul className="score-reasons">{score.reasons.map((reason, index) => <li key={index}>{reason}</li>)}</ul> : null}
                        {score?.missing_data?.length ? <p className="score-missing">Missing inputs: {score.missing_data.join(", ")}</p> : null}
                        {item.evidence.length ? <div className="signal-list">{[...item.evidence].sort((a, b) => (b.signal_date || b.created_at || "").localeCompare(a.signal_date || a.created_at || "")).slice(0, 5).map((record) => <article className="signal-list-item" key={record.id}>
                          <div className="signal-list-meta"><span>{record.signal_type?.replaceAll("_", " ") || "Signal"}</span><span>{record.source_type || "Source"}</span><span>{record.signal_date || (record.created_at ? new Date(record.created_at).toLocaleDateString() : "Date unavailable")}</span></div>
                          <p>{record.signal_text}</p>
                          {record.source_url && <a href={record.source_url} target="_blank" rel="noreferrer">Open source ↗</a>}
                        </article>)}</div> : <EmptyState title="No evidence linked to this run" text="This run's score is saved, but KOMP has no linked evidence record to show here."/>}
                      </div>
                    </td></tr>}
                  </Fragment>;
                })}
              </tbody>
            </table>
          </div>
          <div className="queue-pagination"><span>Page {page} of {totalPages}</span><div><button className="button secondary" disabled={page <= 1} onClick={() => {setPage((current) => Math.max(1, current - 1));setExpanded(null);}}>Previous</button><button className="button secondary" disabled={page >= totalPages} onClick={() => {setPage((current) => Math.min(totalPages, current + 1));setExpanded(null);}}>Next</button></div></div>
        </> : activeRun ? <EmptyState title="No competitor scores in this analysis" text="This run did not produce scored competitors. Choose a different analysis above, or start a new one from Import & validate."><div className="button-row mt-4"><Link className="button secondary" to="/import">Open Import & validate <ArrowRight size={14}/></Link></div></EmptyState>
          : <EmptyState title="No analysis results yet" text="Upload a file and run analysis once from Import & validate. This page only displays saved competitor scores; it does not upload or run files."><div className="button-row mt-4"><Link className="button secondary" to="/import">Open Import & validate <ArrowRight size={14}/></Link></div></EmptyState>}
      </section>
    </div>
  );
}
