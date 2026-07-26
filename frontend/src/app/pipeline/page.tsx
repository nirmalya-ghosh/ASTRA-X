"use client";

import { useState, useRef, useEffect } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { UploadCloud, CheckCircle2, Loader2, ArrowRight, AlertTriangle, RotateCcw } from "lucide-react";
import { useRouter } from "next/navigation";
import { getApiUrl } from "@/lib/api";

export default function PipelineWizard() {
  const [files, setFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [pipelineComplete, setPipelineComplete] = useState(false);
  const [pipelineFailed, setPipelineFailed] = useState(false);
  const [datasetId, setDatasetId] = useState<number | null>(null);
  const router = useRouter();
  const logEndRef = useRef<HTMLDivElement>(null);

  const getErrorMessage = (error: unknown) => {
    return error instanceof Error ? error.message : String(error);
  };

  const requestJson = async <T,>(url: string, init?: RequestInit, timeoutMs = 20000): Promise<T> => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await fetch(url, { ...init, signal: controller.signal });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`HTTP ${res.status}: ${errText || res.statusText}`);
      }
      return await res.json();
    } finally {
      window.clearTimeout(timeout);
    }
  };

  const getPipelineLabel = (file: File) => {
    const name = file.name.toLowerCase();
    if (name.endsWith(".csv") || name.endsWith(".json") || name.endsWith(".tsv") ||
        name.endsWith(".xls") || name.endsWith(".xlsx") || name.endsWith(".parquet")) {
      return {
        launch: "Launching multi-model ensemble detection pipeline...",
        task: "Running 5 ML models:",
        models: [
          "IsolationForest (tree-based anomaly isolation)",
          "LocalOutlierFactor (density-based detection)",
          "EllipticEnvelope (Gaussian distribution)",
          "SGDOneClassSVM (support vector boundary)",
          "ZScoreOutlier (statistical sigma-clipping)",
        ],
      };
    }
    if (name.endsWith(".jpg") || name.endsWith(".jpeg") || name.endsWith(".png")) {
      return {
        launch: "Launching computer-vision detection pipeline...",
        task: "Running OpenCV vision detector:",
        models: [
          "Adaptive thresholding",
          "Contour analysis",
          "HOG feature extraction",
        ],
      };
    }
    return {
      launch: "Launching astronomical FITS detection pipeline...",
      task: "Running astronomical source detector:",
      models: [
        "DAOStarFinder source detection",
        "Known-object verification",
        "Tracklet and orbit analysis",
      ],
    };
  };

  // Auto-scroll logs to bottom
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files).filter(f => {
      const name = f.name.toLowerCase();
      return name.endsWith('.fits') || name.endsWith('.fts') || 
             name.endsWith('.jpg') || name.endsWith('.jpeg') || name.endsWith('.png') ||
             name.endsWith('.csv') || name.endsWith('.json') || name.endsWith('.tsv') ||
             name.endsWith('.xls') || name.endsWith('.xlsx') || name.endsWith('.parquet');
    });
    if (droppedFiles.length > 0) {
      setFiles(prev => [...prev, ...droppedFiles]);
    }
  };

  const waitForDatasetReady = async (apiUrl: string, dsId: number) => {
    const maxPolls = 120; // 4 minutes max (120 * 2s)
    let lastStatus = "pending";

    for (let i = 0; i < maxPolls; i++) {
      const dataset = await requestJson<{ status: string; file_count: number }>(`${apiUrl}/datasets/${dsId}`);
      const previousStatus = lastStatus;
      lastStatus = dataset.status;

      if (dataset.status === "ready") {
        setLogs(prev => [...prev, `✅ Dataset #${dsId} indexed (${dataset.file_count} file${dataset.file_count === 1 ? "" : "s"}).`]);
        return;
      }

      if (dataset.status === "empty" || dataset.status === "error") {
        throw new Error(`Dataset indexing ended with status "${dataset.status}"`);
      }

      setProgress(Math.min(35, 20 + Math.round((i / maxPolls) * 15)));
      if (i === 0 || dataset.status !== previousStatus || i % 5 === 0) {
        setLogs(prev => [...prev, `📁 Dataset status: ${dataset.status}. Waiting for indexing...`]);
      }
      await new Promise(r => setTimeout(r, 2000));
    }

    throw new Error(`Dataset indexing timed out (last status: ${lastStatus})`);
  };

  const pollTaskStatus = async (apiUrl: string, taskId: number, dsId: number) => {
    const maxPolls = 600; // 10 minutes max (600 * 1s)
    let pendingPolls = 0;

    for (let i = 0; i < maxPolls; i++) {
      try {
        const task = await requestJson<{
          status: string;
          progress?: number;
          message?: string;
          error_message?: string;
          result_json?: { total_candidates?: number; models_used?: string[] };
        }>(`${apiUrl}/tasks/${taskId}`);
        
        // Update progress
        const taskProgress = Math.round((task.progress || 0) * 100);
        setProgress(Math.max(35, Math.min(95, taskProgress)));

        // Update log with latest message
        if (task.message) {
          setLogs(prev => {
            const last = prev[prev.length - 1];
            // Only add if message is different from last log
            if (last !== `🔬 ${task.message}`) {
              return [...prev, `🔬 ${task.message}`];
            }
            return prev;
          });
        }

        if (task.status === "pending") {
          pendingPolls += 1;
          if (pendingPolls === 5) {
            setLogs(prev => [...prev, "⏳ Detection task is still queued. Waiting for the backend worker..."]);
          }
        } else {
          pendingPolls = 0;
        }

        if (task.status === "completed") {
          const total = task.result_json?.total_candidates || 0;
          const models = task.result_json?.models_used?.join(", ") || "unknown";
          setLogs(prev => [
            ...prev,
            `✅ Detection complete!`,
            `📊 Found ${total} anomalous candidates.`,
            `🧠 Models used: ${models}`,
            `🚀 Redirecting to results...`,
          ]);
          setProgress(100);
          setPipelineComplete(true);
          await new Promise(r => setTimeout(r, 2000));
          router.push(`/datasets/${dsId}`);
          return;
        }

        if (task.status === "failed") {
          setLogs(prev => [
            ...prev,
            `❌ Pipeline failed: ${task.error_message || "Unknown error"}`,
          ]);
          setPipelineFailed(true);
          return;
        }

        // Still running — wait and poll again
        await new Promise(r => setTimeout(r, 2000));
      } catch (err: unknown) {
        setLogs(prev => [...prev, `⚠️ Poll error: ${getErrorMessage(err)}. Retrying...`]);
        await new Promise(r => setTimeout(r, 3000));
      }
    }

    // Timed out
    setLogs(prev => [...prev, "⏱️ Pipeline timed out. Check the dashboard for results."]);
    setPipelineFailed(true);
  };

  const startPipeline = async () => {
    if (files.length === 0) return;
    
    setIsUploading(true);
    setPipelineComplete(false);
    setPipelineFailed(false);
    setLogs(["🚀 Initializing analysis environment..."]);
    setProgress(5);
    
    try {
      const apiUrl = getApiUrl();
      const pipelineLabel = getPipelineLabel(files[0]);
      
      // 1. Upload file
      setLogs(prev => [...prev, `📤 Uploading ${files[0].name} (${(files[0].size / 1024 / 1024).toFixed(1)} MB)...`]);
      setProgress(10);
      
      const formData = new FormData();
      formData.append("file", files[0]);
      
      const uploadRes = await fetch(`${apiUrl}/datasets`, {
        method: "POST",
        body: formData,
      });
      
      if (!uploadRes.ok) {
        const errText = await uploadRes.text();
        throw new Error(`Upload failed (${uploadRes.status}): ${errText}`);
      }
      
      const dataset = await uploadRes.json();
      setDatasetId(dataset.id);
      setLogs(prev => [...prev, `✅ Dataset #${dataset.id} created. Indexing files...`]);
      setProgress(20);

      await waitForDatasetReady(apiUrl, dataset.id);
      
      // 2. Trigger detection pipeline
      setLogs(prev => [...prev, `🧠 ${pipelineLabel.launch}`]);
      setProgress(40);
      
      const detectionRes = await fetch(`${apiUrl}/detection/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_id: dataset.id,
          fwhm: 3.0,
          threshold_sigma: 5.0,
          motion_threshold: 0.5,
          min_persistence: 2,
          enable_motion_detection: true,
          enable_false_positive_filter: true
        }),
      });
      
      if (!detectionRes.ok) {
        const errText = await detectionRes.text();
        throw new Error(`Failed to start detection (${detectionRes.status}): ${errText}`);
      }

      const taskData = await detectionRes.json();
      const taskId = taskData.id;
      
      setLogs(prev => [
        ...prev, 
        `📋 Task #${taskId} created. ${pipelineLabel.task}`,
        ...pipelineLabel.models.map((model, index) => (
          `   ${index === pipelineLabel.models.length - 1 ? "└" : "├"}─ ${model}`
        )),
        `⏳ Polling for results...`,
      ]);

      // 3. Poll task status until complete
      await pollTaskStatus(apiUrl, taskId, dataset.id);
      
    } catch (err: unknown) {
      console.error(err);
      setLogs(prev => [...prev, `❌ ERROR: ${getErrorMessage(err)}`]);
      setPipelineFailed(true);
    }
  };

  const handleReset = () => {
    setIsUploading(false);
    setPipelineComplete(false);
    setPipelineFailed(false);
    setFiles([]);
    setLogs([]);
    setProgress(0);
    setDatasetId(null);
  };

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto py-6 sm:py-12 px-2 sm:px-0">
        <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[#ededed] mb-2">New Analysis</h1>
        <p className="text-[#a1a1aa] mb-8 text-sm">Upload astronomical datasets to run the multi-model asteroid detection pipeline.</p>

        {!isUploading ? (
          <div 
            onDragOver={e => e.preventDefault()}
            onDrop={handleDrop}
            className="border border-dashed border-[#333] hover:border-[#888] transition-colors rounded-lg p-8 sm:p-12 text-center bg-[#0a0a0a]"
          >
            <div className="w-12 h-12 bg-[#111] rounded-full flex items-center justify-center mx-auto mb-4 border border-[#333]">
              <UploadCloud className="w-5 h-5 text-[#ededed]" />
            </div>
            <h3 className="text-[#ededed] font-medium mb-1">Drag and drop datasets here</h3>
            <p className="text-sm text-[#71717a] mb-6">Supports FITS, Images (JPG/PNG), and Tabular Data (CSV/JSON/TSV/XLSX/Parquet)</p>
            
            <label className="cursor-pointer vercel-button-primary px-4 py-2 inline-flex items-center text-sm">
              <span>Select Files</span>
              <input 
                type="file" 
                multiple 
                accept=".fits,.fts,.jpg,.jpeg,.png,.csv,.json,.tsv,.xls,.xlsx,.parquet" 
                className="hidden"
                onChange={(e) => {
                  if (e.target.files) {
                    setFiles(prev => [...prev, ...Array.from(e.target.files!)]);
                  }
                }}
              />
            </label>

            {files.length > 0 && (
              <div className="mt-8 text-left border-t border-[#333] pt-6">
                <h4 className="text-sm font-medium text-[#ededed] mb-3">{files.length} files queued</h4>
                <div className="max-h-32 overflow-y-auto space-y-2 mb-6 pr-2">
                  {files.map((file, i) => (
                    <div key={i} className="flex items-center justify-between text-sm p-2 rounded bg-[#111] border border-[#333]">
                      <span className="text-[#a1a1aa] truncate">{file.name}</span>
                      <span className="text-[#71717a] shrink-0 ml-2">{(file.size / 1024 / 1024).toFixed(1)} MB</span>
                    </div>
                  ))}
                </div>
                <button 
                  onClick={startPipeline}
                  className="w-full flex items-center justify-center gap-2 vercel-button-primary px-4 py-2.5"
                >
                  Start Analysis <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="vercel-card p-4 sm:p-6">
            <div className="flex items-center justify-between mb-4 sm:mb-6">
              <h3 className="font-medium text-[#ededed] flex items-center gap-2 text-sm sm:text-base">
                {pipelineComplete ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : pipelineFailed ? (
                  <AlertTriangle className="w-4 h-4 text-red-400" />
                ) : (
                  <Loader2 className="w-4 h-4 animate-spin" />
                )}
                {pipelineComplete ? "Pipeline Complete" : pipelineFailed ? "Pipeline Failed" : "Running Pipeline"}
              </h3>
              <span className="text-sm text-[#a1a1aa]">{Math.round(progress)}%</span>
            </div>

            <div className="w-full bg-[#111] h-1.5 rounded-full overflow-hidden mb-6 sm:mb-8">
              <div 
                className={`h-full transition-all duration-700 ${
                  pipelineFailed ? "bg-red-500" : pipelineComplete ? "bg-emerald-400" : "bg-[#ededed]"
                }`}
                style={{ width: `${progress}%` }}
              />
            </div>

            <div className="bg-[#000] border border-[#333] rounded-md p-3 sm:p-4 font-mono text-[11px] sm:text-xs text-[#a1a1aa] space-y-1.5 h-64 sm:h-80 overflow-y-auto">
              {logs.map((log, i) => (
                <div key={i} className="flex gap-2 sm:gap-4">
                  <span className="text-[#71717a] w-8 sm:w-12 shrink-0 text-right">{String(i + 1).padStart(2, '0')}</span>
                  <span className={`break-all ${
                    log.includes("ERROR") || log.includes("❌") ? "text-red-400" : 
                    log.includes("✅") ? "text-emerald-400" :
                    log.includes("📊") || log.includes("🧠") ? "text-blue-400" :
                    i === logs.length - 1 ? "text-[#ededed]" : ""
                  }`}>{log}</span>
                </div>
              ))}
              <div ref={logEndRef} />
            </div>

            {/* Action buttons */}
            {(pipelineFailed || pipelineComplete) && (
              <div className="flex gap-3 mt-4">
                <button onClick={handleReset} className="flex-1 flex items-center justify-center gap-2 vercel-button-secondary px-4 py-2 text-sm">
                  <RotateCcw className="w-4 h-4" /> Try Again
                </button>
                {datasetId && (
                  <button onClick={() => router.push(`/datasets/${datasetId}`)} className="flex-1 flex items-center justify-center gap-2 vercel-button-primary px-4 py-2 text-sm">
                    View Results <ArrowRight className="w-4 h-4" />
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
