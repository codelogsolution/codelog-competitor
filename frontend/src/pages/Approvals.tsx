import { useState } from "react";
import { Check, MessageSquare, X } from "lucide-react";
import { getApprovals, submitApprovalAction } from "../api/approvals";
import { useApi } from "../hooks/useApi";
import { EmptyState, ErrorMessage, Loading, StatusBadge } from "../components/common/Feedback";

export default function Approvals() {
  const {data,loading,error,refresh} = useApi(getApprovals);
  const [comments,setComments] = useState<Record<number,string>>({});
  const [busy,setBusy] = useState<number|null>(null);
  const [message,setMessage] = useState("");
  if (loading) return <Loading text="Loading approval queue..."/>;

  async function act(id:number,action:"approve"|"reject"|"request-changes"|"resubmit") {
    setBusy(id); setMessage("");
    try { await submitApprovalAction(id,action,comments[id] ?? ""); setMessage("Approval action submitted."); await refresh(); }
    catch (err) { setMessage(err instanceof Error ? err.message : "Approval action failed"); }
    finally { setBusy(null); }
  }

  return <div className="page-stack"><ErrorMessage text={error}/>{message && <div className="alert">{message}</div>}
    {data?.length ? data.map((item,index)=>{const id=Number(item.id ?? index);return <article className="panel" key={id}>
      <div className="panel-heading"><div><h3>{item.competitor_name ?? `Battlecard #${id}`}</h3><p>{item.domain ?? "Competitor review"}</p></div><StatusBadge value={item.status}/></div>
      <label className="field-label">Review comment</label><textarea value={comments[id] ?? ""} onChange={event=>setComments(old=>({...old,[id]:event.target.value}))} placeholder="Optional review comment..."/>
      <div className="button-row">
        <button className="button primary" disabled={busy===id} onClick={()=>void act(id,"approve")}><Check size={14}/> Approve</button>
        <button className="button danger" disabled={busy===id} onClick={()=>void act(id,"reject")}><X size={14}/> Reject</button>
        <button className="button secondary" disabled={busy===id} onClick={()=>void act(id,"request-changes")}><MessageSquare size={14}/> Request changes</button>
        {item.status==="changes_requested" && <button className="button secondary" disabled={busy===id} onClick={()=>void act(id,"resubmit")}>Resubmit</button>}
      </div>
    </article>;}) : <EmptyState title="Record not found" text="Battlecards awaiting human review will appear here."/>}
  </div>;
}
