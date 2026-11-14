import { getAuditLogs } from "../api/approvals";
import { useApi } from "../hooks/useApi";
import { EmptyState, ErrorMessage, Loading, StatusBadge } from "../components/common/Feedback";

export default function AuditLogs() {
  const {data,loading,error,refresh} = useApi(getAuditLogs);
  if (loading) return <Loading text="Loading audit history..."/>;
  return <section className="panel page-stack"><div className="panel-heading"><div><h3>Audit history</h3><p>Recorded approval and review actions</p></div><button className="button secondary" onClick={()=>void refresh()}>Refresh</button></div>
    <ErrorMessage text={error}/>
    {data?.length ? <div className="table-wrap"><table><thead><tr><th>Action</th><th>Entity</th><th>Previous</th><th>New status</th><th>Actor</th><th>Timestamp</th></tr></thead><tbody>
      {data.map((item,index)=><tr key={String(item.id ?? index)}><td><b>{String(item.action ?? "—")}</b><small>{String(item.comment ?? "")}</small></td><td>{String(item.entity_type ?? "—")} #{String(item.entity_id ?? "—")}</td><td><StatusBadge value={String(item.previous_status ?? "")}/></td><td><StatusBadge value={String(item.new_status ?? "")}/></td><td>{String(item.actor ?? "System")}</td><td>{item.created_at ? new Date(String(item.created_at)).toLocaleString() : "—"}</td></tr>)}
    </tbody></table></div> : <EmptyState title="Record not found" text="Approval actions will appear here."/>}
  </section>;
}
