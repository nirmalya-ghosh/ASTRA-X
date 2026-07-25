"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { UploadCloud, CheckCircle2, Loader2, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";

export default function PipelineWizard() {
  const [files, setFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const router = useRouter();

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files).filter(f => {
      const name = f.name.toLowerCase();
      return name.endsWith('.fits') || name.endsWith('.fts') || 
             name.endsWith('.jpg') || name.endsWith('.jpeg') || name.endsWith('.png') ||
             name.endsWith('.csv') || name.endsWith('.json');
    });
    if (droppedFiles.length > 0) {
      setFiles(prev => [...prev, ...droppedFiles]);
    }
  };

  const startPipeline = async () => {
    if (files.length === 0) return;
    
    setIsUploading(true);
    setLogs(["Initializing analysis environment..."]);
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      
      // 1. Upload file to create dataset
      setLogs(prev => [...prev, `Uploading ${files[0].name}...`]);
      setProgress(20);
      
      const formData = new FormData();
      formData.append("file", files[0]); // Just process the first file for now
      
      const uploadRes = await fetch(`${apiUrl}/datasets`, {
        method: "POST",
        body: formData,
      });
      
      if (!uploadRes.ok) throw new Error("Failed to upload dataset");
      
      const dataset = await uploadRes.json();
      setLogs(prev => [...prev, `Dataset #${dataset.id} created successfully.`]);
      setProgress(50);
      
      // 2. Trigger detection pipeline
      setLogs(prev => [...prev, "Launching ML detection pipeline..."]);
      setProgress(70);
      
      const detectionRes = await fetch(`${apiUrl}/detection/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
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
      
      if (!detectionRes.ok) throw new Error("Failed to start detection pipeline");
      
      setLogs(prev => [...prev, "Pipeline launched! Redirecting to dashboard..."]);
      setProgress(100);
      
      await new Promise(r => setTimeout(r, 1000));
      router.push(`/datasets/${dataset.id}`);
      
    } catch (err: any) {
      console.error(err);
      setLogs(prev => [...prev, `❌ ERROR: ${err.toString()}`, "Pipeline failed. Please refresh the page to try again."]);
      // Do not set isUploading(false) here, otherwise the log window instantly disappears
      // and the user is thrown back to the upload form without seeing the error!
    }
  };

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto py-12">
        <h1 className="text-2xl font-semibold tracking-tight text-[#ededed] mb-2">New Analysis</h1>
        <p className="text-[#a1a1aa] mb-8">Upload astronomical datasets to run the asteroid detection pipeline.</p>

        {!isUploading ? (
          <div 
            onDragOver={e => e.preventDefault()}
            onDrop={handleDrop}
            className="border border-dashed border-[#333] hover:border-[#888] transition-colors rounded-lg p-12 text-center bg-[#0a0a0a]"
          >
            <div className="w-12 h-12 bg-[#111] rounded-full flex items-center justify-center mx-auto mb-4 border border-[#333]">
              <UploadCloud className="w-5 h-5 text-[#ededed]" />
            </div>
            <h3 className="text-[#ededed] font-medium mb-1">Drag and drop datasets here</h3>
            <p className="text-sm text-[#71717a] mb-6">Supports FITS, Images (JPG/PNG), CSV, and JSON data</p>
            
            <label className="cursor-pointer vercel-button-primary px-4 py-2 inline-flex items-center text-sm">
              <span>Select Files</span>
              <input 
                type="file" 
                multiple 
                accept=".fits,.fts,.jpg,.jpeg,.png,.csv,.json" 
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
                      <span className="text-[#71717a]">{(file.size / 1024 / 1024).toFixed(1)} MB</span>
                    </div>
                  ))}
                </div>
                <button 
                  onClick={startPipeline}
                  className="w-full flex items-center justify-center gap-2 vercel-button-primary px-4 py-2"
                >
                  Start Analysis <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="vercel-card p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-medium text-[#ededed] flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Running Pipeline
              </h3>
              <span className="text-sm text-[#a1a1aa]">{Math.round(progress)}%</span>
            </div>

            <div className="w-full bg-[#111] h-1.5 rounded-full overflow-hidden mb-8">
              <div 
                className="h-full bg-[#ededed] transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>

            <div className="bg-[#000] border border-[#333] rounded-md p-4 font-mono text-xs text-[#a1a1aa] space-y-2 h-64 overflow-y-auto">
              {logs.map((log, i) => (
                <div key={i} className="flex gap-4">
                  <span className="text-[#71717a] w-12 shrink-0">{String(i + 1).padStart(2, '0')}</span>
                  <span className={i === logs.length - 1 ? "text-[#ededed]" : ""}>{log}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
