import { useMemo, useState } from "react";
import { ExternalLink, RefreshCw, Search } from "lucide-react";
import { getEvidence } from "../api/evidence";
import { useApi } from "../hooks/useApi";
import { EmptyState, ErrorMessage, Loading, StatusBadge } from "../components/common/Feedback";

export default function EvidenceHub() {
  const {data,loading,error,refresh} = useApi(getEvidence);
  const [query,setQuery] = useState("");
  const rows = useMemo(() => (data ?? []).filter(item => `${item.competitor_name} ${item.domain} ${item.signal_text} ${item.source_type}`.toLowerCase().includes(query.toLowerCase())),[data,query]);
  if (loading) return <Loading text="Loading evidence..."/>;
  return <div className="page-stack"><ErrorMessage text={error}/>
    <div className="toolbar"><div className="search-box"><Search size={16}/><input value={query} onChange={event=>setQuery(event.target.value)} placeholder="Search evidence"/></div><button className="button secondary" onClick={()=>void refresh()}><RefreshCw size={14}/> Refresh</button></div>
    <section className="panel"><div className="panel-heading"><div><h3>Evidence records</h3><p>{rows.length} records</p></div></div>
      {rows.length ? <div className="table-wrap"><table><thead><tr><th>Competitor</th><th>Signal</th><th>Type</th><th>Sentiment</th><th>Frequency</th><th>Source</th></tr></thead><tbody>
        {rows.map(item=><tr key={item.id}><td><b>{item.competitor_name}</b><small>{item.domain}</small></td><td>{item.signal_text}</td><td>{item.signal_type}</td><td><StatusBadge value={item.sentiment}/></td><td>{item.frequency ?? "—"}</td><td><a className="text-link" href={item.source_url} target="_blank" rel="noreferrer">Open <ExternalLink size={12}/></a></td></tr>)}
      </tbody></table></div> : <EmptyState title="Record not found" text="Try another search or upload competitor data."/>}
    </section>
  </div>;
}
