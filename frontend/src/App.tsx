import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import Workspace from "./pages/Workspace";
import ImportSources from "./pages/ImportSources";
import CompetitorQueue from "./pages/CompetitorQueue";
import EvidenceHub from "./pages/EvidenceHub";
import BattlecardStudio from "./pages/BattlecardStudio";
import Approvals from "./pages/Approvals";
import AuditLogs from "./pages/AuditLogs";

export default function App() {
  return <Routes>
    <Route element={<AppLayout/>}>
      <Route index element={<Workspace/>}/>
      <Route path="/import" element={<ImportSources/>}/>
      <Route path="/competitors" element={<CompetitorQueue/>}/>
      <Route path="/evidence" element={<EvidenceHub/>}/>
      <Route path="/battlecards" element={<BattlecardStudio/>}/>
      <Route path="/battlecards/:id" element={<BattlecardStudio/>}/>
      <Route path="/approvals" element={<Approvals/>}/>
      <Route path="/audit" element={<AuditLogs/>}/>
      <Route path="/validation" element={<Navigate to="/import" replace/>}/>
      <Route path="*" element={<Navigate to="/" replace/>}/>
    </Route>
  </Routes>;
}
