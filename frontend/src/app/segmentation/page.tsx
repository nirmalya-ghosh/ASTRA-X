"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import {
  Layers, Play, Loader2, Star, CircleDot,
  Target
} from "lucide-react";

interface SegSource {
  source_id: number;
  class_name: string;
  score: number;
  bbox: number[];
  x_centroid: number;
  y_centroid: number;
  area_pixels: number;
  flux: number;
  ellipticity: number;
  fwhm: number;
  concentration_index: number;
}

export default function SegmentationPage() {
  const [datasetId, setDatasetId] = useState("");
  const [frameIndex, setFrameIndex] = useState(0);
  const [threshold, setThreshold] = useState(3.0);
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState<SegSource[]>([]);
  const [stats, setStats] = useState<{ n_stars: number; n_galaxies: number; total: number } | null>(null);
  const [error, setError] = useState("");

  async function runSegmentation() {
    if (!datasetId) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch(
        `${(await import("@/lib/api")).getApiUrl()}/detection/segmentation`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            dataset_id: parseInt(datasetId),
            frame_index: frameIndex,
            threshold_sigma: threshold,
          }),
        }
      );
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setSources(data.sources || []);
      setStats({
        n_stars: data.n_stars || 0,
        n_galaxies: data.n_galaxies || 0,
        total: data.sources?.length || 0,
      });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Segmentation failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-[#ededed] flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-purple-500/30 flex items-center justify-center">
              <Layers className="w-4 h-4 text-purple-400" />
            </div>
            Instance Segmentation
          </h1>
          <p className="text-[#71717a] text-sm mt-1">
            Detect, classify (star/galaxy), and deblend astronomical sources
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="vercel-card p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <div>
            <label className="text-xs text-[#a1a1aa] mb-1.5 block">Dataset ID</label>
            <input
              type="number"
              value={datasetId}
              onChange={(e) => setDatasetId(e.target.value)}
              placeholder="Enter dataset ID"
              className="vercel-input w-full px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="text-xs text-[#a1a1aa] mb-1.5 block">Frame Index</label>
            <input
              type="number"
              value={frameIndex}
              onChange={(e) => setFrameIndex(parseInt(e.target.value) || 0)}
              className="vercel-input w-full px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="text-xs text-[#a1a1aa] mb-1.5 block">Threshold (σ)</label>
            <input
              type="number"
              step="0.5"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value) || 3.0)}
              className="vercel-input w-full px-3 py-2 text-sm"
            />
          </div>
          <button
            onClick={runSegmentation}
            disabled={loading || !datasetId}
            className="vercel-button-primary px-4 py-2 text-sm flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Run Segmentation
          </button>
        </div>
        {error && <p className="text-red-400 text-xs mt-3">{error}</p>}
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="vercel-card p-4 text-center">
            <div className="text-2xl font-bold text-[#ededed]">{stats.total}</div>
            <div className="text-xs text-[#71717a] mt-1 flex items-center justify-center gap-1">
              <Target className="w-3 h-3" /> Total Sources
            </div>
          </div>
          <div className="vercel-card p-4 text-center">
            <div className="text-2xl font-bold text-yellow-400">{stats.n_stars}</div>
            <div className="text-xs text-[#71717a] mt-1 flex items-center justify-center gap-1">
              <Star className="w-3 h-3" /> Stars
            </div>
          </div>
          <div className="vercel-card p-4 text-center">
            <div className="text-2xl font-bold text-purple-400">{stats.n_galaxies}</div>
            <div className="text-xs text-[#71717a] mt-1 flex items-center justify-center gap-1">
              <CircleDot className="w-3 h-3" /> Galaxies
            </div>
          </div>
        </div>
      )}

      {/* Results Table */}
      {sources.length > 0 && (
        <div className="vercel-card overflow-hidden">
          <div className="p-4 border-b border-[#333] flex items-center justify-between">
            <h2 className="text-sm font-medium text-[#ededed]">Detected Sources</h2>
            <span className="badge">{sources.length} sources</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#222]">
                  {["ID", "Class", "Score", "X", "Y", "Flux", "FWHM", "Ellip.", "C-Index", "Area"].map(h => (
                    <th key={h} className="text-left py-3 px-4 text-[#71717a] font-medium text-xs">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sources.slice(0, 100).map((s) => (
                  <tr key={s.source_id} className="border-b border-[#111] hover:bg-[#0a0a0a] transition-colors">
                    <td className="py-2.5 px-4 text-[#a1a1aa] font-mono text-xs">{s.source_id}</td>
                    <td className="py-2.5 px-4">
                      <span className={`badge ${s.class_name === "star" ? "badge-success" : ""}`}>
                        {s.class_name === "star" ? <Star className="w-3 h-3" /> : <CircleDot className="w-3 h-3" />}
                        {s.class_name}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-[#ededed] font-mono text-xs">{(s.score * 100).toFixed(0)}%</td>
                    <td className="py-2.5 px-4 text-[#a1a1aa] font-mono text-xs">{s.x_centroid.toFixed(1)}</td>
                    <td className="py-2.5 px-4 text-[#a1a1aa] font-mono text-xs">{s.y_centroid.toFixed(1)}</td>
                    <td className="py-2.5 px-4 text-[#ededed] font-mono text-xs">{s.flux.toFixed(0)}</td>
                    <td className="py-2.5 px-4 text-[#a1a1aa] font-mono text-xs">{s.fwhm.toFixed(1)}</td>
                    <td className="py-2.5 px-4 text-[#a1a1aa] font-mono text-xs">{s.ellipticity.toFixed(3)}</td>
                    <td className="py-2.5 px-4 text-[#a1a1aa] font-mono text-xs">{s.concentration_index.toFixed(3)}</td>
                    <td className="py-2.5 px-4 text-[#71717a] font-mono text-xs">{s.area_pixels}px</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && sources.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center h-48 border border-dashed border-[#333] rounded-lg bg-[#0a0a0a]">
          <Layers className="w-8 h-8 text-[#71717a] mb-3" />
          <p className="text-[#a1a1aa] text-sm">Enter a dataset ID and run segmentation</p>
          <p className="text-[#71717a] text-xs mt-1">Inspired by Astro R-CNN • Star/Galaxy Classification</p>
        </div>
      )}
    </AppShell>
  );
}
