"use client";

import { AppShell } from "@/components/layout/AppShell";
import { motion } from "framer-motion";
import { useState } from "react";
import {
  Users,
  Search,
  Filter,
  SortDesc,
  Check,
  X,
  Flag,
  Star,
  Eye,
  ChevronDown,
  ArrowUpRight,
  Sparkles,
  Activity,
} from "lucide-react";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function CandidatesPage() {
  const [datasetId, setDatasetId] = useState<number | undefined>();
  const [classification, setClassification] = useState<string>("unreviewed");
  
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["candidates", { datasetId, classification }],
    queryFn: () => api.candidates.list({ 
      dataset_id: datasetId,
      classification: classification || undefined 
    }),
  });

  const candidates = data?.candidates || [];
  const totalItems = data?.total || 0;
  
  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-space-100">Candidate Explorer</h1>
            <p className="text-sm text-space-500 mt-1">
              Review, classify, and manage detected moving-object candidates
            </p>
          </div>
          <div className="flex gap-2">
            <button className="flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-glow/10 text-emerald-glow border border-emerald-glow/20 hover:bg-emerald-glow/20 text-xs transition-colors">
              <Check className="w-3.5 h-3.5" />
              Confirm Selected
            </button>
            <button className="flex items-center gap-2 px-3 py-2 rounded-lg bg-rose-glow/10 text-rose-glow border border-rose-glow/20 hover:bg-rose-glow/20 text-xs transition-colors">
              <X className="w-3.5 h-3.5" />
              Reject Selected
            </button>
          </div>
        </div>

        {/* Filters Bar */}
        <div className="glass-card p-4">
          <div className="flex gap-3 flex-wrap">
            <div className="flex-1 min-w-[200px] relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-space-500" />
              <input
                type="text"
                placeholder="Search candidates..."
                className="w-full pl-10 pr-4 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-200 placeholder:text-space-600 focus:border-neon-500/30 focus:outline-none"
              />
            </div>

            <div className="flex gap-2">
              <select 
                value={classification}
                onChange={(e) => setClassification(e.target.value)}
                className="px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-300 focus:border-neon-500/30 focus:outline-none appearance-none pr-8"
              >
                <option value="">All Classifications</option>
                <option value="unreviewed">Unreviewed</option>
                <option value="confirmed">Confirmed</option>
                <option value="rejected">Rejected</option>
                <option value="flagged">Flagged</option>
              </select>

              <select className="px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-300 focus:border-neon-500/30 focus:outline-none appearance-none pr-8">
                <option value="confidence_score">Sort: Confidence</option>
                <option value="snr">Sort: SNR</option>
                <option value="magnitude">Sort: Magnitude</option>
                <option value="created_at">Sort: Date</option>
              </select>

              <button className="flex items-center gap-2 px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-space-400 hover:text-space-200 text-sm transition-colors">
                <SortDesc className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="flex gap-6 mt-4 pt-4 border-t border-space-700/50">
            <QuickStat label="Total" value="0" />
            <QuickStat label="Unreviewed" value="0" color="text-amber-glow" />
            <QuickStat label="Confirmed" value="0" color="text-emerald-glow" />
            <QuickStat label="Rejected" value="0" color="text-rose-glow" />
            <QuickStat label="Flagged" value="0" color="text-violet-glow" />
          </div>
        </div>

        {/* Candidates Grid */}
        {candidates.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass-card p-16 text-center"
          >
            <div className="w-20 h-20 rounded-2xl bg-space-800/50 flex items-center justify-center mx-auto mb-6">
              <Users className="w-9 h-9 text-space-600" />
            </div>
            <h3 className="text-lg font-semibold text-space-200 mb-2">
              No candidates detected yet
            </h3>
            <p className="text-sm text-space-500 max-w-md mx-auto mb-6">
              Run the detection pipeline on a dataset to identify moving-object
              candidates. Each candidate will appear here with confidence scores
              and measurement data.
            </p>
            <div className="flex justify-center gap-6 text-xs text-space-600">
              <span className="flex items-center gap-1.5">
                <Star className="w-3.5 h-3.5" /> Confidence ranking
              </span>
              <span className="flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5" /> Motion vectors
              </span>
              <span className="flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" /> AI explanations
              </span>
            </div>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Candidate cards would render here */}
          </div>
        )}
      </div>
    </AppShell>
  );
}

function QuickStat({
  label,
  value,
  color = "text-space-200",
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="text-center">
      <p className={`text-lg font-bold ${color}`}>{value}</p>
      <p className="text-[10px] text-space-500 uppercase tracking-wider">{label}</p>
    </div>
  );
}
