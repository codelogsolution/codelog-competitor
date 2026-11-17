import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Circle,
  ClipboardCheck,
  Clock3,
  FileSpreadsheet,
  FileText,
  Globe2,
  Layers3,
  RefreshCw,
  ShieldCheck,
  Trash2,
  UploadCloud,
  Users,
  XCircle,
} from "lucide-react";
import { getEvidence } from "../api/evidence";
import { getBattlecards } from "../api/battlecards";
import { getApprovals } from "../api/approvals";
import { getAgentRuns, type AgentRunRecord } from "../api/agentRuns";
import {
  deleteSourceImport,
  getSourceImports,
  type SourceImportRecord,
} from "../api/sourceImports";
import { useApi } from "../hooks/useApi";
import {
  ErrorMessage,
  Loading,
  StatusBadge,
} from "../components/common/Feedback";

const pendingStatuses = new Set([
  "pending_review",
  "pending",
  "changes_requested",
]);
const stageLabels: Record<string, string> = {
  analysis: "Ready to analyze",
  scoring: "Scoring competitors",
  uploaded_evidence: "Saving uploaded evidence",
  research: "Researching public sources",
  research_evidence: "Saving public evidence",
  battlecards: "Preparing battlecards",
  human_approval: "Waiting for human review",
  complete: "Analysis complete",
};

type StepState =
  | "done"
  | "active"
  | "waiting"
  | "skipped"
  | "rejected"
  | "failed";
type WorkflowStep = { label: string; state: StepState; detail: string };

function Metric({
  icon: Icon,
  label,
  value,
  footnote,
}: {
  icon: typeof Users;
  label: string;
  value: number;
  footnote: string;
}) {
  return (
    <article className="workspace-metric">
      <span className="workspace-metric-icon">
        <Icon size={17} />
      </span>
      <div>
        <span>{label}</span>
        <b>{value}</b>
        <small>{footnote}</small>
      </div>
    </article>
  );
}

function timeLabel(value: string) {
  if (!value) return "Date unavailable";
  return new Date(value).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function workflowSteps(
  source: SourceImportRecord,
  run: AgentRunRecord | undefined,
  cards: Array<{
    id: number;
    status: string;
    competitor_name: string;
    domain: string;
  }>,
): WorkflowStep[] {
  const progress = source.stage_progress ?? {};
  const isRunning = source.status === "running";
  const isFailed = source.status === "failed" || run?.status === "failed";
  const isComplete = run?.status.toLowerCase() === "completed";
  const relevantCards = cards;
  const waitingCards = relevantCards.filter((card) =>
    pendingStatuses.has(card.status),
  );
  const rejectedCards = relevantCards.filter(
    (card) => card.status === "rejected",
  );
  const allReviewed = relevantCards.length > 0 && waitingCards.length === 0;

  const stateFor = (key: string): StepState => {
    if (isFailed && source.current_stage === key) return "failed";
    const saved = progress[key]?.status;
    if (saved === "completed") return "done";
    if (saved === "skipped") return "skipped";
    if (saved === "started" || (isRunning && source.current_stage === key))
      return "active";
    return "waiting";
  };

  const scoreState = stateFor("scoring");
  const evidenceStages = ["uploaded_evidence", "research", "research_evidence"];
  const evidenceFailed =
    isFailed && evidenceStages.includes(source.current_stage);
  const evidenceDone = evidenceStages.every((key) =>
    ["completed", "skipped"].includes(progress[key]?.status ?? ""),
  );
  const evidenceActive = evidenceStages.some(
    (key) =>
      progress[key]?.status === "started" ||
      (isRunning && source.current_stage === key),
  );
  const battlecardState = relevantCards.length
    ? "done"
    : stateFor("battlecards");
  const approvalState: StepState = waitingCards.length
    ? "active"
    : allReviewed
      ? rejectedCards.length === relevantCards.length
        ? "rejected"
        : "done"
      : isComplete
        ? "skipped"
        : "waiting";

  return [
    { label: "File received", state: "done", detail: source.original_filename },
    {
      label: "Rows validated",
      state: "done",
      detail: `${source.valid_records} valid · ${source.warning_records} warnings · ${source.invalid_records} invalid`,
    },
    {
      label: "Competitor queue",
      state: scoreState,
      detail: run
        ? `${run.scoring_results.length} competitors scored`
        : "Run the validated source to score competitors",
    },
    {
      label: "Evidence hub",
      state: evidenceFailed
        ? "failed"
        : evidenceDone
          ? "done"
          : evidenceActive
            ? "active"
            : isComplete
              ? "skipped"
              : "waiting",
      detail: run
        ? `${run.source_urls.length} source URLs in this run`
        : "Evidence is collected after scoring",
    },
    {
      label: "Battlecards",
      state: battlecardState,
      detail: relevantCards.length
        ? `${relevantCards.length} draft${relevantCards.length === 1 ? "" : "s"} saved`
        : isComplete
          ? "No competitor met the draft rules"
          : "Drafts require score ≥70 and usable evidence",
    },
    {
      label: "Human approval",
      state: approvalState,
      detail: waitingCards.length
        ? `${waitingCards.length} waiting · ${relevantCards.length - waitingCards.length} reviewed`
        : allReviewed
          ? `${relevantCards.length} decision${relevantCards.length === 1 ? "" : "s"} recorded`
          : isComplete
            ? "No draft needs approval"
            : "Starts after eligible drafts are saved",
    },
  ];
}

function StepMark({ state }: { state: StepState }) {
  if (state === "done") return <CheckCircle2 size={16} />;
  if (state === "rejected" || state === "failed") return <XCircle size={16} />;
  if (state === "active") return <Clock3 size={16} />;
  if (state === "skipped")
    return <span className="workflow-step-skipped">—</span>;
  return <Circle size={15} />;
}

function sourceStatus(
  source: SourceImportRecord,
  run: AgentRunRecord | undefined,
  cards: Array<{
    id: number;
    status: string;
    competitor_name: string;
    domain: string;
  }>,
) {
  if (source.status === "ready") return "Ready to analyze";
  if (source.status === "running")
    return stageLabels[source.current_stage] ?? "Analysis running";
  if (source.status === "failed" || run?.status === "failed")
    return "Run failed · retry available";
  const reviewCards = cards;
  const pendingCount = reviewCards.filter((card) =>
    pendingStatuses.has(card.status),
  ).length;
  if (pendingCount)
    return `${pendingCount} draft${pendingCount === 1 ? "" : "s"} waiting for review`;
  if (reviewCards.length) return "Review decisions saved";
  return "Analysis complete · no draft required";
}

export default function Workspace() {
  const evidence = useApi(getEvidence);
  const cards = useApi(getBattlecards);
  const approvals = useApi(getApprovals);
  const runs = useApi(getAgentRuns);
  const imports = useApi(getSourceImports);
  const hasRunningImport = (imports.data ?? []).some(
    (item) => item.status === "running",
  );
  const refreshImports = imports.refresh;
  const refreshRuns = runs.refresh;
  const refreshCards = cards.refresh;
  const refreshApprovals = approvals.refresh;
  useEffect(() => {
    if (!hasRunningImport) return;
    const timer = window.setInterval(() => {
      void refreshImports();
      void refreshRuns();
      void refreshCards();
      void refreshApprovals();
    }, 2500);
    return () => window.clearInterval(timer);
  }, [
    hasRunningImport,
    refreshImports,
    refreshRuns,
    refreshCards,
    refreshApprovals,
  ]);
  const [expandedImport, setExpandedImport] = useState<string | null>(null);
  const [deletingImport, setDeletingImport] = useState<string | null>(null);
  if (
    evidence.loading ||
    cards.loading ||
    approvals.loading ||
    runs.loading ||
    imports.loading
  )
    return <Loading text="Loading KOMP intelligence workspace..." />;

  const records = evidence.data ?? [];
  const battlecards = cards.data ?? [];
  const pending = (approvals.data ?? []).filter((item) =>
    pendingStatuses.has(item.status),
  );
  const history = runs.data ?? [];
  const latestRun = history[0];
  const legacyRuns = history.filter((run) => !run.import_id);
  const legacyCompetitors = [
    ...new Set(
      legacyRuns.flatMap((run) =>
        run.scoring_results
          .map((item) => item.competitor_name)
          .filter((name): name is string => Boolean(name)),
      ),
    ),
  ];
  const competitors = new Map<string, typeof records>();
  records.forEach((record) =>
    competitors.set(record.domain, [
      ...(competitors.get(record.domain) ?? []),
      record,
    ]),
  );
  const scoreMap = new Map(
    (latestRun?.scoring_results ?? []).map((item) => [item.domain ?? "", item]),
  );
  const highPriority = (latestRun?.scoring_results ?? []).filter(
    (item) => item.priority === "high",
  ).length;
  const activeImports = (imports.data ?? []).filter(
    (item) => item.status === "running",
  ).length;
  const sources = imports.data ?? [];
  const sourceRunHistory = (source: SourceImportRecord) =>
    history.filter((run) => run.import_id === source.import_id);
  const sourceRuns = (source: SourceImportRecord) =>
    sourceRunHistory(source)[0];
  const sourceCards = (source: SourceImportRecord) => {
    const cardIds = new Set(
      sourceRunHistory(source).flatMap((run) => run.battlecard_ids),
    );
    return battlecards.filter((card) => cardIds.has(card.id));
  };
  const competitorDomains = new Set(
    [...competitors.keys(), ...scoreMap.keys()].filter(Boolean),
  );
  const competitorRows = [...competitorDomains]
    .map((domain) => {
      const signals = competitors.get(domain) ?? [];
      return {
        domain,
        name:
          signals[0]?.competitor_name ??
          scoreMap.get(domain)?.competitor_name ??
          domain,
        signals,
        score: scoreMap.get(domain),
      };
    })
    .sort(
      (a, b) =>
        (b.score?.preliminary_score ?? -1) -
          (a.score?.preliminary_score ?? -1) ||
        b.signals.length - a.signals.length,
    )
    .slice(0, 5);
  const errors = [
    evidence.error,
    cards.error,
    approvals.error,
    runs.error,
    imports.error,
  ].filter(Boolean);
  const unavailable = errors.some((item) =>
    item.includes("KOMP API is unavailable") ||
    item.includes("server is temporarily unavailable"),
  );
  const isRefreshing = [
    evidence.refreshing,
    cards.refreshing,
    approvals.refreshing,
    runs.refreshing,
    imports.refreshing,
  ].some(Boolean);
  const refreshAll = async () => {
    await Promise.all([
      evidence.refresh(),
      cards.refresh(),
      approvals.refresh(),
      runs.refresh(),
      imports.refresh(),
    ]);
  };
  const removeSource = async (source: SourceImportRecord) => {
    const confirmed = window.confirm(
      `Permanently delete “${source.original_filename}”? This removes the uploaded file, its analysis runs, scores, linked battlecards, and run-owned evidence from KOMP. Audit history is retained.`,
    );
    if (!confirmed) return;
    setDeletingImport(source.import_id);
    try {
      await deleteSourceImport(source.import_id);
      setExpandedImport(null);
      await imports.refresh();
    } catch (error) {
      window.alert(
        error instanceof Error
          ? error.message
          : "Could not remove this source file.",
      );
    } finally {
      setDeletingImport(null);
    }
  };
  const approvedCount = battlecards.filter(
    (item) => item.status === "approved",
  ).length;
  return (
    <div className="page-stack komp-home">
      <ErrorMessage
        text={
          unavailable
            ? "The server is temporarily unavailable. Please try again in a moment."
            : errors.join(" · ")
        }
      />

      <header className="workspace-heading workspace-hero">
        <div>
          <span className="eyebrow">KOMP · GLOBAL WORKFORCE INTELLIGENCE</span>
          <h2>Your competitor analysis, all in one place.</h2>
          <p>
            Upload a competitor data file. KOMP checks it, finds evidence,
            drafts insights, and brings eligible battlecards here for your
            approval.
          </p>
        </div>
        <div className="workspace-heading-actions">
          <button className="button secondary" onClick={() => void refreshAll()} disabled={isRefreshing} title="Reload saved files, scores, evidence and review decisions. This does not rerun an analysis.">
            <RefreshCw size={14} className={isRefreshing ? "refresh-icon-spin" : ""} /> {isRefreshing ? "Reloading workspace…" : "Reload data"}
          </button>
          <Link className="button primary" to="/import">
            <UploadCloud size={14} /> Upload competitor data
          </Link>
        </div>
      </header>

      <section className="workspace-metrics" aria-label="Workspace summary">
        <Metric
          icon={FileSpreadsheet}
          label="Uploaded source files"
          value={sources.length}
          footnote={
            legacyRuns.length
              ? `${legacyRuns.length} older run${legacyRuns.length === 1 ? "" : "s"} have no file attached`
              : `${history.length} analysis run${history.length === 1 ? "" : "s"} saved`
          }
        />
        <Metric
          icon={Users}
          label="Competitors in runs"
          value={competitorDomains.size}
          footnote={
            legacyRuns.length
              ? "Includes older unlinked score runs"
              : "From saved analysis runs"
          }
        />
        <Metric
          icon={Globe2}
          label="High priority"
          value={highPriority}
          footnote={
            latestRun
              ? latestRun.import_id
                ? "In the latest uploaded-file run"
                : `Legacy run ${latestRun.run_id.slice(0, 8)} · no file linked`
              : "After the first analysis"
          }
        />
        <Metric
          icon={ClipboardCheck}
          label="Need your decision"
          value={pending.length}
          footnote={`${approvedCount} approved and saved`}
        />
      </section>

      {legacyRuns.length > 0 && (
        <aside className="workspace-legacy-notice">
          <span className="workspace-legacy-icon">
            <Clock3 size={17} />
          </span>
          <div>
            <b>
              {legacyRuns.length} older analysis run
              {legacyRuns.length === 1 ? " is" : "s are"} still contributing to
              these results
            </b>
            <p>
              No uploaded file is linked to these runs
              {legacyCompetitors.length
                ? `; they include ${legacyCompetitors.join(", ")}`
                : ""}
              . Delete any test or incorrect run from Run history to clear its
              scores and outputs.
            </p>
          </div>
          <Link to="/audit?legacy=1">
            Review legacy runs <ArrowRight size={13} />
          </Link>
        </aside>
      )}

      {pending.length > 0 && (
        <section className="workspace-next-action">
          <span className="workspace-next-icon">
            <ClipboardCheck size={20} />
          </span>
          <div>
            <span className="eyebrow">NEXT ACTION</span>
            <h3>
              {pending.length} battlecard{pending.length === 1 ? "" : "s"} need
              your review
            </h3>
            <p>
              Review the evidence, then approve, reject, or request a change.
              Your decision is saved.
            </p>
          </div>
          <Link className="button primary" to="/approvals">
            Review now <ArrowRight size={14} />
          </Link>
        </section>
      )}

      <section className="workspace-imports-panel">
        <div className="workspace-section-heading">
          <div>
            <span className="eyebrow">YOUR WORK</span>
            <h3>Uploaded files & history</h3>
            <p>
              Each file shows its current step, results, and saved decisions.
            </p>
          </div>
          <div className="workspace-section-actions">
            <span className="source-count-label">
              {activeImports
                ? `${activeImports} in progress`
                : `${sources.length} file${sources.length === 1 ? "" : "s"}`}
            </span>
            <Link className="text-link" to="/workflow">
              Full workflow <ArrowRight size={13} />
            </Link>
            <Link className="text-link" to="/audit">
              Audit trail <ArrowRight size={13} />
            </Link>
          </div>
        </div>

        {sources.length ? (
          <div className="source-register-list">
            {sources.map((source) => {
              const run = sourceRuns(source);
              const runHistory = sourceRunHistory(source);
              const sourceBattlecards = sourceCards(source);
              const currentRunCards = sourceBattlecards.filter((card) =>
                run?.battlecard_ids.includes(card.id),
              );
              const steps = workflowSteps(source, run, currentRunCards);
              const statusText = sourceStatus(source, run, sourceBattlecards);
              const isOpen = expandedImport === source.import_id;
              const pendingCards = sourceBattlecards.filter((card) =>
                pendingStatuses.has(card.status),
              );
              const reviewedCards = sourceBattlecards.filter(
                (card) => !pendingStatuses.has(card.status),
              );
              const pendingRun = runHistory.find((candidate) =>
                candidate.battlecard_ids.some((id) =>
                  pendingCards.some((card) => card.id === id),
                ),
              );
              let action = {
                label: "Open source",
                to: `/import?import_id=${encodeURIComponent(source.import_id)}`,
                style: "secondary",
              };
              if (source.status === "running")
                action = {
                  label: "Analysis running",
                  to: "#",
                  style: "secondary",
                };
              else if (pendingCards.length && pendingRun)
                action = {
                  label: `Continue review · ${pendingCards.length}`,
                  to: `/approvals?run_id=${encodeURIComponent(pendingRun.run_id)}`,
                  style: "primary",
                };
              else if (source.status === "failed")
                action = {
                  label: "Retry this file",
                  to: `/import?import_id=${encodeURIComponent(source.import_id)}`,
                  style: "secondary",
                };
              else if (source.status === "ready")
                action = {
                  label: "Continue analysis",
                  to: `/import?import_id=${encodeURIComponent(source.import_id)}`,
                  style: "primary",
                };
              else if (reviewedCards.length)
                action = {
                  label: `View ${reviewedCards.length} reviewed card${reviewedCards.length === 1 ? "" : "s"}`,
                  to: `/battlecards?run_id=${encodeURIComponent(run?.run_id ?? "")}`,
                  style: "secondary",
                };
              else if (run)
                action = {
                  label: "Open competitor scores",
                  to: "/competitors",
                  style: "secondary",
                };
              return (
                <article
                  className={`source-register-item ${isOpen ? "is-expanded" : ""}`}
                  key={source.import_id}
                >
                  <div className="source-register-row">
                    <button
                      className="source-row-toggle"
                      onClick={() =>
                        setExpandedImport(isOpen ? null : source.import_id)
                      }
                      aria-expanded={isOpen}
                    >
                      <span className="source-file-icon">
                        <FileSpreadsheet size={19} />
                      </span>
                      <span className="source-main">
                        <b>{source.original_filename}</b>
                        <small>
                          Uploaded {timeLabel(source.created_at)}
                          {run
                            ? ` · Run ${run.run_id.slice(0, 8)}`
                            : " · Validation saved"}
                        </small>
                      </span>
                      <span
                        className={`source-current-state ${source.status === "running" ? "is-running" : source.status === "failed" ? "is-failed" : pendingCards.length ? "is-review" : ""}`}
                      >
                        <i />
                        {statusText}
                      </span>
                      <span className="source-row-count">
                        <b>{source.valid_records}</b>
                        <small>valid rows</small>
                      </span>
                      <span className="source-row-count">
                        <b>{sourceBattlecards.length}</b>
                        <small>drafts</small>
                      </span>
                      <span className="source-expand-icon">
                        {isOpen ? (
                          <ChevronDown size={17} />
                        ) : (
                          <ChevronRight size={17} />
                        )}
                      </span>
                    </button>
                    <div className="source-row-actions">
                      <Link
                        className={`button ${action.style}`}
                        to={action.to}
                        onClick={(event) => {
                          if (action.to === "#") event.preventDefault();
                        }}
                      >
                        {action.label}
                      </Link>
                      <button
                        className="button source-delete-button"
                        onClick={() => void removeSource(source)}
                        disabled={
                          source.status === "running" ||
                          deletingImport === source.import_id
                        }
                        aria-label={`Remove ${source.original_filename}`}
                        title="Remove uploaded file"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                  {isOpen && (
                    <div className="source-register-details">
                      <div className="source-detail-summary">
                        <span>
                          <b>{source.total_records}</b> rows received
                        </span>
                        <span>
                          <b>{source.valid_records}</b> valid
                        </span>
                        <span>
                          <b>{source.warning_records}</b> warnings
                        </span>
                        <span>
                          <b>{source.invalid_records}</b> invalid
                        </span>
                        {run && (
                          <span>
                            <b>{run.source_urls.length}</b> evidence URLs in run
                          </span>
                        )}
                      </div>
                      <ol className="source-stage-list">
                        {steps.map((step, index) => (
                          <li
                            className={`stage-${step.state}`}
                            key={step.label}
                          >
                            <span className="source-stage-mark">
                              <StepMark state={step.state} />
                            </span>
                            <span className="source-stage-copy">
                              <b>
                                {index + 1}. {step.label}
                              </b>
                              <small>{step.detail}</small>
                            </span>
                            <em>
                              {step.state === "done"
                                ? "Complete"
                                : step.state === "active"
                                  ? "In progress"
                                  : step.state === "skipped"
                                    ? "Not required"
                                    : step.state === "rejected"
                                      ? "Rejected"
                                      : step.state === "failed"
                                        ? "Failed"
                                        : "Waiting"}
                            </em>
                          </li>
                        ))}
                      </ol>
                      {sourceBattlecards.length > 0 && (
                        <div className="source-battlecard-history">
                          <b>
                            <Layers3 size={15} /> Saved battlecard decisions
                          </b>
                          {sourceBattlecards.map((card) => (
                            <Link to={`/battlecards/${card.id}`} key={card.id}>
                              <span>
                                {card.competitor_name}
                                <small>{card.domain}</small>
                              </span>
                              <StatusBadge value={card.status} />
                              <ArrowRight size={13} />
                            </Link>
                          ))}
                        </div>
                      )}
                      {source.error_message && (
                        <div className="source-error-note">
                          <XCircle size={15} />
                          {source.error_message}
                        </div>
                      )}
                      <div className="source-detail-footer">
                        <span>
                          <ShieldCheck size={14} /> Run IDs, source links and
                          reviewer actions are saved in KOMP.
                        </span>
                        <Link
                          className={`button ${action.style}`}
                          to={action.to}
                          onClick={(event) => {
                            if (action.to === "#") event.preventDefault();
                          }}
                        >
                          {action.label}
                        </Link>
                      </div>
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        ) : (
          <div className="workspace-first-import">
            <span className="workspace-first-import-icon">
              <FileText size={21} />
            </span>
            <div>
              <b>
                {history.length
                  ? "No files tracked for new analyses yet"
                  : "Start with a competitor data file"}
              </b>
              <p>
                {history.length
                  ? "Earlier analysis results are still available below, but they were created before KOMP started saving each uploaded filename here. New uploads will have full step-by-step history."
                  : "Upload a CSV or Excel export. First, KOMP checks the rows. Then it scores competitors, gathers eligible evidence, and prepares drafts for your review."}
              </p>
            </div>
            <Link className="button primary" to="/import">
              <UploadCloud size={14} /> Choose a file
            </Link>
          </div>
        )}
      </section>

      <section className="workspace-secondary-grid">
        <article className="workspace-panel relative">
          <div className="workspace-panel-heading flex">
            <div className="flex-1">
              <h3>Competitor results</h3>
              <p>
                {latestRun?.import_id
                  ? "Priority scores from the latest uploaded file."
                  : latestRun
                    ? "Priority scores from the latest saved run; the original file is not linked."
                    : "Priority scores are based on uploaded data."}
              </p>
            </div>
            <Link className="flex items-center" to="/competitors">
              See all results <ArrowRight size={13} />
            </Link>
          </div>
          {competitorRows.length ? (
            <div className="table-wrap workspace-table-wrap">
              <table className="workspace-table">
                <thead>
                  <tr>
                    <th>Competitor</th>
                    <th>Score</th>
                    <th>Priority</th>
                    <th>Signals</th>
                  </tr>
                </thead>
                <tbody>
                  {competitorRows.map(({ domain, name, signals, score }) => (
                    <tr key={domain}>
                      <td>
                        <b>{name}</b>
                        <small>{domain}</small>
                      </td>
                      <td>
                        {score ? (
                          <>
                            <b>{score.preliminary_score}</b>
                            <small>of {score.max_score}</small>
                          </>
                        ) : (
                          <span className="muted">Not scored</span>
                        )}
                      </td>
                      <td>
                        {score?.priority ? (
                          <StatusBadge value={score.priority} />
                        ) : (
                          <span className="muted">—</span>
                        )}
                      </td>
                      <td>{signals.length}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="workspace-empty mt-2">
              <span>
                Competitor scores appear here after you upload and run a source from Import & validate.
              </span>
            </div>
          )}
          <div className="workspace-panel-foot flex absolute bottom-0 left-0 right-0 p-3">
            <ShieldCheck size={14} />
            <span className="ml-1 mt-auto">
              KOMP explains each score; public research adds evidence, not score
              points.
            </span>
            <Link to="/evidence">View evidence</Link>
          </div>
        </article>

        <article className="workspace-panel workspace-approval-panel">
          <div className="workspace-panel-heading flex">
            <div className="flex-1">
              <h3>Review & saved decisions</h3>
              <p>Your team makes the final call before export.</p>
            </div>
            <Link className="flex items-center" to="/approvals">
              Open review <ArrowRight size={13} />
            </Link>
          </div>
          <div className="approval-status-grid">
            <div>
              <small>Waiting on you</small>
              <b>{pending.length}</b>
            </div>
            <div>
              <small>Approved</small>
              <b>{approvedCount}</b>
            </div>
            <div>
              <small>Not approved</small>
              <b>
                {
                  battlecards.filter((card) => card.status === "rejected")
                    .length
                }
              </b>
            </div>
          </div>
          <p className="approval-storage-note">
            <ShieldCheck size={15} /> Battlecards and decisions are saved in
            KOMP. Only approved cards can be exported.
          </p>
          <div className="button-row">
            {approvedCount > 0 && (
              <Link
                className="button primary"
                to="/battlecards?status=approved"
              >
                View {approvedCount} approved card
                {approvedCount === 1 ? "" : "s"}
              </Link>
            )}
            <Link className="button secondary" to="/approvals">
              {pending.length
                ? `Review ${pending.length} now`
                : "View decision history"}
            </Link>
          </div>
        </article>
      </section>

      <section className="workspace-method">
        <div className="workspace-method-heading">
          <span className="eyebrow">THE KOMP PROCESS</span>
          <h3>Uploaded data in. Approved competitor insight out.</h3>
          <p>
            Each stage has one job, and the final decision stays with your team.
          </p>
        </div>
        <ol>
          <li>
            <span>01</span>
            <div>
              <b>Upload & validate</b>
              <small>
                Import SEMrush, G2, Capterra, or competitor website exports.
                KOMP checks and normalizes rows.
              </small>
            </div>
          </li>
          <li>
            <span>02</span>
            <div>
              <b>Score & prioritize</b>
              <small>
                Explainable scores use review pain, SEO gaps, product overlap,
                and signal recency.
              </small>
            </div>
          </li>
          <li>
            <span>03</span>
            <div>
              <b>Research & draft</b>
              <small>
                Tavily finds current public proof for eligible competitors; the
                configured LLM drafts a sourced battlecard.
              </small>
            </div>
          </li>
          <li>
            <span>04</span>
            <div>
              <b>Human review</b>
              <small>
                Approve, reject, or request changes. Only approved battlecards
                can be exported.
              </small>
            </div>
          </li>
        </ol>
      </section>
    </div>
  );
}
