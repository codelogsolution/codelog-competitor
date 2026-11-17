import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";

export default function Validation() {
  return <section className="panel"><h2>Validation</h2><p className="muted">File validation results appear after uploading a CSV or XLSX file.</p><div className="button-row" style={{ marginTop: 16 }}><Link className="button secondary" to="/import">Back to Import <ArrowRight size={14}/></Link><Link className="button primary" to="/evidence">Next: View Evidence <ArrowRight size={14}/></Link><Link className="button primary" to="/battlecards">Next: Generate Battlecards <ArrowRight size={14}/></Link></div></section>;
}
