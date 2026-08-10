"use client";
import { AppShell } from "@/components/layout/AppShell";
import { motion } from "framer-motion";
import { ScanEye, Play, Pause, SkipForward, SkipBack } from "lucide-react";
import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { WebGLFitsViewer } from "@/components/visualization/WebGLFitsViewer";

export default function BlinkPage() {
  const [datasetId] = useState<number | undefined>();
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(500);

  const { data, isLoading } = useQuery({
    queryKey: ["dataset_frames", datasetId],
    queryFn: () => datasetId ? api.datasets.frames(datasetId) : Promise.resolve([]),
    enabled: !!datasetId,
  });

  const frames = data || [];

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying && frames.length > 0) {
      interval = setInterval(() => {
        setCurrentFrameIndex((prev) => (prev + 1) % frames.length);
      }, speed);
    }
    return () => clearInterval(interval);
  }, [isPlaying, frames.length, speed]);

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-space-100">Blink Comparator</h1>
          <p className="text-sm text-space-500 mt-1">Rapidly alternate between frames to spot moving objects</p>
        </div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-prominent rounded-xl overflow-hidden">
          {/* Viewer Area */}
          <div className="aspect-[16/10] bg-space-950 flex items-center justify-center relative overflow-hidden">
            {isLoading ? (
              <p className="text-neon-400 animate-pulse">Loading frames...</p>
            ) : frames.length > 0 ? (
              <WebGLFitsViewer 
                imageUrl={`/api/v1/datasets/${datasetId}/frames/${frames[currentFrameIndex].id}/preview`} 
                alt="Frame preview" 
                className="w-full h-full"
              />
            ) : (
              <div className="text-center z-10">
                <ScanEye className="w-16 h-16 text-space-800 mx-auto mb-4" />
                <p className="text-sm text-space-500">No frames available to blink</p>
                <p className="text-xs text-space-600 mt-1">Please select a processed dataset</p>
              </div>
            )}

            {/* Grid overlay */}
            <div className="absolute inset-0 grid-bg pointer-events-none opacity-30" />
            
            {/* Frame Counter */}
            {frames.length > 0 && (
              <div className="absolute top-4 right-4 px-3 py-1 bg-space-900/80 rounded-lg text-xs font-mono text-space-200 backdrop-blur">
                Frame {currentFrameIndex + 1} / {frames.length}
              </div>
            )}
          </div>

          {/* Controls */}
          <div className="p-4 border-t border-neon-500/10 flex items-center justify-center gap-3">
            <button 
              onClick={() => setCurrentFrameIndex(prev => prev > 0 ? prev - 1 : frames.length - 1)}
              className="p-2 rounded-lg hover:bg-space-800/50 text-space-500 hover:text-space-200 transition-colors"
            >
              <SkipBack className="w-4 h-4" />
            </button>
            <button 
              onClick={() => setIsPlaying(!isPlaying)}
              className="p-3 rounded-xl bg-neon-500/15 text-neon-400 border border-neon-500/25 hover:bg-neon-500/25 transition-colors neon-glow"
            >
              {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
            </button>
            <button 
              onClick={() => setCurrentFrameIndex(prev => (prev + 1) % frames.length)}
              className="p-2 rounded-lg hover:bg-space-800/50 text-space-500 hover:text-space-200 transition-colors"
            >
              <SkipForward className="w-4 h-4" />
            </button>
            <div className="mx-4 h-6 w-px bg-space-700" />
            <div className="flex items-center gap-2 text-xs text-space-500">
              <span>Speed:</span>
              <input 
                type="range" min={100} max={2000} value={speed} 
                onChange={(e) => setSpeed(Number(e.target.value))}
                className="w-24 h-1 rounded-full bg-space-700 appearance-none [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-neon-500" 
              />
              <span className="font-mono text-neon-400 w-12">{speed}ms</span>
            </div>
          </div>
        </motion.div>
      </div>
    </AppShell>
  );
}
