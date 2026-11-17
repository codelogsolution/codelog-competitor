import { useEffect, useRef, useState } from "react";
import { Play, RotateCcw, UploadCloud, ArrowRight, Sparkles } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";
import {
  uploadCompetitorFile,
  runCompetitorAgent,
  type UploadResult,
  type AgentResult,
} from "../api/uploads";
import { getSourceImport } from "../api/sourceImports";
import { ErrorMessage, StatusBadge } from "../components/common/Feedback";
import { useAnalysisRun } from "../contexts/AnalysisRunContext";

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <article className="metric-card">
      <small>{label}</small>
      <b>{value}</b>
    </article>
  );
}

function describeValidationIssue(item: unknown): string {
  if (typeof item === "string") return item;
  if (!item || typeof item !== "object") return String(item);
  const issue = item as { row?: number; message?: string };
  const message = issue.message ?? "This row needs a quick review.";
  const signalType = message.match(/^Unknown signal_type: (.+)$/i)?.[1];
  const sourceType = message.match(/^Unknown source_type: (.+)$/i)?.[1];
  const friendly = signalType
    ? `Signal category “${signalType}” needs review. This row won't affect the competitor score.`
    : sourceType
      ? `Source “${sourceType}” isn't recognized yet. Check the source type before using this row.`
      : message === "Source URL missing; manual evidence review required"
        ? "Add a source link, or review this evidence manually."
        : message === "Signal date missing or invalid"
          ? "Add a valid date so KOMP can judge how recent this signal is."
          : message;
  return `${issue.row ? `Row ${issue.row} · ` : ""}${friendly}`;
}

export default function ImportSources() {
  const { setIsRunning, setStageStatus, resetStages } = useAnalysisRun();
  const fileInput = useRef<HTMLInputElement>(null);
  const [searchParams] = useSearchParams();
  const requestedImportId = searchParams.get("import_id");
  const [file, setFile] = useState<File | null>(null);
  const [validation, setValidation] = useState<UploadResult | null>(null);
  const [agent, setAgent] = useState<AgentResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!requestedImportId || validation?.import_id === requestedImportId) return;
    let active = true;
    getSourceImport(requestedImportId)
      .then(result => {
        if (active) {
          setFile(null);
          setValidation(result);
          setAgent(null);
        }
      })
      .catch(err => {
        if (active) setError(err instanceof Error ? err.message : "Could not reopen this source import.");
      });
    return () => { active = false; };
  }, [requestedImportId, validation?.import_id]);

  async function handleUpload() {
    if (!file) return;
    setBusy(true);
    setError("");
    setAgent(null);
    try {
      setValidation(await uploadCompetitorFile(file));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleRun() {
    if (!validation?.records?.length) return;
    setBusy(true);
    resetStages();
    setIsRunning(true);
    setStageStatus("validation", "completed", "Upload validation is complete.");
    setError("");
    try {
      setAgent(await runCompetitorAgent(validation.records, (event) => {
        if (event.type === "progress" && event.stage && event.status) {
          setStageStatus(event.stage, event.status, event.message);
        }
      }, validation.import_id, validation.original_filename ?? file?.name));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Agent run failed");
    } finally {
      setBusy(false);
      setIsRunning(false);
    }
  }

  const restoringImport = Boolean(requestedImportId && validation?.import_id !== requestedImportId);

  return (
    <div className="page-stack">
      <section className="workflow-progress" aria-label="Analysis workflow">
        <div className={`workflow-progress-step ${file ? "is-complete" : "is-current"}`}><span>1</span><div><b>Upload</b><small>Choose a source file</small></div></div>
        <div className={`workflow-progress-step ${validation ? "is-complete" : file ? "is-current" : ""}`}><span>2</span><div><b>Validate</b><small>Check rows and warnings</small></div></div>
        <div className={`workflow-progress-step ${agent ? "is-complete" : validation ? "is-current" : ""}`}><span>3</span><div><b>Analyse</b><small>Score and research</small></div></div>
        <div className={`workflow-progress-step ${agent?.battlecard_results?.length ? "is-current" : ""}`}><span>4</span><div><b>Review</b><small>Approve drafts</small></div></div>
      </section>
      {restoringImport && <div className="notice">Reopening the saved source file and its validated rows so you can continue this run.</div>}
      <section className="intelligence-intro">
        <div>
          <span className="eyebrow">KOMP INTELLIGENCE WORKSPACE</span>
          <h2>Turn competitor signals into evidence-backed decisions.</h2>
          <p>Upload an export. KOMP checks the data, scores competitors, researches eligible companies, and prepares drafts for your team to review.</p>
        </div>
        <div className="intelligence-intro-badge"><Sparkles size={16}/><span>Research is selective<br/><small>Only high-priority competitors are researched</small></span></div>
      </section>
      <section className="panel">
        <label className="eyebrow">IMPORT SOURCES</label>
        <h2>Upload competitor data</h2>
        <p className="muted">
          Upload SEMrush, G2, Capterra or manually prepared competitor website data (CSV / XLSX).
        </p>
        <div className="sample-downloads">
          <b>Try a sample CSV</b>
          <span>All records are synthetic. High-priority examples may call Tavily and your configured LLM.</span>
          <div>
            <a href="/sample-data/synthetic_high_priority_only.csv" download>High only · score 95</a>
            <a href="/sample-data/synthetic_g2_capterra_reviews.csv" download>High + medium · reviews</a>
            <a href="/sample-data/synthetic_mixed_end_to_end.csv" download>Mixed · high + medium</a>
            <a href="/sample-data/synthetic_semrush_keyword_gaps.csv" download>Other · SEO medium</a>
            <a href="/sample-data/synthetic_website_signals.csv" download>Other · website signals</a>
          </div>
        </div>
        <div className="supported-source-note"><b>What can I upload?</b><span>CSV and XLSX are supported. A website URL can be recorded as evidence in the <code>source_url</code> column, but KOMP does not fetch page content from a pasted URL yet. Tavily searches public sources for eligible high-priority competitors. PDF, Word, and other document uploads are not supported yet.</span></div>
        <div className="dropzone">
          <UploadCloud size={30} />
          <b>{file?.name ?? "Drop your file here"}</b>
          <p>{file ? "File selected" : "CSV or XLSX · Maximum 10 MB"}</p>
          <input
            ref={fileInput}
            hidden
            type="file"
            accept=".csv,.xlsx"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <button className="button secondary" onClick={() => fileInput.current?.click()}>
            Choose file
          </button>
        </div>
        <div className="button-row">
          <button
            className="button primary"
            disabled={!file || busy || restoringImport}
            onClick={() => void handleUpload()}
          >
            <UploadCloud size={15} />
              {restoringImport ? "Restoring saved source..." : busy ? "Uploading..." : "Upload and validate"}
          </button>
          <button
            className="button ghost"
            onClick={() => {
              setFile(null);
              setValidation(null);
              setAgent(null);
              setError("");
              if (fileInput.current) fileInput.current.value = "";
            }}
          >
            <RotateCcw size={15} /> Reset
          </button>
        </div>
        <ErrorMessage text={error} />
      </section>

      {validation && (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h3>Validation summary</h3>
              <p>{validation.original_filename ?? validation.filename ?? file?.name}</p>
            </div>
            <StatusBadge value={validation.success ? "valid" : "warning"} />
          </div>
          <div className="metric-grid compact">
            <Metric label="Total rows" value={validation.total_records} />
            <Metric label="Valid rows" value={validation.valid_records} />
            <Metric label="Invalid rows" value={validation.invalid_records} />
            <Metric label="Warnings" value={validation.warning_records ?? 0} />
          </div>
          {validation.errors?.length ? (
            <div className="notice">
              <b>Rows needing correction</b>
              {validation.errors.slice(0, 10).map((item, index) => (
                <p key={`error-${index}`}>{describeValidationIssue(item)}</p>
              ))}
            </div>
          ) : null}
          {validation.warnings?.length ? (
            <div className="notice validation-review-notice">
              <b>Some rows need a quick review</b>
              <small>These rows are saved with your source file for review and excluded from scoring in this analysis run.</small>
              {validation.warnings.slice(0, 10).map((item, index) => (
                <p key={`warning-${index}`}>{describeValidationIssue(item)}</p>
              ))}
              {(validation.warnings?.length ?? 0) > 10 && <small>And {validation.warnings!.length - 10} more rows. Open the validation details to review the full list.</small>}
            </div>
          ) : null}
          <button
            className="button primary mt-4"
            disabled={busy || restoringImport || validation.valid_records < 1}
            onClick={() => void handleRun()}
          >
            <Play size={15} />
            {restoringImport
              ? "Restoring saved source..."
              : busy
              ? "Running analysis..."
              : validation.valid_records > 0
                ? `Run analysis using ${validation.valid_records} valid rows`
                : "No valid rows available"}
          </button>
          {validation.valid_records > 0 && !agent && (
            <p className="analysis-next-hint">Run the analysis to unlock your evidence and competitor results.</p>
          )}
        </section>
      )}

      {agent && (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h3>Analysis complete</h3>
              <p>{agent.run_id ? `Run reference: ${agent.run_id}` : "Your analysis results are ready."}</p>
            </div>
            <StatusBadge value={agent.status} />
          </div>
          <div className="metric-grid compact">
            <Metric label="Scored" value={agent.scoring_results?.length ?? 0} />
            <Metric label="Research results" value={agent.research_results?.length ?? 0} />
            <Metric label="Evidence returned" value={agent.evidence_results?.length ?? 0} />
            <Metric label="Battlecards" value={agent.battlecard_results?.length ?? 0} />
          </div>
          {(agent.scoring_results?.length ?? 0) > 0 && (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Competitor</th>
                    <th>Score</th>
                    <th>Priority</th>
                    <th>Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {agent.scoring_results.map((item) => (
                    <tr key={item.domain}>
                      <td>
                        <b>{item.competitor_name}</b>
                        <small>{item.domain}</small>
                      </td>
                      <td>{item.preliminary_score}/{item.max_score}</td>
                      <td><StatusBadge value={item.priority} /></td>
                      <td>{item.evidence_count ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {(agent.research_results?.length ?? 0) > 0 && (
            <section className="research-results-panel">
              <div className="panel-heading"><div><h3>AI research & source evidence</h3><p>Public research is shown separately from uploaded evidence.</p></div></div>
              {agent.research_results.map((item, index) => {
                const research = item as { competitor_name?: string; domain?: string; status?: string; message?: string; sources?: Array<{ title?: string; url?: string }> };
                return <article className="research-result-row" key={`${research.domain ?? "research"}-${index}`}>
                  <div><b>{research.competitor_name ?? research.domain ?? "Competitor research"}</b><small>{research.message ?? research.status ?? "Research finished"}</small></div>
                  <div className="research-source-links">{research.sources?.length ? research.sources.slice(0, 3).map((source, sourceIndex) => source.url ? <a key={`${source.url}-${sourceIndex}`} href={source.url} target="_blank" rel="noreferrer">{source.title || "Open source"} <ArrowRight size={12}/></a> : null) : <StatusBadge value={research.status ?? "no sources"}/>}</div>
                </article>;
              })}
            </section>
          )}
          {(agent.errors?.length ?? 0) > 0 && (
            <div className="notice">
              <b>Workflow messages</b>
              {agent.errors.map((message, index) => (
                <p key={index}>{message}</p>
              ))}
            </div>
          )}
          <div className="button-row mt-4">
            {agent.status === "completed" && agent.battlecard_results?.length > 0 && (
              <Link className="button primary" to="/battlecards">
                <ArrowRight size={14} /> Next: View Battlecards
              </Link>
            )}
            {agent.status === "completed" && agent.battlecard_results?.length === 0 && (
              <span className="notice">
                No battlecards generated — only high-priority competitors (score ≥ 70) get battlecards.
              </span>
            )}
            {agent.status === "completed" && <Link className="button secondary" to="/evidence">
              <ArrowRight size={14} /> View Evidence
            </Link>}
          </div>
        </section>
      )}
    </div>
  );
}
