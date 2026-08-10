"use client";

import { useCallback, useState, useEffect, use } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Users, Activity, Telescope, ScanEye, Download, Loader2, RefreshCw, AlertTriangle, Brain, Shield, Orbit } from "lucide-react";
import Link from "next/link";
import { getApiUrl } from "@/lib/api";

interface Candidate {
  id: number;
  confidence_score: number;
  ra: number | null;
  dec: number | null;
  flux: number | null;
  motion_speed: number | null;
  classification: string;
  notes?: string;
  detection_method?: string;
  snr?: number | null;
  x_centroid?: number;
  y_centroid?: number;
  object_type?: string;
  metadata_json?: {
    orbit?: {
      estimated_elements?: {
        a?: string | number;
        e?: string | number;
        i?: string | number;
      };
    };
  } & Record<string, unknown>;
}

interface TaskStatus {
  id: number;
  status: string;
  progress: number;
  message: string;
  result_json?: Record<string, unknown>;
}

export default function DatasetResultsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const datasetId = resolvedParams.id;
  const [activeTab, setActiveTab] = useState("candidates");
  const [datasetName, setDatasetName] = useState(`Dataset #${datasetId}`);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [taskRunning, setTaskRunning] = useState(false);
  const [taskProgress, setTaskProgress] = useState(0);
  const [taskMessage, setTaskMessage] = useState("");

  const apiUrl = getApiUrl();

  const fetchCandidates = useCallback(async () => {
    try {
      const candRes = await fetch(`${apiUrl}/candidates?dataset_id=${datasetId}&limit=100&sort_by=confidence_score&sort_desc=true`);
      if (candRes.ok) {
        const candData = await candRes.json();
        setCandidates(candData.candidates || []);
      }
    } catch (err) {
      console.error("Failed to fetch candidates", err);
    }
  }, [apiUrl, datasetId]);

  const pollTask = useCallback(async (taskId: number) => {
    for (let i = 0; i < 600; i++) {
      try {
        const res = await fetch(`${apiUrl}/tasks/${taskId}`);
        if (!res.ok) break;
        const task = await res.json();
        setTaskProgress(Math.round((task.progress || 0) * 100));
        setTaskMessage(task.message || "Processing...");
        if (task.status === "completed" || task.status === "failed") {
          setTaskRunning(false);
          await fetchCandidates();
          break;
        }
      } catch { break; }
      await new Promise(r => setTimeout(r, 2000));
    }
    setTaskRunning(false);
  }, [apiUrl, fetchCandidates]);

  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch dataset name
        const dsRes = await fetch(`${apiUrl}/datasets/${datasetId}`);
        if (dsRes.ok) {
          const dsData = await dsRes.json();
          if (dsData.name) setDatasetName(dsData.name);
        }

        // Check if any tasks are still running for this dataset
        try {
          const tasksRes = await fetch(`${apiUrl}/tasks?dataset_id=${datasetId}&status=running`);
          if (tasksRes.ok) {
            const tasksData = await tasksRes.json();
            const tasks = tasksData.tasks || tasksData || [];
            const runningTask = Array.isArray(tasks) ? tasks.find((t: TaskStatus) => t.status === "running" || t.status === "pending") : null;
            if (runningTask) {
              setTaskRunning(true);
              setTaskProgress(Math.round((runningTask.progress || 0) * 100));
              setTaskMessage(runningTask.message || "Processing...");
              // Poll until complete
              pollTask(runningTask.id);
            }
          }
        } catch {
          // Tasks endpoint might not support filtering — that's fine
        }

        // Fetch candidates
        await fetchCandidates();
      } catch (err) {
        console.error("Failed to fetch data", err);
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, [apiUrl, datasetId, fetchCandidates, pollTask]);

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return "text-emerald-400";
    if (score >= 0.6) return "text-blue-400";
    if (score >= 0.4) return "text-amber-400";
    return "text-[#71717a]";
  };

  const getConfidenceBar = (score: number) => {
    if (score >= 0.8) return "bg-emerald-400";
    if (score >= 0.6) return "bg-blue-400";
    if (score >= 0.4) return "bg-amber-400";
    return "bg-[#333]";
  };

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6 px-2 sm:px-0">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 sm:mb-8 gap-3">
          <div>
            <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[#ededed]">{datasetName}</h1>
            <p className="text-[#a1a1aa] mt-1 text-sm">Dataset #{datasetId} • {candidates.length} Candidates found</p>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={async () => { setIsLoading(true); await fetchCandidates(); setIsLoading(false); }}
              className="flex items-center gap-2 vercel-button-secondary px-3 py-2 text-sm"
            >
              <RefreshCw className="w-4 h-4" /> Refresh
            </button>
            <button className="flex items-center gap-2 vercel-button-secondary px-3 py-2 text-sm">
              <Download className="w-4 h-4" />
              <span className="hidden sm:inline">Export Data</span>
            </button>
          </div>
        </div>

        {/* Task Running Banner */}
        {taskRunning && (
          <div className="vercel-card p-4 border-blue-900/50 bg-blue-950/20">
            <div className="flex items-center gap-3 mb-3">
              <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
              <span className="text-sm text-blue-400 font-medium">Detection pipeline is running...</span>
              <span className="text-xs text-[#71717a] ml-auto">{taskProgress}%</span>
            </div>
            <div className="w-full bg-[#111] h-1 rounded-full overflow-hidden mb-2">
              <div className="h-full bg-blue-400 transition-all duration-500" style={{ width: `${taskProgress}%` }} />
            </div>
            <p className="text-xs text-[#a1a1aa]">{taskMessage}</p>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex gap-4 sm:gap-6 border-b border-[#333] mb-4 sm:mb-8 overflow-x-auto">
          <button 
            onClick={() => setActiveTab("candidates")}
            className={`pb-3 border-b-2 text-sm font-medium transition-colors whitespace-nowrap ${activeTab === "candidates" ? "border-[#ededed] text-[#ededed]" : "border-transparent text-[#a1a1aa] hover:text-[#ededed]"}`}
          >
            Detected Candidates
          </button>
          <button 
            onClick={() => setActiveTab("advanced")}
            className={`pb-3 border-b-2 text-sm font-medium transition-colors whitespace-nowrap ${activeTab === "advanced" ? "border-[#ededed] text-[#ededed]" : "border-transparent text-[#a1a1aa] hover:text-[#ededed]"}`}
          >
            Advanced Tools
          </button>
        </div>

        {/* Main Content Area */}
        {activeTab === "candidates" && (
          <div className="space-y-4">
            {/* Summary Stats */}
            {candidates.length > 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                <div className="vercel-card p-3 sm:p-4 text-center">
                  <p className="text-lg sm:text-2xl font-semibold text-[#ededed]">{candidates.length}</p>
                  <p className="text-xs text-[#71717a]">Total Detected</p>
                </div>
                <div className="vercel-card p-3 sm:p-4 text-center">
                  <p className="text-lg sm:text-2xl font-semibold text-emerald-400">
                    {candidates.filter(c => c.confidence_score >= 0.8).length}
                  </p>
                  <p className="text-xs text-[#71717a]">High Confidence</p>
                </div>
                <div className="vercel-card p-3 sm:p-4 text-center">
                  <p className="text-lg sm:text-2xl font-semibold text-blue-400">
                    {candidates.filter(c => c.confidence_score >= 0.4 && c.confidence_score < 0.8).length}
                  </p>
                  <p className="text-xs text-[#71717a]">Medium Confidence</p>
                </div>
                <div className="vercel-card p-3 sm:p-4 text-center">
                  <p className="text-lg sm:text-2xl font-semibold text-[#a1a1aa]">
                    {candidates.filter(c => c.confidence_score < 0.4).length}
                  </p>
                  <p className="text-xs text-[#71717a]">Low Confidence</p>
                </div>
              </div>
            )}
            
            {isLoading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-[#71717a]" />
              </div>
            ) : candidates.length === 0 ? (
              <div className="text-center py-12 border border-dashed border-[#333] rounded-lg bg-[#0a0a0a]">
                {taskRunning ? (
                  <>
                    <Loader2 className="w-8 h-8 text-blue-400 mx-auto mb-3 animate-spin" />
                    <p className="text-[#a1a1aa] text-sm">Detection pipeline is still running. Results will appear here automatically.</p>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-8 h-8 text-[#333] mx-auto mb-3" />
                    <p className="text-[#a1a1aa] text-sm">No candidates detected yet.</p>
                    <button 
                      onClick={async () => { setIsLoading(true); await fetchCandidates(); setIsLoading(false); }}
                      className="mt-3 text-sm text-[#ededed] hover:underline"
                    >
                      Refresh Results
                    </button>
                  </>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {candidates.map((candidate) => (
                  <div key={candidate.id} className="vercel-card p-3 sm:p-4 hover:border-[#555] transition-colors">
                    <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                      {/* Confidence indicator */}
                      <div className="flex sm:flex-col items-center gap-2 sm:gap-1 sm:w-16 shrink-0">
                        <div className={`w-10 h-10 sm:w-14 sm:h-14 rounded-lg border border-[#333] flex items-center justify-center bg-[#111]`}>
                          <span className={`text-sm sm:text-lg font-bold ${getConfidenceColor(candidate.confidence_score)}`}>
                            {Math.round(candidate.confidence_score * 100)}
                          </span>
                        </div>
                        <span className="text-[10px] text-[#71717a] uppercase">score</span>
                      </div>

                      {/* Details */}
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <h3 className="font-medium text-[#ededed] text-sm">Candidate AST-{candidate.id}</h3>
                            {candidate.object_type === 'asteroid' && (
                              <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full font-medium shrink-0 bg-blue-950 text-blue-400 border border-blue-900 flex items-center gap-1">
                                <Shield className="w-3 h-3" />
                                Known Object
                              </span>
                            )}
                          </div>
                          <span className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full font-medium shrink-0 w-fit ${
                            candidate.classification === 'confirmed' ? 'bg-emerald-950 text-emerald-400 border border-emerald-900' : 
                            candidate.classification === 'rejected' ? 'bg-red-950 text-red-400 border border-red-900' : 
                            'bg-[#111] text-[#71717a] border border-[#333]'
                          }`}>
                            {candidate.classification}
                          </span>
                        </div>

                        {/* Confidence bar */}
                        <div className="flex items-center gap-2 mt-2">
                          <div className="flex-1 bg-[#111] h-1.5 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${getConfidenceBar(candidate.confidence_score)}`} 
                              style={{ width: `${candidate.confidence_score * 100}%` }} />
                          </div>
                          <span className={`text-xs font-medium ${getConfidenceColor(candidate.confidence_score)}`}>
                            {(candidate.confidence_score * 100).toFixed(0)}%
                          </span>
                        </div>

                        {/* Metadata grid */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-4 gap-y-1 mt-2 text-xs text-[#71717a]">
                          {candidate.flux && <p>Flux: {candidate.flux.toFixed(2)}</p>}
                          {candidate.snr && <p>SNR: {typeof candidate.snr === 'number' ? candidate.snr.toFixed(1) : candidate.snr}</p>}
                          {candidate.ra ? <p>RA: {candidate.ra.toFixed(4)}</p> : null}
                          {candidate.dec ? <p>DEC: {candidate.dec.toFixed(4)}</p> : null}
                          {candidate.motion_speed && <p>Speed: {candidate.motion_speed.toFixed(2)} px/hr</p>}
                        </div>

                        {/* Detection method badge */}
                        {candidate.detection_method && (
                          <div className="flex items-center gap-1.5 mt-2">
                            <Brain className="w-3 h-3 text-[#71717a]" />
                            <span className="text-[10px] text-[#71717a] font-mono truncate">{candidate.detection_method}</span>
                          </div>
                        )}
                        
                        {/* Notes */}
                        {candidate.notes && (
                          <div className="mt-2 p-2 bg-[#111] rounded text-xs text-[#a1a1aa] border border-[#222] break-words whitespace-pre-line">
                            {candidate.notes}
                          </div>
                        )}

                        {/* Orbit */}
                        {candidate.metadata_json?.orbit && (
                          <div className="mt-2 p-2 bg-blue-950/20 rounded text-xs text-blue-200 border border-blue-900/50 break-words flex gap-2">
                            <Orbit className="w-4 h-4 shrink-0 mt-0.5 text-blue-400" />
                            <div className="w-full">
                              <span className="font-semibold text-blue-300">Estimated Orbit (Gauss method short-arc)</span>
                              <div className="grid grid-cols-3 mt-1 gap-2 font-mono text-[10px]">
                                <div><span className="text-blue-400/50">a:</span> {candidate.metadata_json.orbit.estimated_elements?.a || 'N/A'} AU</div>
                                <div><span className="text-blue-400/50">e:</span> {candidate.metadata_json.orbit.estimated_elements?.e || 'N/A'}</div>
                                <div><span className="text-blue-400/50">i:</span> {candidate.metadata_json.orbit.estimated_elements?.i || 'N/A'}°</div>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Action buttons */}
                        <div className="mt-3 flex items-center gap-2">
                          <button 
                            onClick={async (e) => {
                              e.preventDefault();
                              try {
                                const res = await fetch(`${apiUrl}/candidates/${candidate.id}/classify-ai`, { method: 'POST' });
                                if (res.ok) {
                                  const updated = await res.json();
                                  setCandidates(prev => prev.map(c => c.id === updated.id ? updated : c));
                                }
                              } catch (err) {
                                console.error(err);
                              }
                            }}
                            className="text-xs bg-[#111] hover:bg-[#222] border border-[#333] text-[#ededed] px-2 py-1 rounded transition-colors"
                          >
                            Run AI Analysis
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Advanced Tools Sub-menu */}
        {activeTab === "advanced" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Link href="/blink" className="vercel-card p-6 flex flex-col items-center justify-center text-center group cursor-pointer hover:bg-[#111]">
              <ScanEye className="w-8 h-8 text-[#71717a] mb-4 group-hover:text-[#ededed] transition-colors" />
              <h3 className="font-medium text-[#ededed] text-sm">Blink Comparator</h3>
              <p className="text-xs text-[#a1a1aa] mt-1">Visually inspect moving objects across frames</p>
            </Link>
            <Link href="/inspector" className="vercel-card p-6 flex flex-col items-center justify-center text-center group cursor-pointer hover:bg-[#111]">
              <Telescope className="w-8 h-8 text-[#71717a] mb-4 group-hover:text-[#ededed] transition-colors" />
              <h3 className="font-medium text-[#ededed] text-sm">Deep Inspector</h3>
              <p className="text-xs text-[#a1a1aa] mt-1">FITS header analysis and pixel-level math</p>
            </Link>
            <Link href="/heatmaps" className="vercel-card p-6 flex flex-col items-center justify-center text-center group cursor-pointer hover:bg-[#111]">
              <Activity className="w-8 h-8 text-[#71717a] mb-4 group-hover:text-[#ededed] transition-colors" />
              <h3 className="font-medium text-[#ededed] text-sm">Heatmaps</h3>
              <p className="text-xs text-[#a1a1aa] mt-1">Intensity mapping of detected sources</p>
            </Link>
            <Link href="/processing" className="vercel-card p-6 flex flex-col items-center justify-center text-center group cursor-pointer hover:bg-[#111]">
              <Users className="w-8 h-8 text-[#71717a] mb-4 group-hover:text-[#ededed] transition-colors" />
              <h3 className="font-medium text-[#ededed] text-sm">Raw Processing</h3>
              <p className="text-xs text-[#a1a1aa] mt-1">Manual dark/flat field calibration</p>
            </Link>
          </div>
        )}
      </div>
    </AppShell>
  );
}
