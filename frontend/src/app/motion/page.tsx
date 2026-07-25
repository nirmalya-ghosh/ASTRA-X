"use client";
import { AppShell } from "@/components/layout/AppShell";
import { Activity } from "lucide-react";

export default function MotionPage() {
  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-space-100">Motion Analytics</h1>
          <p className="text-sm text-space-500 mt-1">Visualize motion vectors, trajectories, and velocity distributions</p>
        </div>
        <div className="glass-card p-16 text-center">
          <Activity className="w-12 h-12 text-space-700 mx-auto mb-4" />
          <h3 className="text-base font-medium text-space-300 mb-2">No motion data yet</h3>
          <p className="text-sm text-space-500 max-w-md mx-auto">
            Run the detection pipeline with motion analysis enabled to visualize motion vectors, object trajectories, and velocity distributions across frames.
          </p>
        </div>
      </div>
    </AppShell>
  );
}
