import { lazy, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import { AnalysisRunContext, type AnalysisStageMap } from "./contexts/AnalysisRunContext";

const Workspace = lazy(() => import("./pages/Workspace"));
const ImportSources = lazy(() => import("./pages/ImportSources"));
const CompetitorQueue = lazy(() => import("./pages/CompetitorQueue"));
const EvidenceHub = lazy(() => import("./pages/EvidenceHub"));
const BattlecardStudio = lazy(() => import("./pages/BattlecardStudio"));
const Approvals = lazy(() => import("./pages/Approvals"));
const AuditLogs = lazy(() => import("./pages/AuditLogs"));
const Workflow = lazy(() => import("./pages/Workflow"));

export default function App() {
  const [isRunning, setIsRunning] = useState(false);
  const [stages, setStages] = useState<AnalysisStageMap>({});
  const resetStages = () => setStages({});
  const setStageStatus = (stage: string, status: "started" | "completed" | "skipped", message?: string) => {
    setStages(current => ({ ...current, [stage]: { status, message } }));
  };

  return (
    <AnalysisRunContext.Provider value={{ isRunning, setIsRunning, stages, setStageStatus, resetStages }}>
      <Routes>
        <Route element={<AppLayout/>}>
          <Route index element={<Workspace/>}/>
          <Route path="/workflow" element={<Workflow/>}/>
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
      </Routes>
    </AnalysisRunContext.Provider>
  );
}
