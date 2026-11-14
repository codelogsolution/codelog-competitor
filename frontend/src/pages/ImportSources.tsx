import { useRef, useState } from "react";
import { Play, RotateCcw, UploadCloud } from "lucide-react";
import { uploadCompetitorFile, runCompetitorAgent, type UploadResult, type AgentResult } from "../api/uploads";
import { ErrorMessage, StatusBadge } from "../components/common/Feedback";

export default function ImportSources() {
  const fileInput = useRef<HTMLInputElement>(null);
  const [file,setFile] = useState<File|null>(null);
  const [validation,setValidation] = useState<UploadResult|null>(null);
  const [agent,setAgent] = useState<AgentResult|null>(null);
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState("");

  async function handleUpload() {
    if (!file) return;
    setBusy(true); setError(""); setAgent(null);
    try { setValidation(await uploadCompetitorFile(file)); }
    catch (err) { setError(err instanceof Error ? err.message : "Upload failed"); }
    finally { setBusy(false); }
  }

  async function handleRun() {
    if (!validation?.records?.length) return;
    setBusy(true); setError("");
    try { setAgent(await runCompetitorAgent(validation.records)); }
    catch (err) { setError(err instanceof Error ? err.message : "Agent run failed"); }
    finally { setBusy(false); }
  }

  return <div className="page-stack">
    <section className="panel">
      <label className="eyebrow">DATA INGESTION</label><h2>Import competitor sources</h2>
      <p className="muted">Upload SEMrush, G2, Capterra or manually collected CSV/XLSX data.</p>
      <p className="sample-download"><a href="/demo_competitor_data.csv" download>Download demo CSV</a><span> · Contains clearly labelled synthetic test records</span></p>
      <div className="dropzone" onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); setFile(event.dataTransfer.files[0] ?? null); }}>
        <UploadCloud size={30}/><b>{file?.name ?? "Drop your file here"}</b><p>{file ? "File selected" : "CSV or XLSX · Maximum 10 MB"}</p>
        <input ref={fileInput} hidden type="file" accept=".csv,.xlsx" onChange={event => setFile(event.target.files?.[0] ?? null)}/>
        <button className="button secondary" onClick={() => fileInput.current?.click()}>Choose file</button>
      </div>
      <div className="button-row">
        <button className="button primary" disabled={!file || busy} onClick={() => void handleUpload()}><UploadCloud size={15}/>{busy ? "Uploading..." : "Upload and validate"}</button>
        <button className="button ghost" onClick={() => { setFile(null); setValidation(null); setAgent(null); setError(""); if (fileInput.current) fileInput.current.value = ""; }}><RotateCcw size={15}/> Reset</button>
      </div>
      <ErrorMessage text={error}/>
    </section>

    {validation && <section className="panel">
      <div className="panel-heading"><div><h3>Validation summary</h3><p>{validation.filename ?? file?.name}</p></div><StatusBadge value={validation.success ? "valid" : "warning"}/></div>
      <div className="metric-grid compact">
        <Metric label="Total rows" value={validation.total_records}/><Metric label="Valid rows" value={validation.valid_records}/><Metric label="Invalid rows" value={validation.invalid_records}/><Metric label="Warnings" value={validation.warning_records ?? 0}/>
      </div>
      {!!validation.errors?.length && <div className="notice"><b>Validation messages</b>{validation.errors.slice(0,10).map((item,index)=><p key={index}>{typeof item === "string" ? item : JSON.stringify(item)}</p>)}</div>}
      <button className="button primary mt-4" disabled={busy || !validation.records?.length} onClick={() => void handleRun()}><Play size={15}/>{busy ? "Running agent..." : "Run competitor analysis"}</button>
    </section>}

    {agent && <section className="panel">
      <div className="panel-heading"><h3>Agent execution result</h3><StatusBadge value={agent.status}/></div>
      <div className="metric-grid compact">
        <Metric label="Scored" value={agent.scoring_results?.length ?? 0}/><Metric label="Research results" value={agent.research_results?.length ?? 0}/><Metric label="Evidence returned" value={agent.evidence_results?.length ?? 0}/><Metric label="Battlecards" value={agent.battlecard_results?.length ?? 0}/>
      </div>
      {!!agent.scoring_results?.length && <div className="table-wrap"><table><thead><tr><th>Competitor</th><th>Score</th><th>Priority</th><th>Evidence</th></tr></thead><tbody>{agent.scoring_results.map(item=><tr key={item.domain}><td><b>{item.competitor_name}</b><small>{item.domain}</small></td><td>{item.preliminary_score}/{item.max_score}</td><td><StatusBadge value={item.priority}/></td><td>{item.evidence_count ?? "—"}</td></tr>)}</tbody></table></div>}
      {!!agent.errors?.length && <div className="notice"><b>Workflow messages</b>{agent.errors.map((message,index)=><p key={index}>{message}</p>)}</div>}
    </section>}
  </div>;
}

function Metric({label,value}:{label:string;value:number}) { return <article className="metric-card"><small>{label}</small><b>{value}</b></article>; }
