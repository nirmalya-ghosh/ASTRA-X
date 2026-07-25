"use client";
import { AppShell } from "@/components/layout/AppShell";
import { Telescope } from "lucide-react";
import { WebGLFitsViewer } from "@/components/visualization/WebGLFitsViewer";

export default function InspectorPage() {
  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-space-100">Object Inspector</h1>
          <p className="text-sm text-space-500 mt-1">Detailed examination of individual candidates with full measurement data</p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 glass-prominent rounded-xl overflow-hidden h-[500px]">
            {/* We mock a URL for now to show the interactive viewer */}
            <WebGLFitsViewer 
              imageUrl="/api/v1/datasets/1/frames/1/preview" 
              className="w-full h-full"
            />
          </div>
          <div className="glass-card p-6 space-y-6">
            <div>
              <h3 className="text-lg font-bold text-space-100">Candidate Data</h3>
              <p className="text-xs text-space-500">Metadata and scientific measurements</p>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-space-800">
                <span className="text-xs text-space-400">Centroid X/Y</span>
                <span className="text-sm font-mono text-space-200">1024.5, 512.2</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-space-800">
                <span className="text-xs text-space-400">Right Ascension</span>
                <span className="text-sm font-mono text-space-200">12h 34m 56s</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-space-800">
                <span className="text-xs text-space-400">Declination</span>
                <span className="text-sm font-mono text-space-200">+45° 20' 11"</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-space-800">
                <span className="text-xs text-space-400">SNR</span>
                <span className="text-sm font-mono text-emerald-glow">18.5</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-space-800">
                <span className="text-xs text-space-400">Classification</span>
                <span className="text-sm font-mono text-amber-glow">Unreviewed</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
