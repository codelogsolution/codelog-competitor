import { Suspense, useState } from "react";
import { createPortal } from "react-dom";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  LayoutDashboard, UploadCloud, Users, FileText, Layers3, Globe2, CheckCircle2, Circle,
  Menu, X, History, Download
} from "lucide-react";
import { useAnalysisRun, type AnalysisStageMap } from "../../contexts/AnalysisRunContext";
import { Loading } from "../common/Feedback";

const primaryNavigation = [
  { to: "/", label: "Workspace", icon: LayoutDashboard },
  { to: "/import", label: "Import & validate", icon: UploadCloud },
  { to: "/workflow", label: "Workflow & files", icon: FileText },
  { to: "/competitors", label: "Competitor scores", icon: Users },
  { to: "/evidence", label: "Evidence", icon: FileText },
  { to: "/battlecards", label: "Insight Studio", icon: Layers3 },
  { to: "/approvals", label: "Review & export", icon: Download },
  { to: "/audit", label: "Audit trail", icon: History },
];

const analysisSteps = [
  { key: "validation", label: "Validate source rows", stages: ["validation"], note: "Checking the uploaded data." },
  { key: "scoring", label: "Score competitors", stages: ["scoring"], note: "Calculating explainable priority scores." },
  { key: "evidence", label: "Gather evidence and research", stages: ["uploaded_evidence", "research", "research_evidence"], note: "Saving supplied evidence and researching eligible competitors." },
  { key: "battlecards", label: "Prepare battlecard drafts", stages: ["battlecards", "complete"], note: "Creating drafts only when score and evidence rules are met." },
];

function analysisStepState(stages: AnalysisStageMap, stepStages: string[]) {
  const statuses = stepStages.map(stage => stages[stage]?.status);
  if (statuses.includes("started")) return "active";
  if (statuses.every(status => status === "completed" || status === "skipped")) {
    return statuses.includes("completed") ? "completed" : "skipped";
  }
  if (statuses.some(Boolean)) return "active";
  return "waiting";
}

function analysisStepMessage(stages: AnalysisStageMap, stepStages: string[], fallback: string) {
  return [...stepStages].reverse().map(stage => stages[stage]?.message).find(Boolean) ?? fallback;
}

const pageTitles: Record<string, [string, string]> = {
  "/": ["Workspace", "KOMP global workforce · EOR and COR competitor intelligence"],
  "/import": ["Import & validate", "Upload your source exports, check the rows, then run analysis."],
  "/competitors": ["Competitor scores", "See priorities, score reasons and the evidence behind them."],
  "/evidence": ["Evidence", "Review uploaded and public sources behind competitor insights."],
  "/battlecards": ["Insight Studio", "Review sourced competitor insights and draft battlecards."],
  "/approvals": ["Review & export", "Approve drafts before exporting them for business use."],
  "/audit": ["Audit trail", "See what each KOMP run generated and who changed a review decision."],
  "/workflow": ["Workflow & files", "Track each uploaded source, its current step, and its saved decision."],
};

export default function AppLayout() {
  const { isRunning, stages } = useAnalysisRun();
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const [title, subtitle] = pageTitles[location.pathname] ?? ["KOMP", "Competitor intelligence workspace."];
  return (
    <div className="app-shell redesigned-shell">
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`} inert={isRunning}>
        <div className="brand">
          <span className="brand-logo komp-brand-mark" aria-hidden="true">K</span>
          <span><b>KOMP</b><small>GLOBAL WORKFORCE</small></span>
          <button className="mobile-close" onClick={() => setMenuOpen(false)} aria-label="Close menu"><X size={18}/></button>
        </div>
        <p className="nav-caption">MARKET INTELLIGENCE</p>
        <nav>
          {primaryNavigation.map(({to,label,icon:Icon}) => (
            <NavLink key={to} to={to} end={to === "/"} onClick={() => setMenuOpen(false)}
              className={({isActive}) => `nav-item ${isActive ? "active" : ""}`}>
              <Icon size={17}/><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <span className="online-dot"/> Uploaded sources only
          <small>Human approval before export</small>
        </div>
      </aside>
      {menuOpen && <button className="mobile-shade" onClick={() => setMenuOpen(false)} aria-label="Close menu overlay"/>}
      <main className="main-area" inert={isRunning}>
        <header className="topbar redesigned-topbar">
          <button className="mobile-menu" onClick={() => setMenuOpen(true)} aria-label="Open menu"><Menu/></button>
          <div className="topbar-title"><h1>{title}</h1><p>{subtitle}</p></div>
          <div className="topbar-context"><Globe2 size={14}/> EOR + COR intelligence</div>
        </header>
        <div className="page-content redesigned-content">
          <Suspense fallback={<Loading text="Opening this section..."/>}>
            <Outlet/>
          </Suspense>
        </div>
        <footer className="footer redesigned-footer"><span>KOMP</span> Competitor Intelligence <small>Private workspace · Human-reviewed insights</small></footer>
      </main>
      {isRunning && <div className="workspace-run-shield" aria-hidden="true" />}
      {isRunning && createPortal(
        <div className="analysis-run-overlay" role="dialog" aria-modal="true" aria-labelledby="analysis-run-title">
          <section className="analysis-run-dialog">
            <span className="eyebrow">SOURCE ANALYSIS</span>
            <h2 id="analysis-run-title">Analysis in progress</h2>
            <p className="analysis-run-copy">KOMP completes one stage at a time. Public research runs only for competitors that meet the priority rules.</p>
            <div className="analysis-run-steps">
              {analysisSteps.map((step, index) => {
                const status = analysisStepState(stages, step.stages);
                const description = analysisStepMessage(stages, step.stages, step.note);
                return <div className={`analysis-run-stage is-${status}`} key={step.key}>
                  <span className="analysis-stage-icon">{status === "completed" ? <CheckCircle2 size={17}/> : status === "skipped" ? <span className="analysis-stage-dash">—</span> : status === "active" ? <span className="analysis-stage-number">{index + 1}</span> : <Circle size={15}/>}</span>
                  <span><b>{step.label}</b><small>{description}</small></span>
                  <em>{status === "active" ? "In progress" : status === "completed" ? "Completed" : status === "skipped" ? "Not needed" : "Up next"}</em>
                </div>;
              })}
            </div>
            <div className="analysis-run-footer">Next: review saved drafts. Nothing is exported until a person approves it.</div>
          </section>
        </div>, document.body,
      )}
    </div>
  );
}
