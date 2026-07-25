"use client";

import { useState, useEffect } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Plus, Database, ChevronRight, Activity, Loader2 } from "lucide-react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";

interface Dataset {
  id: number;
  name: string;
  status: string;
  file_count: number;
  created_at: string;
}

export default function DashboardPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchDatasets() {
      try {
        const { getApiUrl } = await import("@/lib/api");
        const res = await fetch(`${getApiUrl()}/datasets?limit=10`);
        if (res.ok) {
          const data = await res.json();
          setDatasets(data.datasets || []);
        }
      } catch (err) {
        console.error("Failed to fetch datasets", err);
      } finally {
        setIsLoading(false);
      }
    }
    fetchDatasets();
  }, []);

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

      {isLoading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="w-6 h-6 text-[#71717a] animate-spin" />
        </div>
      ) : datasets.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 border border-dashed border-[#333] rounded-lg bg-[#0a0a0a]">
          <Database className="w-8 h-8 text-[#71717a] mb-3" />
          <p className="text-[#a1a1aa] text-sm">No recent analyses found.</p>
          <Link href="/pipeline" className="text-[#ededed] text-sm mt-2 hover:underline">Start a new analysis</Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {datasets.map((dataset) => (
            <Link key={dataset.id} href={`/datasets/${dataset.id}`} className="group flex flex-col h-48 vercel-card p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#111] border border-[#333] flex items-center justify-center shrink-0">
                    <Database className="w-4 h-4 text-[#ededed]" />
                  </div>
                  <h3 className="font-medium text-[#ededed] group-hover:text-white transition-colors truncate" title={dataset.name}>
                    {dataset.name}
                  </h3>
                </div>
              </div>
              
              <div className="mt-auto">
                <div className="flex items-center gap-2 text-sm text-[#a1a1aa] mb-2">
                  <Activity className="w-3.5 h-3.5" />
                  <span className="capitalize">{dataset.status}</span>
                  <span className="w-1 h-1 rounded-full bg-[#333]" />
                  <span>{dataset.file_count} Files</span>
                </div>
                <div className="flex items-center text-xs text-[#71717a]">
                  <span>{formatDistanceToNow(new Date(dataset.created_at), { addSuffix: true })}</span>
                  <ChevronRight className="w-3 h-3 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </AppShell>
  );
}
