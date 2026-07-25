"use client";
import { AppShell } from "@/components/layout/AppShell";
import { Clock } from "lucide-react";

export default function TimelinePage() {
  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-space-100">Timeline</h1>
          <p className="text-sm text-space-500 mt-1">Observation timeline with detection events and playback controls</p>
        </div>
        <div className="glass-card p-16 text-center">
          <Clock className="w-12 h-12 text-space-700 mx-auto mb-4" />
          <h3 className="text-base font-medium text-space-300 mb-2">No timeline data</h3>
          <p className="text-sm text-space-500 max-w-md mx-auto">
            The timeline view shows observation sequences with detection events overlaid, enabling chronological review and playback of discoveries.
          </p>
        </div>
      </div>
    </AppShell>
  );
}
