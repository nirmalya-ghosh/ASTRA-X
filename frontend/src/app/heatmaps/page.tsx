"use client";
import { AppShell } from "@/components/layout/AppShell";
import { Flame } from "lucide-react";

export default function HeatmapsPage() {
  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-space-100">Heatmaps</h1>
          <p className="text-sm text-space-500 mt-1">Detection density, motion magnitude, and noise distribution maps</p>
        </div>
        <div className="glass-card p-16 text-center">
          <Flame className="w-12 h-12 text-space-700 mx-auto mb-4" />
          <h3 className="text-base font-medium text-space-300 mb-2">No heatmap data</h3>
          <p className="text-sm text-space-500 max-w-md mx-auto">
            Heatmaps will be generated from detection results, showing spatial distribution of candidates, motion intensity, and noise patterns.
          </p>
        </div>
      </div>
    </AppShell>
  );
}
