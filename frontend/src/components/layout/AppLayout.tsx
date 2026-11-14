import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { LayoutDashboard, UploadCloud, Users, FileText, Layers3, ClipboardCheck, History, Menu, X, Bell, ChevronDown } from "lucide-react";
import brandMark from "../../assets/codelogsolution-mark.svg";

const navigation = [
  { to: "/", label: "Workspace", icon: LayoutDashboard },
  { to: "/import", label: "Import Sources", icon: UploadCloud },
  { to: "/competitors", label: "Competitor Queue", icon: Users },
  { to: "/evidence", label: "Evidence Hub", icon: FileText },
  { to: "/battlecards", label: "Battlecard Studio", icon: Layers3 },
  { to: "/approvals", label: "Approvals", icon: ClipboardCheck },
  { to: "/audit", label: "Audit History", icon: History },
];
const pageTitles: Record<string, [string, string]> = {
  "/": ["Workspace", "Competitor intelligence overview and recent activity."],
  "/import": ["Import Sources", "Upload and validate competitor source files."],
  "/competitors": ["Competitor Queue", "Review competitor signals and scoring results."],
  "/evidence": ["Evidence Hub", "Explore uploaded and researched evidence."],
  "/battlecards": ["Battlecard Studio", "Review AI-generated competitor battlecards."],
  "/approvals": ["Approvals", "Human review of generated battlecards."],
  "/audit": ["Audit History", "Trace review actions and status changes."],
};
export default function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const [title, subtitle] = pageTitles[location.pathname] ?? ["KOMP", "Competitor intelligence workspace."];
  return <div className="app-shell">
    <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
      <div className="brand">
        <img className="brand-logo" src={brandMark} alt="CodeLogSolution logo"/>
        <span><b>CodeLogSolution</b><small>COMPETITOR INTELLIGENCE</small></span>
        <button className="mobile-close" onClick={() => setMenuOpen(false)} aria-label="Close menu"><X size={18}/></button>
      </div>
      <p className="nav-caption">KOMP WORKSPACE</p>
      <nav>{navigation.map(({to,label,icon:Icon}) => <NavLink key={to} to={to} end={to === "/"} onClick={() => setMenuOpen(false)} className={({isActive}) => `nav-item ${isActive ? "active" : ""}`}><Icon size={18}/><span>{label}</span></NavLink>)}</nav>
      <div className="sidebar-foot"><span className="online-dot"/> API workspace<small>Human-reviewed intelligence</small></div>
    </aside>
    {menuOpen && <button className="mobile-shade" onClick={() => setMenuOpen(false)} aria-label="Close menu overlay"/>}
    <main className="main-area">
      <header className="topbar">
        <button className="mobile-menu" onClick={() => setMenuOpen(true)} aria-label="Open menu"><Menu/></button>
        <div><h1>{title}</h1><p>{subtitle}</p></div>
        <div className="topbar-user"><button className="icon-button" aria-label="Notifications"><Bell size={18}/></button><span className="avatar">SY</span><span className="user-name">Workspace Admin<small>CodeLogSolution</small></span><ChevronDown size={14}/></div>
      </header>
      <div className="page-content"><Outlet/></div>
      <footer className="footer"><span>CodeLogSolution</span><i>·</i> KOMP Competitor Intelligence <small>v0.1.0 · Local workspace</small></footer>
    </main>
  </div>;
}
