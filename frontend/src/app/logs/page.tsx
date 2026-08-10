"use client";
import { AppShell } from "@/components/layout/AppShell";
import { motion } from "framer-motion";
import { Search } from "lucide-react";
import { useState } from "react";

const sampleLogs = [
  { time: "23:07:51", level: "INFO", source: "system", message: "AstraX AI started successfully" },
  { time: "23:07:51", level: "INFO", source: "database", message: "SQLite database initialized" },
  { time: "23:07:52", level: "INFO", source: "engine", message: "Processing engine ready (4 workers)" },
  { time: "23:07:52", level: "WARN", source: "gpu", message: "CUDA not detected, GPU acceleration disabled" },
  { time: "23:07:52", level: "INFO", source: "ai", message: "AI Assistant: no provider configured" },
];

export default function LogsPage() {
  const [logLevel, setLogLevel] = useState("all");

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-space-100">Logs</h1>
            <p className="text-sm text-space-500 mt-1">Real-time application log viewer</p>
          </div>
        </div>

        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-space-500" />
            <input type="text" placeholder="Filter logs..." className="w-full pl-10 pr-4 py-2 rounded-lg bg-space-800/30 border border-space-700/50 text-sm text-space-200 placeholder:text-space-600 focus:border-neon-500/30 focus:outline-none" />
          </div>
          <select value={logLevel} onChange={e => setLogLevel(e.target.value)} className="px-3 py-2 rounded-lg bg-space-800/30 border border-space-700/50 text-sm text-space-300 focus:outline-none">
            <option value="all">All Levels</option>
            <option value="debug">Debug</option>
            <option value="info">Info</option>
            <option value="warn">Warning</option>
            <option value="error">Error</option>
          </select>
        </div>

        <div className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <div className="font-mono text-xs p-4 space-y-0.5 min-w-[600px]">
              {sampleLogs.map((log, i) => (
                <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }}
                  className="flex gap-4 py-1 px-2 rounded hover:bg-space-800/30"
                >
                  <span className="text-space-600 shrink-0">{log.time}</span>
                  <span className={`shrink-0 w-12 ${
                    log.level === "ERROR" ? "text-rose-glow" :
                    log.level === "WARN" ? "text-amber-glow" :
                    log.level === "DEBUG" ? "text-space-500" :
                    "text-neon-400"
                  }`}>{log.level}</span>
                  <span className="text-violet-glow shrink-0 w-20">[{log.source}]</span>
                  <span className="text-space-300">{log.message}</span>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
