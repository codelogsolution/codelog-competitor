import { Link, useParams } from "react-router-dom";
import { getBattlecard, getBattlecards, type BattlecardContent } from "../api/battlecards";
import { useApi } from "../hooks/useApi";
import { EmptyState, ErrorMessage, Loading, StatusBadge } from "../components/common/Feedback";

function BattlecardDetail({id}:{id:string}) {
  const {data,loading,error} = useApi(() => getBattlecard(id),[id]);
  if (loading) return <Loading text="Loading battlecard..."/>;
  if (error || !data) return <ErrorMessage text={error || "Battlecard not found"}/>;
  let content: BattlecardContent;
  try { content = typeof data.content === "string" ? JSON.parse(data.content) as BattlecardContent : data.content; }
  catch { content = {} as BattlecardContent; }
  const sections: Array<[string,string|string[]|undefined]> = [
    ["Overview",content.overview],["Positioning",content.positioning],["Strengths",content.strengths],
    ["Weaknesses",content.weaknesses],["Product gaps",content.product_gaps],["Pricing",content.pricing],
    ["Opportunities",content.opportunities],["Recommended actions",content.recommended_actions],["Evidence notes",content.evidence_notes],
  ];
  return <div className="page-stack"><Link className="text-link" to="/battlecards">← Back to battlecards</Link>
    <section className="panel"><StatusBadge value={data.status}/><h2>{data.competitor_name}</h2><p className="muted">{data.domain}</p><p>Threat level: <StatusBadge value={content.threat_level}/></p></section>
    <div className="card-grid">{sections.map(([title,value])=><article className="panel" key={title}><h3>{title}</h3>
      {Array.isArray(value) ? value.length ? <ul>{value.map((item,index)=><li key={index}>{item}</li>)}</ul> : <p className="muted">Not available in supplied evidence</p> : <p>{value || "Not available in supplied evidence"}</p>}
    </article>)}</div>
  </div>;
}

export default function BattlecardStudio() {
  const {id} = useParams();
  const {data,loading,error} = useApi(getBattlecards);
  if (id) return <BattlecardDetail id={id}/>;
  if (loading) return <Loading text="Loading battlecards..."/>;
  return <div className="page-stack"><ErrorMessage text={error}/>
    {data?.length ? <div className="card-grid m-2">{data.map(card=><Link className="mini-card panel" to={`/battlecards/${card.id}`} key={card.id}><StatusBadge value={card.status}/><b>{card.competitor_name}</b><small>{card.domain}</small><span className="text-link">Open battlecard →</span></Link>)}</div> : <EmptyState title="Record not found" text="Run competitor analysis to generate a draft."/>}
  </div>;
}
