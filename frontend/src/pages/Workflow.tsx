import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Check, Circle, Clock3, FileSpreadsheet, RefreshCw, Trash2, UploadCloud, X } from "lucide-react";
import { getAgentRuns } from "../api/agentRuns";
import { getBattlecards } from "../api/battlecards";
import { deleteSourceImport, getSourceImports, type SourceImportRecord } from "../api/sourceImports";
import { useApi } from "../hooks/useApi";
import { ErrorMessage, Loading } from "../components/common/Feedback";

const stages = [
  { label: "File uploaded", keys: ["upload"] },
  { label: "Rows checked", keys: ["validation"] },
  { label: "Competitors scored", keys: ["scoring"] },
  { label: "Evidence gathered", keys: ["uploaded_evidence", "research", "research_evidence"] },
  { label: "Battlecard drafted", keys: ["battlecards"] },
  { label: "Human approval", keys: ["human_approval"] },
];
const runningStageNames: Record<string, string> = {
  analysis: "Ready to start analysis", scoring: "Scoring competitors", uploaded_evidence: "Saving uploaded evidence",
  research: "Researching eligible competitors", research_evidence: "Saving public evidence",
  battlecards: "Preparing battlecards", human_approval: "Waiting for your review", complete: "Analysis complete",
};

type Card = { id: number; status: string; competitor_name: string; domain: string };

function rowStageStates(source: SourceImportRecord, cards: Card[]) {
  const progress = source.stage_progress ?? {};
  const complete = source.status === "completed";
  return stages.map((stage, index) => {
    if (index === 0) return "done";
    if (index === 1) return "done";
    if (index === 4 && cards.length) return "done";
    if (index === 4 && source.status === "completed" && !cards.length) return "skipped";
    if (index === 5 && cards.some(card => ["pending_review", "pending", "changes_requested"].includes(card.status))) return "active";
    if (index === 5 && cards.length && cards.every(card => card.status === "approved")) return "done";
    if (index === 5 && cards.length && cards.every(card => card.status === "rejected")) return "rejected";
    if (index === 5 && cards.length && cards.every(card => ["approved", "rejected"].includes(card.status))) return "done";
    if (index === 5 && source.status === "completed" && !cards.length) return "skipped";
    const states = stage.keys.map(key => progress[key]?.status).filter(Boolean);
    if (states.length && states.every(state => state === "completed" || state === "skipped")) return states.every(state => state === "skipped") ? "skipped" : "done";
    if (states.includes("started") || (source.status === "running" && stage.keys.includes(source.current_stage))) return "active";
    if (source.status === "failed" && stage.keys.includes(source.current_stage)) return "failed";
    if (complete && index < 4) return "done";
    if (source.status === "pending_review" && index < 4) return "done";
    return "waiting";
  });
}

function currentStep(source: SourceImportRecord, states: string[]) {
  if (source.status === "failed") {
    const stage = stages.findIndex(item => item.keys.includes(source.current_stage));
    return `Stopped at step ${stage >= 0 ? stage + 1 : "—"} · ${runningStageNames[source.current_stage] ?? source.current_stage}`;
  }
  if (source.status === "running") return `In progress · ${runningStageNames[source.current_stage] ?? "Analysis running"}`;
  const pending = states.findIndex(state => state === "waiting" || state === "active");
  if (pending < 0) return "Complete";
  return `Step ${pending + 1} of 6 · ${stages[pending].label}`;
}

export default function Workflow() {
  const sources = useApi(getSourceImports);
  const runs = useApi(getAgentRuns);
  const battlecards = useApi(getBattlecards);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [decisionFilter, setDecisionFilter] = useState("all");
  if (sources.loading || runs.loading || battlecards.loading) return <Loading text="Loading analysis workflow..."/>;

  const history = runs.data ?? [];
  const cards = battlecards.data ?? [];
  const decisionCounts = {
    all: cards.length,
    pending_review: cards.filter(card => ["pending_review", "pending", "changes_requested"].includes(card.status)).length,
    approved: cards.filter(card => card.status === "approved").length,
    rejected: cards.filter(card => card.status === "rejected").length,
  };
  const visibleDecisionCards = decisionFilter === "all" ? cards : cards.filter(card => decisionFilter === "pending_review"
    ? ["pending_review", "pending", "changes_requested"].includes(card.status)
    : card.status === decisionFilter);
  const sourceNameByCard = new Map(history.flatMap(run => run.battlecard_ids.map(id => [id, run.source_name || "Legacy analysis"] as const)));
  const isRefreshing = sources.refreshing || runs.refreshing || battlecards.refreshing;
  const refresh = async () => { await Promise.all([sources.refresh(), runs.refresh(), battlecards.refresh()]); };
  const remove = async (source: SourceImportRecord) => {
    if (!window.confirm(`Permanently delete “${source.original_filename}”? This removes the original file, its analysis runs, scores, linked battlecards, and run-owned evidence from KOMP. Audit history is retained.`)) return;
    setDeletingId(source.import_id);
    try { await deleteSourceImport(source.import_id); await sources.refresh(); }
    catch (error) { window.alert(error instanceof Error ? error.message : "Could not remove this file."); }
    finally { setDeletingId(null); }
  };

  return <div className="page-stack workflow-page">
    <header className="workflow-page-heading"><div><span className="eyebrow">WORKFLOW</span><h2>Follow each file from upload to decision.</h2><p>Every file has its own progress, results, and review history. Pick up where KOMP stopped.</p></div><div><button className="button secondary" onClick={() => void refresh()} disabled={isRefreshing} title="Reload saved source files and analysis status. This does not restart analysis."><RefreshCw size={14} className={isRefreshing ? "refresh-icon-spin" : ""}/> {isRefreshing ? "Reloading…" : "Reload workflow"}</button><Link className="button primary" to="/import"><UploadCloud size={14}/> Upload a file</Link></div></header>
    <ErrorMessage text={[sources.error, runs.error, battlecards.error].filter(Boolean).join(" · ")}/>
    {sources.data?.length ? <div className="workflow-file-list">{sources.data.map(source => {
      const sourceRuns = history.filter(run => run.import_id === source.import_id);
      const run = sourceRuns[0];
      const ids = new Set(sourceRuns.flatMap(item => item.battlecard_ids));
      const sourceCards = cards.filter(card => ids.has(card.id));
      const states = rowStageStates(source, sourceCards);
      const waiting = sourceCards.filter(card => ["pending_review", "pending", "changes_requested"].includes(card.status));
      const approved = sourceCards.filter(card => card.status === "approved");
      const rejected = sourceCards.filter(card => card.status === "rejected");
      const activeStep = states.findIndex(state => state === "waiting" || state === "active" || state === "failed");
      let next = { label: "Open file", to: `/import?import_id=${encodeURIComponent(source.import_id)}` };
      if (source.status === "running") next = { label: "Analysis is running", to: "#" };
      else if (waiting.length && run) next = { label: `Review ${waiting.length} battlecard${waiting.length === 1 ? "" : "s"}`, to: `/approvals?run_id=${encodeURIComponent(run.run_id)}` };
      else if (source.status === "ready" || source.status === "failed") next = { label: source.status === "ready" ? "Continue analysis" : "Retry analysis", to: `/import?import_id=${encodeURIComponent(source.import_id)}` };
      else if (run) next = { label: "View analysis results", to: `/battlecards?run_id=${encodeURIComponent(run.run_id)}` };
      return <article className="workflow-file-card" key={source.import_id}>
        <div className="workflow-file-heading"><span className="workflow-file-icon"><FileSpreadsheet size={19}/></span><div className="workflow-file-name"><b>{source.original_filename}</b><small>{new Date(source.created_at).toLocaleString()} · {source.valid_records} valid rows{run ? ` · Run ${run.run_id.slice(0, 8)}` : " · Not analyzed yet"}</small></div><span className={`workflow-current ${source.status}`}><i/>{currentStep(source, states)}</span><Link className="button primary" to={next.to} onClick={event => { if (next.to === "#") event.preventDefault(); }}>{next.label}<ArrowRight size={13}/></Link><button className="button source-delete-button" onClick={() => void remove(source)} disabled={source.status === "running" || deletingId === source.import_id} title="Delete file and its KOMP analysis data" aria-label={`Delete ${source.original_filename} and related analysis data`}><Trash2 size={15}/></button></div>
        <div className="workflow-steps" aria-label={`Progress for ${source.original_filename}`}>{stages.map((stage, index) => {
          const state = states[index];
          const isCurrent = activeStep === index;
          return <div className={`workflow-step-card ${state} ${isCurrent ? "current" : ""}`} key={stage.label}><span>{state === "done" ? <Check size={14}/> : state === "failed" || state === "rejected" ? <X size={14}/> : state === "active" ? <Clock3 size={14}/> : <Circle size={13}/>}</span><b>{stage.label}</b><small>{state === "done" ? "Done" : state === "active" ? "In progress" : state === "failed" ? "Failed" : state === "rejected" ? "Rejected" : state === "skipped" ? "Not needed" : "Waiting"}</small></div>;
        })}</div>
        <div className="workflow-file-footer"><span>{source.total_records} rows · {source.warning_records} warnings · {source.invalid_records} invalid</span><span className="workflow-decisions">{waiting.length > 0 && <span className="workflow-decision pending">{waiting.length} pending review</span>}{approved.length > 0 && <span className="workflow-decision approved">{approved.length} approved</span>}{rejected.length > 0 && <span className="workflow-decision rejected">{rejected.length} rejected</span>}{!sourceCards.length && <span>No battlecards created</span>}</span></div>
      </article>;
    })}</div> : <section className="workflow-empty"><FileSpreadsheet size={28}/><h3>No source files yet</h3><p>{history.length ? `${history.length} earlier analysis runs are saved, but their source filenames predate file tracking. New uploads will appear here with full step history.` : "Upload a CSV/XLSX file to start. KOMP will show each step and save the result against that file."}</p><Link className="button primary" to="/import"><UploadCloud size={14}/> Upload first file</Link>{history.length > 0 && <Link to="/audit">View earlier runs <ArrowRight size={13}/></Link>}</section>}
    <section className="workflow-decisions-panel">
      <div className="workflow-decisions-heading"><div><span className="eyebrow">BATTLECARD DECISIONS</span><h3>Review status by competitor</h3><p>AI drafts and human decisions are kept together here.</p></div><Link to="/approvals">Open review & export <ArrowRight size={13}/></Link></div>
      <div className="workflow-filter-tabs" role="tablist" aria-label="Filter battlecards by decision"><button className={decisionFilter === "all" ? "active" : ""} onClick={() => setDecisionFilter("all")}>All <b>{decisionCounts.all}</b></button><button className={decisionFilter === "pending_review" ? "active" : ""} onClick={() => setDecisionFilter("pending_review")}>Needs review <b>{decisionCounts.pending_review}</b></button><button className={decisionFilter === "approved" ? "active" : ""} onClick={() => setDecisionFilter("approved")}>Approved <b>{decisionCounts.approved}</b></button><button className={decisionFilter === "rejected" ? "active" : ""} onClick={() => setDecisionFilter("rejected")}>Rejected <b>{decisionCounts.rejected}</b></button></div>
      {visibleDecisionCards.length ? <div className="workflow-decision-list">{visibleDecisionCards.map(card => <Link to={`/battlecards/${card.id}`} key={card.id} className="workflow-decision-row"><span><b>{card.competitor_name}</b><small>{card.domain} · {sourceNameByCard.get(card.id) ?? "Manual analysis"}</small></span><span className={`workflow-decision-status ${card.status}`}>{card.status.replaceAll("_", " ")}</span><ArrowRight size={15}/></Link>)}</div> : <p className="workflow-decision-empty">{decisionFilter === "all" ? "Battlecards appear here after KOMP finds eligible evidence." : `No ${decisionFilter === "pending_review" ? "battlecards waiting for review" : `${decisionFilter} battlecards`} right now.`}</p>}
    </section>
    <aside className="workflow-audit-explainer"><b>What is saved where?</b><p><strong>Workflow</strong> shows each file and current step. <strong>Run history</strong> records what the agent processed and generated. <strong>Audit trail</strong> records battlecard creation and each human approval, rejection, or change request.</p><Link to="/audit">Open run history & audit trail <ArrowRight size={13}/></Link></aside>
  </div>;
}
