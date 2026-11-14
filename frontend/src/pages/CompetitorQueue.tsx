import { Fragment, useMemo, useState } from "react";
import { ChevronDown, ChevronRight, RefreshCw, Search, SlidersHorizontal } from "lucide-react";
import { getCompetitors } from "../api/competitors";
import { useApi } from "../hooks/useApi";
import { EmptyState, ErrorMessage, Loading, StatusBadge } from "../components/common/Feedback";

const PAGE_SIZE = 10;

export default function CompetitorQueue() {
  const { data, loading, error, refresh } = useApi(getCompetitors);
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => (data ?? [])
    .filter(item => `${item.competitor_name} ${item.domain}`.toLowerCase().includes(query.trim().toLowerCase()))
    .sort((a, b) => a.competitor_name.localeCompare(b.competitor_name)), [data, query]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const visible = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  function updateQuery(value: string) {
    setQuery(value);
    setPage(1);
    setExpanded(null);
  }

  if (loading) return <Loading text="Loading competitor records..."/>;

  return <div className="page-stack queue-page">
    <div className="queue-heading">
      <div>
        <span className="eyebrow">COMPETITOR INTELLIGENCE</span>
        <h2>Competitor Queue</h2>
        <p className="heading-copy">A consolidated view of competitors and their available evidence.</p>
      </div>
      <button className="button secondary" onClick={() => void refresh()}><RefreshCw size={14}/> Refresh</button>
    </div>

    <ErrorMessage text={error}/>

    <section className="panel queue-toolbar-panel">
      <div className="queue-toolbar">
        <label className="search-box queue-search"><Search size={16}/><input value={query} onChange={event => updateQuery(event.target.value)} placeholder="Search by competitor or domain" /></label>
        <div className="queue-toolbar-meta"><SlidersHorizontal size={15}/><span>{filtered.length} {filtered.length === 1 ? "competitor" : "competitors"}</span></div>
      </div>
      <div className="queue-summary">
        <div><small>Tracked competitors</small><b>{data?.length ?? 0}</b></div>
        <div><small>Total evidence records</small><b>{(data ?? []).reduce((sum, item) => sum + item.evidence.length, 0)}</b></div>
        <div><small>Showing</small><b>{filtered.length ? `${(page - 1) * PAGE_SIZE + 1}–${Math.min(page * PAGE_SIZE, filtered.length)}` : "0"}</b></div>
      </div>
    </section>

    <section className="panel queue-table-panel">
      <div className="panel-heading">
        <div><h3>Competitors</h3><p>Select a row to review its evidence signals.</p></div>
        <span className="queue-count">{filtered.length} records</span>
      </div>
      {visible.length ? <>
        <div className="table-wrap queue-table-wrap">
          <table className="queue-table">
            <thead><tr><th className="expand-col"></th><th>Competitor</th><th>Domain</th><th>Evidence records</th><th>Latest signal</th><th>Availability</th></tr></thead>
            <tbody>
              {visible.map(item => {
                const isOpen = expanded === item.domain;
                const latest = [...item.evidence].sort((a,b) => (b.signal_date || b.created_at || "").localeCompare(a.signal_date || a.created_at || ""))[0];
                return <Fragment key={item.domain}>
                  <tr className={`queue-row ${isOpen ? "selected" : ""}`} onClick={() => setExpanded(isOpen ? null : item.domain)}>
                    <td className="expand-col">{isOpen ? <ChevronDown size={15}/> : <ChevronRight size={15}/>}</td>
                    <td><b>{item.competitor_name}</b></td>
                    <td><span className="domain-text">{item.domain}</span></td>
                    <td><span className="evidence-count">{item.evidence.length}</span></td>
                    <td className="latest-signal">{latest?.signal_type?.replaceAll("_", " ") || "—"}</td>
                    <td><StatusBadge value={item.evidence.length ? "Evidence available" : "No evidence"}/></td>
                  </tr>
                  {isOpen && <tr key={`${item.domain}-details`} className="queue-detail-row"><td colSpan={6}>
                    <div className="queue-detail">
                      <div className="queue-detail-heading"><div><b>Evidence for {item.competitor_name}</b><small>{item.domain} · {item.evidence.length} total records</small></div><span className="queue-detail-hint">Latest 5 shown</span></div>
                      {item.evidence.length ? <div className="signal-list">
                        {[...item.evidence].sort((a,b) => (b.signal_date || b.created_at || "").localeCompare(a.signal_date || a.created_at || "")).slice(0,5).map(record => <article className="signal-list-item" key={record.id}>
                          <div className="signal-list-meta"><span>{record.signal_type?.replaceAll("_", " ") || "Signal"}</span><span>{record.source_type || "Source"}</span><span>{record.signal_date || (record.created_at ? new Date(record.created_at).toLocaleDateString() : "Date unavailable")}</span></div>
                          <p>{record.signal_text}</p>
                          {record.source_url && <a href={record.source_url} target="_blank" rel="noreferrer">Open source ↗</a>}
                        </article>)}
                      </div> : <EmptyState title="Record not found" text="No evidence is linked to this competitor yet."/>}
                    </div>
                  </td></tr>}
                </Fragment>;
              })}
            </tbody>
          </table>
        </div>
        <div className="queue-pagination"><span>Page {page} of {totalPages}</span><div><button className="button secondary" disabled={page <= 1} onClick={() => {setPage(p => Math.max(1,p-1));setExpanded(null);}}>Previous</button><button className="button secondary" disabled={page >= totalPages} onClick={() => {setPage(p => Math.min(totalPages,p+1));setExpanded(null);}}>Next</button></div></div>
      </> : <EmptyState title="Record not found" text={query ? "Try another competitor name or domain." : "Upload a CSV or XLSX source to populate the competitor queue."}/>}
    </section>
  </div>;
}
