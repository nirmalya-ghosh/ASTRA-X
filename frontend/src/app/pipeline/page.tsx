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
    const droppedFiles = Array.from(e.dataTransfer.files).filter(f => 
      f.name.toLowerCase().endsWith('.fits') || f.name.toLowerCase().endsWith('.fts')
    );
    if (droppedFiles.length > 0) {
      setFiles(prev => [...prev, ...droppedFiles]);
    }
  };

  const startPipeline = async () => {
    if (files.length === 0) return;
    
    setIsUploading(true);
    setLogs(["Initializing analysis environment...", "Allocating cloud resources..."]);
    
    // Simulate Vercel-like build logs
    const stages = [
      "Uploading FITS datasets...",
      "Calibrating images (Dark/Flat fielding)...",
      "Running Source Extractor (SEP)...",
      "Aligning astronomical frames...",
      "Executing transient detection algorithms...",
      "Ranking candidates using AI model...",
      "Finalizing results..."
    ];

    for (let i = 0; i < stages.length; i++) {
      await new Promise(r => setTimeout(r, 1200));
      setLogs(prev => [...prev, stages[i]]);
      setProgress(((i + 1) / stages.length) * 100);
    }

    await new Promise(r => setTimeout(r, 1000));
    router.push("/datasets/demo-dataset");
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
            <p className="text-sm text-[#71717a] mb-6">Supports .fits and .fts file formats</p>
            
            <label className="cursor-pointer vercel-button-primary px-4 py-2 inline-flex items-center text-sm">
              <span>Select Files</span>
              <input 
                type="file" 
                multiple 
                accept=".fits,.fts" 
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
