import { Link } from "react-router-dom";
import { FileText, Users, Layers3, ClipboardCheck, RefreshCw, UploadCloud, Zap, Clock3, ArrowUpRight, BarChart3 } from "lucide-react";
import { getEvidence } from "../api/evidence";
import { getBattlecards } from "../api/battlecards";
import { getApprovals } from "../api/approvals";
import { useApi } from "../hooks/useApi";
import { EmptyState, ErrorMessage, Loading, StatusBadge } from "../components/common/Feedback";

export default function Workspace() {
  const evidence = useApi(getEvidence);
  const cards = useApi(getBattlecards);
  const approvals = useApi(getApprovals);
  if (evidence.loading || cards.loading || approvals.loading) return <Loading text="Loading KOMP workspace..."/>;
  const records = evidence.data ?? [];
  const battlecards = cards.data ?? [];
  const queue = approvals.data ?? [];
  const competitorCount = new Set(records.map(item => item.domain)).size;
  const errors = [evidence.error, cards.error, approvals.error].filter(Boolean);
  const apiUnavailable = errors.some(item => item.includes("KOMP API is unavailable"));
  const refreshAll = () => { void evidence.refresh(); void cards.refresh(); void approvals.refresh(); };

  return <div className="dashboard page-stack">
    <div className="dashboard-heading">
      <div><p className="greeting">Your intelligence workspace</p><label className="eyebrow">INTELLIGENCE OVERVIEW</label><h2>Competitor intelligence, at a glance.</h2><p className="heading-copy">Track evidence, competitor moves, and human review progress.</p></div>
      <div className="heading-actions"><span className="date-chip"><Clock3 size={14}/> Live workspace</span><button className="button primary" onClick={refreshAll}><RefreshCw size={15}/> Refresh</button></div>
    </div>

    {apiUnavailable
      ? <ErrorMessage text="KOMP API is unavailable. Start the FastAPI backend at http://127.0.0.1:8000, then refresh this page."/>
      : errors.length > 0 ? <ErrorMessage text={errors.join(" · ")}/> : null}

    <div className="metric-grid dashboard-metrics">
      <Metric icon={<Users/>} label="Tracked competitors" value={competitorCount}/>
      <Metric icon={<FileText/>} label="Evidence records" value={records.length}/>
      <Metric icon={<Layers3/>} label="Battlecards" value={battlecards.length}/>
      <Metric icon={<ClipboardCheck/>} label="Pending approvals" value={queue.filter(item => ["pending_review","pending","changes_requested"].includes(item.status)).length}/>
    </div>

    <section className="workflow-panel panel">
      <div className="workflow-intro"><h3>Workflow</h3><p>From source import to human-approved battlecards.</p></div>
      <div className="workflow-steps">
        <WorkflowStep number="01" title="Import sources" detail="CSV, XLSX or URLs" icon={<UploadCloud/>} to="/import"/>
        <span className="workflow-arrow">→</span>
        <WorkflowStep number="02" title="Extract evidence" detail="Validate competitor signals" icon={<FileText/>} to="/evidence"/>
        <span className="workflow-arrow">→</span>
        <WorkflowStep number="03" title="Generate battlecard" detail="AI-assisted analysis" icon={<Zap/>} to="/battlecards"/>
        <span className="workflow-arrow">→</span>
        <WorkflowStep number="04" title="Human approval" detail="Review before use" icon={<ClipboardCheck/>} to="/approvals"/>
      </div>
    </section>

    <div className="dashboard-main-grid">
      <section className="panel evidence-panel">
        <div className="panel-heading"><div className="heading-with-icon"><span className="section-icon"><BarChart3 size={18}/></span><div><h3>Latest Evidence</h3><p>Recently processed competitor signals</p></div></div><Link className="text-link" to="/evidence">View all <ArrowUpRight size={13}/></Link></div>
        {records.length ? <div className="table-wrap"><table><thead><tr><th>Competitor</th><th>Signal / Insight</th><th>Source</th><th>Date</th><th>Status</th></tr></thead><tbody>
          {records.slice(0,6).map(item => <tr key={item.id}><td><b>{item.competitor_name}</b><small>{item.domain}</small></td><td className="signal-cell">{item.signal_text}</td><td><span className="source-pill">{item.source_type}</span></td><td>{item.signal_date || "—"}</td><td><StatusBadge value={item.status || "valid"}/></td></tr>)}
        </tbody></table></div> : <EmptyState title="Record not found" text="Import a CSV or XLSX source to start building your evidence library."/>}
      </section>

      <aside className="dashboard-side">
        <section className="panel quick-panel"><div className="panel-heading"><div><h3>Quick Actions</h3><p>Common tasks to get started</p></div><Zap size={18}/></div>
          <Link className="quick-action featured" to="/import"><UploadCloud size={18}/><span><b>Import Sources</b><small>Upload CSV or XLSX files</small></span><ArrowUpRight size={14}/></Link>
          <Link className="quick-action" to="/battlecards"><Layers3 size={18}/><span><b>Open Battlecard Studio</b><small>Review competitor drafts</small></span><ArrowUpRight size={14}/></Link>
          <Link className="quick-action" to="/approvals"><ClipboardCheck size={18}/><span><b>Review Approvals</b><small>Human review queue</small></span><ArrowUpRight size={14}/></Link>
        </section>
        <section className="panel activity-panel"><div className="panel-heading"><div><h3>Recent Activity</h3><p>Latest workspace records</p></div><Clock3 size={18}/></div>
          {records.length || battlecards.length || queue.length ? <div className="activity-list">
            {records.slice(0,3).map(item=><div className="activity-item" key={`e-${item.id}`}><span className="activity-icon"><FileText size={15}/></span><span><b>Evidence added</b><small>{item.competitor_name} · {item.source_type}</small></span></div>)}
            {battlecards.slice(0,2).map(item=><div className="activity-item" key={`b-${item.id}`}><span className="activity-icon purple"><Layers3 size={15}/></span><span><b>Battlecard draft</b><small>{item.competitor_name} · {item.status}</small></span></div>)}
          </div> : <EmptyState title="Record not found" text="Imports, analysis runs and approval activity will appear here."/>}
        </section>
      </aside>
    </div>

    <section className="panel battlecard-panel"><div className="panel-heading"><div className="heading-with-icon"><span className="section-icon"><Layers3 size={18}/></span><div><h3>Recent Battlecards</h3><p>AI-assisted drafts waiting for review</p></div></div><Link className="text-link" to="/battlecards">Open studio <ArrowUpRight size={13}/></Link></div>
      {battlecards.length ? <div className="card-grid m-2">{battlecards.slice(0,4).map(card=><Link className="mini-card" to={`/battlecards/${card.id}`} key={card.id}><StatusBadge value={card.status}/><b>{card.competitor_name}</b><small>{card.domain}</small><span className="text-link">Open battlecard →</span></Link>)}</div> : <EmptyState title="Record not found" text="Run competitor analysis after importing valid evidence to generate a battlecard draft."/>}
    </section>
  </div>;
}
function Metric({icon,label,value}:{icon:React.ReactNode;label:string;value:number}) {
  return <article className="metric-card"><span className="metric-icon">{icon}</span><div><small>{label}</small><b>{value}</b></div><span className="metric-trend">—</span></article>;
}
function WorkflowStep({number,title,detail,icon,to}:{number:string;title:string;detail:string;icon:React.ReactNode;to:string}) {
  return <Link className="workflow-step" to={to}><span className="workflow-icon">{icon}</span><span className="workflow-number">{number}</span><b>{title}</b><small>{detail}</small></Link>;
}
