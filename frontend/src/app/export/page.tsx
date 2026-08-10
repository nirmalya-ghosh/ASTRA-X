"use client";
import { AppShell } from "@/components/layout/AppShell";
import { motion } from "framer-motion";
import { FileText, FileJson, FileImage, Archive, Table2 } from "lucide-react";

const exportFormats = [
  { icon: Table2, label: "CSV", desc: "Candidate data as spreadsheet", ext: ".csv" },
  { icon: FileJson, label: "JSON", desc: "Structured candidate database", ext: ".json" },
  { icon: FileText, label: "PDF Report", desc: "Observation report with charts", ext: ".pdf" },
  { icon: FileImage, label: "Annotated PNG", desc: "Images with detection overlays", ext: ".png" },
  { icon: FileText, label: "Observation Log", desc: "Text-based observation record", ext: ".md" },
  { icon: Archive, label: "Session Archive", desc: "Complete session data (ZIP)", ext: ".zip" },
];

export default function ExportPage() {
  return (
    <AppShell>
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-space-100">Export Center</h1>
          <p className="text-sm text-space-500 mt-1">Export candidates, reports, and session data in multiple formats</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {exportFormats.map(({ icon: Icon, label, desc, ext }) => (
            <motion.button
              key={label}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="glass-card p-5 text-left group"
            >
              <Icon className="w-6 h-6 text-space-500 group-hover:text-neon-400 transition-colors mb-3" />
              <h3 className="text-sm font-medium text-space-200 group-hover:text-space-100 mb-1">{label}</h3>
              <p className="text-xs text-space-500">{desc}</p>
              <span className="text-[10px] text-space-600 font-mono mt-2 block">{ext}</span>
            </motion.button>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
