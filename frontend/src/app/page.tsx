"use client";

import { AppShell } from "@/components/layout/AppShell";
import { Plus, Database, ChevronRight, Activity } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  return (
    <AppShell>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-[#ededed]">Overview</h1>
        <div className="flex items-center gap-3">
          <Link 
            href="/pipeline"
            className="flex items-center gap-2 bg-[#ededed] text-black px-4 py-2 rounded-md font-medium hover:bg-white transition-colors text-sm"
          >
            <Plus className="w-4 h-4" />
            New Analysis
          </Link>
        </div>
      </div>

      <div className="mb-6 flex gap-6 border-b border-[#333]">
        <button className="pb-3 border-b-2 border-[#ededed] text-[#ededed] text-sm font-medium">
          Recent Analyses
        </button>
        <button className="pb-3 border-b-2 border-transparent text-[#a1a1aa] hover:text-[#ededed] text-sm font-medium transition-colors">
          Drafts
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Empty State / Sample Card */}
        <Link href="/pipeline" className="group flex flex-col h-48 vercel-card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-[#111] border border-[#333] flex items-center justify-center">
                <Database className="w-4 h-4 text-[#ededed]" />
              </div>
              <h3 className="font-medium text-[#ededed] group-hover:text-white transition-colors">Dataset_2026_07.fits</h3>
            </div>
          </div>
          
          <div className="mt-auto">
            <div className="flex items-center gap-2 text-sm text-[#a1a1aa] mb-2">
              <Activity className="w-3.5 h-3.5" />
              <span>Processed</span>
              <span className="w-1 h-1 rounded-full bg-[#333]" />
              <span>12 Candidates</span>
            </div>
            <div className="flex items-center text-xs text-[#71717a]">
              <span>Last analyzed 2h ago</span>
              <ChevronRight className="w-3 h-3 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          </div>
        </Link>
      </div>
    </AppShell>
  );
}
