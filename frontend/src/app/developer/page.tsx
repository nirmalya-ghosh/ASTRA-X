"use client";
import { AppShell } from "@/components/layout/AppShell";
import { motion } from "framer-motion";
import { Terminal, Globe, Database, Cpu, Activity } from "lucide-react";

export default function DeveloperPage() {
  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-space-100">Developer Console</h1>
          <p className="text-sm text-space-500 mt-1">API explorer, performance metrics, and debugging tools</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { icon: Globe, title: "API Explorer", desc: "Interactive Swagger UI documentation", link: "http://localhost:8000/api/docs" },
            { icon: Database, title: "Database Browser", desc: "Browse SQLite tables and records" },
            { icon: Cpu, title: "Performance Metrics", desc: "Processing times, memory usage, throughput" },
            { icon: Activity, title: "Task Monitor", desc: "Background task queue status and history" },
          ].map(({ icon: Icon, title, desc }) => (
            <motion.div key={title} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-5 group cursor-pointer">
              <Icon className="w-6 h-6 text-space-500 group-hover:text-neon-400 transition-colors mb-3" />
              <h3 className="text-sm font-medium text-space-200 group-hover:text-space-100 mb-1">{title}</h3>
              <p className="text-xs text-space-500">{desc}</p>
            </motion.div>
          ))}
        </div>

        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-space-200 flex items-center gap-2 mb-4">
            <Terminal className="w-4 h-4 text-neon-400" />
            Quick Commands
          </h3>
          <div className="font-mono text-xs space-y-2">
            <div className="flex items-center gap-2 p-2 rounded bg-space-800/30">
              <span className="text-neon-400">$</span>
              <span className="text-space-300">curl http://localhost:8000/api/v1/health</span>
            </div>
            <div className="flex items-center gap-2 p-2 rounded bg-space-800/30">
              <span className="text-neon-400">$</span>
              <span className="text-space-300">python -m astrax_engine --detect /path/to/fits</span>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
