import { createContext, useContext } from "react";

export interface AnalysisStage {
  status: "started" | "completed" | "skipped";
  message?: string;
}

export type AnalysisStageMap = Record<string, AnalysisStage>;

export interface AnalysisRunContextValue {
  isRunning: boolean;
  setIsRunning: (value: boolean) => void;
  stages: AnalysisStageMap;
  setStageStatus: (stage: string, status: AnalysisStage["status"], message?: string) => void;
  resetStages: () => void;
}

export const AnalysisRunContext = createContext<AnalysisRunContextValue>({
  isRunning: false,
  setIsRunning: () => undefined,
  stages: {},
  setStageStatus: () => undefined,
  resetStages: () => undefined,
});

export function useAnalysisRun() {
  return useContext(AnalysisRunContext);
}
