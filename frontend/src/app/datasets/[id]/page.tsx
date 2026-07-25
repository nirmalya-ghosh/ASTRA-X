"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Users, Activity, Telescope, ScanEye, Download, Star } from "lucide-react";
import Link from "next/link";

export default function DatasetResultsPage() {
  const [activeTab, setActiveTab] = useState("candidates");

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-[#ededed]">Dataset_2026_07.fits</h1>
            <p className="text-[#a1a1aa] mt-1 text-sm">Processed 2 minutes ago • 12 Candidates found</p>
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="vercel-card p-4 flex gap-4">
                  <div className="w-16 h-16 bg-[#111] rounded border border-[#333] flex items-center justify-center shrink-0">
                    <Star className="w-6 h-6 text-[#71717a]" />
                  </div>
                  <div>
                    <h3 className="font-medium text-[#ededed] text-sm">Candidate {i}</h3>
                    <p className="text-xs text-[#a1a1aa] mt-1">Confidence: {98 - (i * 2)}%</p>
                    <p className="text-xs text-[#71717a] mt-1">RA: 12h 34m • DEC: +45° 23'</p>
                  </div>
                </div>
              ))}
            </div>
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
