"use client";

import { useState, useEffect, use } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Users, Activity, Telescope, ScanEye, Download, Star, Loader2 } from "lucide-react";
import Link from "next/link";

interface Candidate {
  id: number;
  confidence_score: number;
  ra: number | null;
  dec: number | null;
  flux: number | null;
  motion_speed: number | null;
  classification: string;
  notes?: string;
}

export default function DatasetResultsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const datasetId = resolvedParams.id;
  const [activeTab, setActiveTab] = useState("candidates");
  const [datasetName, setDatasetName] = useState(`Dataset #${datasetId}`);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
        
        // Fetch dataset name
        const dsRes = await fetch(`${apiUrl}/datasets/${datasetId}`);
        if (dsRes.ok) {
          const dsData = await dsRes.json();
          if (dsData.name) setDatasetName(dsData.name);
        }

        // Fetch candidates
        const candRes = await fetch(`${apiUrl}/candidates?dataset_id=${datasetId}&limit=50&sort_by=confidence_score&sort_desc=true`);
        if (candRes.ok) {
          const candData = await candRes.json();
          setCandidates(candData.candidates || []);
        }
      } catch (err) {
        console.error("Failed to fetch data", err);
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, [datasetId]);

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-[#ededed]">{datasetName}</h1>
            <p className="text-[#a1a1aa] mt-1 text-sm">Dataset #{datasetId} • {candidates.length} Candidates found</p>
          </div>
          <div className="flex items-center gap-3">
            <button className="flex items-center gap-2 vercel-button-secondary px-4 py-2 text-sm">
              <Download className="w-4 h-4" />
              Export Data
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-6 border-b border-[#333] mb-8">
          <button 
            onClick={() => setActiveTab("candidates")}
            className={`pb-3 border-b-2 text-sm font-medium transition-colors ${activeTab === "candidates" ? "border-[#ededed] text-[#ededed]" : "border-transparent text-[#a1a1aa] hover:text-[#ededed]"}`}
          >
            Detected Candidates
          </button>
          <button 
            onClick={() => setActiveTab("advanced")}
            className={`pb-3 border-b-2 text-sm font-medium transition-colors ${activeTab === "advanced" ? "border-[#ededed] text-[#ededed]" : "border-transparent text-[#a1a1aa] hover:text-[#ededed]"}`}
          >
            Advanced Tools
          </button>
        </div>

        {/* Main Content Area */}
        {activeTab === "candidates" && (
          <div className="space-y-4">
            <h2 className="text-sm font-medium text-[#ededed]">High Confidence Asteroids</h2>
            
            {isLoading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-[#71717a]" />
              </div>
            ) : candidates.length === 0 ? (
              <div className="text-center py-12 border border-dashed border-[#333] rounded-lg bg-[#0a0a0a]">
                <Star className="w-8 h-8 text-[#333] mx-auto mb-3" />
                <p className="text-[#a1a1aa] text-sm">No significant asteroid candidates detected in this dataset.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {candidates.map((candidate, i) => (
                  <div key={candidate.id} className="vercel-card p-4 flex gap-4 hover:border-[#888] transition-colors cursor-default">
                    <div className="w-16 h-16 bg-[#111] rounded border border-[#333] flex items-center justify-center shrink-0">
                      <Star className={`w-6 h-6 ${candidate.confidence_score > 0.8 ? 'text-white' : 'text-[#71717a]'}`} />
                    </div>
                    <div>
                      <h3 className="font-medium text-[#ededed] text-sm">Candidate AST-{candidate.id}</h3>
                      <p className="text-xs text-[#a1a1aa] mt-1">
                        Confidence: {(candidate.confidence_score * 100).toFixed(1)}%
                      </p>
                      <div className="text-xs text-[#71717a] mt-1 space-y-0.5">
                        <p>RA: {candidate.ra ? candidate.ra.toFixed(4) : 'N/A'} • DEC: {candidate.dec ? candidate.dec.toFixed(4) : 'N/A'}</p>
                        {candidate.motion_speed && <p>Speed: {candidate.motion_speed.toFixed(2)} px/hr</p>}
                        {candidate.flux && <p>Flux: {candidate.flux.toFixed(2)}</p>}
                      </div>
                      
                      {candidate.notes && (
                        <div className="mt-2 p-2 bg-[#111] rounded text-xs text-[#a1a1aa] border border-[#333]">
                          {candidate.notes}
                        </div>
                      )}
                      
                      <div className="mt-3 flex items-center gap-2">
                        <span className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full font-medium ${candidate.classification === 'confirmed' ? 'bg-emerald-950 text-emerald-400 border border-emerald-900' : candidate.classification === 'rejected' ? 'bg-red-950 text-red-400 border border-red-900' : 'bg-[#111] text-[#71717a] border border-[#333]'}`}>
                          {candidate.classification}
                        </span>
                        
                        <button 
                          onClick={async (e) => {
                            e.preventDefault();
                            try {
                              const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/candidates/${candidate.id}/classify-ai`, { method: 'POST' });
                              if (res.ok) {
                                const updated = await res.json();
                                setCandidates(prev => prev.map(c => c.id === updated.id ? updated : c));
                              }
                            } catch (err) {
                              console.error(err);
                            }
                          }}
                          className="ml-auto text-xs bg-[#111] hover:bg-[#222] border border-[#333] text-[#ededed] px-2 py-1 rounded transition-colors"
                        >
                          Run AI Analysis
                        </button>
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
