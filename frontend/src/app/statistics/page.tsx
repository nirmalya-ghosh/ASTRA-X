"use client";
import { AppShell } from "@/components/layout/AppShell";
import { BarChart3 } from "lucide-react";

export default function StatisticsPage() {
  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-space-100">Statistics</h1>
          <p className="text-sm text-space-500 mt-1">Per-frame statistics, histograms, photometry plots, and confidence distributions</p>
        </div>
        <div className="glass-card p-16 text-center">
          <BarChart3 className="w-12 h-12 text-space-700 mx-auto mb-4" />
          <h3 className="text-base font-medium text-space-300 mb-2">No statistical data</h3>
          <p className="text-sm text-space-500 max-w-md mx-auto">
            Import a dataset and run analysis to view per-frame statistics, source count trends, confidence distributions, and photometric scatter plots.
          </p>
        </div>
      </div>
    </AppShell>
  );
}
