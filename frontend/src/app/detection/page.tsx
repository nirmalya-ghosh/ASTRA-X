"use client";

import { AppShell } from "@/components/layout/AppShell";
import { useState } from "react";
import {
  Search,
  Play,
  Sliders,
  Gauge,
  Target,
  Activity,
  Shield,
  CheckCircle2,
} from "lucide-react";

export default function DetectionPage() {
  const [isRunning, setIsRunning] = useState(false);

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-space-100">Detection Workspace</h1>
            <p className="text-sm text-space-500 mt-1">
              Configure and run the source detection & motion analysis pipeline
            </p>
          </div>
          <button
            onClick={() => setIsRunning(!isRunning)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all ${
              isRunning
                ? "bg-amber-glow/15 text-amber-glow border border-amber-glow/25"
                : "bg-neon-500/15 text-neon-400 border border-neon-500/25 hover:bg-neon-500/25 neon-glow"
            }`}
          >
            {isRunning ? (
              <>
                <div className="w-3 h-3 rounded-full bg-amber-glow animate-glow" />
                Running...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Run Detection
              </>
            )}
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Configuration Panel */}
          <div className="lg:col-span-1 space-y-4">
            {/* Dataset Selection */}
            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold text-space-200 flex items-center gap-2 mb-4">
                <Target className="w-4 h-4 text-neon-400" />
                Dataset
              </h3>
              <select className="w-full px-3 py-2.5 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-300 focus:border-neon-500/30 focus:outline-none">
                <option value="">Select a dataset...</option>
              </select>
            </div>

            {/* Detection Parameters */}
            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold text-space-200 flex items-center gap-2 mb-4">
                <Sliders className="w-4 h-4 text-neon-400" />
                Detection Parameters
              </h3>
              <div className="space-y-4">
                <ParamSlider label="FWHM" value={3.0} min={1} max={10} step={0.5} unit="px" />
                <ParamSlider label="Threshold (σ)" value={5.0} min={1} max={20} step={0.5} unit="σ" />
                <ParamSlider label="Min Persistence" value={2} min={1} max={10} step={1} unit="frames" />

                <div>
                  <label className="text-xs text-space-400 mb-1.5 block">Detection Method</label>
                  <select className="w-full px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-300 focus:border-neon-500/30 focus:outline-none">
                    <option value="dao">DAOStarFinder</option>
                    <option value="iraf">IRAFStarFinder</option>
                    <option value="adaptive">Adaptive Multi-threshold</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Motion Detection */}
            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold text-space-200 flex items-center gap-2 mb-4">
                <Activity className="w-4 h-4 text-cyan-glow" />
                Motion Detection
              </h3>
              <div className="space-y-3">
                <ToggleOption label="Frame Differencing" enabled={true} />
                <ToggleOption label="Optical Flow (Lucas-Kanade)" enabled={true} />
                <ToggleOption label="Farneback Dense Flow" enabled={false} />
                <ToggleOption label="Difference of Gaussians" enabled={false} />
                <ParamSlider label="Motion Threshold" value={2.0} min={0.5} max={10} step={0.5} unit="px" />
              </div>
            </div>

            {/* False Positive Filters */}
            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold text-space-200 flex items-center gap-2 mb-4">
                <Shield className="w-4 h-4 text-emerald-glow" />
                False Positive Filters
              </h3>
              <div className="space-y-3">
                <ToggleOption label="Cosmic Ray Detection" enabled={true} />
                <ToggleOption label="Hot/Dead Pixel Filter" enabled={true} />
                <ToggleOption label="Satellite Streak Filter" enabled={true} />
                <ToggleOption label="Saturation Filter" enabled={true} />
                <ToggleOption label="Noise Cluster Rejection" enabled={true} />
                <ToggleOption label="Duplicate Removal" enabled={true} />
              </div>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2 space-y-4">
            {/* Pipeline Status */}
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold text-space-200 flex items-center gap-2 mb-6">
                <Gauge className="w-4 h-4 text-neon-400" />
                Pipeline Status
              </h3>

              <div className="space-y-3">
                {[
                  { step: "Load Frames", status: "pending" },
                  { step: "Calibrate Images", status: "pending" },
                  { step: "Align Frames", status: "pending" },
                  { step: "Detect Sources", status: "pending" },
                  { step: "Analyze Motion", status: "pending" },
                  { step: "Filter False Positives", status: "pending" },
                  { step: "Rank Candidates", status: "pending" },
                ].map(({ step, status }) => (
                  <div key={step} className="flex items-center gap-3">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                      status === "completed"
                        ? "bg-emerald-glow/20 text-emerald-glow"
                        : status === "running"
                        ? "bg-neon-500/20 text-neon-400"
                        : "bg-space-800 text-space-600"
                    }`}>
                      {status === "completed" ? (
                        <CheckCircle2 className="w-3.5 h-3.5" />
                      ) : status === "running" ? (
                        <div className="w-2 h-2 rounded-full bg-neon-400 animate-glow" />
                      ) : (
                        <div className="w-2 h-2 rounded-full bg-space-600" />
                      )}
                    </div>
                    <span className={`text-sm ${
                      status === "completed" ? "text-space-300" :
                      status === "running" ? "text-neon-400 font-medium" :
                      "text-space-500"
                    }`}>
                      {step}
                    </span>
                    {status === "running" && (
                      <div className="ml-auto flex items-center gap-2">
                        <div className="w-32 h-1.5 rounded-full bg-space-800 overflow-hidden">
                          <div className="h-full w-1/3 rounded-full bg-neon-500 animate-shimmer" />
                        </div>
                        <span className="text-xs text-space-500">33%</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Results placeholder */}
            <div className="glass-card p-12 text-center">
              <Search className="w-12 h-12 text-space-700 mx-auto mb-4" />
              <h3 className="text-base font-medium text-space-300 mb-2">
                Ready to detect
              </h3>
              <p className="text-sm text-space-500 max-w-md mx-auto">
                Select a dataset and configure parameters, then click
                &quot;Run Detection&quot; to start the pipeline. Results will
                appear here as they are processed.
              </p>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function ParamSlider({
  label,
  value,
  min,
  max,
  step,
  unit,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit: string;
}) {
  const [val, setVal] = useState(value);
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <label className="text-xs text-space-400">{label}</label>
        <span className="text-xs text-neon-400 font-mono">{val} {unit}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={val}
        onChange={(e) => setVal(Number(e.target.value))}
        className="w-full h-1 rounded-full bg-space-700 appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-neon-500 [&::-webkit-slider-thumb]:shadow-[0_0_6px_rgba(59,130,246,0.5)]"
      />
    </div>
  );
}

function ToggleOption({
  label,
  enabled: initialEnabled,
}: {
  label: string;
  enabled: boolean;
}) {
  const [enabled, setEnabled] = useState(initialEnabled);
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-space-400">{label}</span>
      <button
        onClick={() => setEnabled(!enabled)}
        className={`w-8 h-4.5 rounded-full transition-colors relative ${
          enabled ? "bg-neon-500/30" : "bg-space-700"
        }`}
      >
        <div
          className={`absolute top-0.5 w-3.5 h-3.5 rounded-full transition-all ${
            enabled
              ? "left-[calc(100%-18px)] bg-neon-400 shadow-[0_0_6px_rgba(59,130,246,0.5)]"
              : "left-0.5 bg-space-500"
          }`}
        />
      </button>
    </div>
  );
}
