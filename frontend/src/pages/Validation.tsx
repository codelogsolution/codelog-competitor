import { Link } from "react-router-dom";
export default function Validation() {
  return <section className="panel"><h2>Validation</h2><p className="muted">File validation results appear after uploading a CSV or XLSX file.</p><Link className="text-link" to="/import">Go to Import sources →</Link></section>;
}
