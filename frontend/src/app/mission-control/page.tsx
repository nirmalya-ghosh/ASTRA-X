"use client";
import { AppShell } from "@/components/layout/AppShell";
import { motion } from "framer-motion";
import { Rocket, CheckCircle2, Clock, Layers } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function MissionControlPage() {
  const { data: tasks = [] } = useQuery({
    queryKey: ["tasks"],
    queryFn: () => api.tasks.list(),
    refetchInterval: 5000, // poll every 5s
  });

  const activeCount = tasks.filter(t => t.status === "processing").length;
  const completedCount = tasks.filter(t => t.status === "completed").length;
  const queuedCount = tasks.filter(t => t.status === "queued").length;

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-space-100">Mission Control</h1>
          <p className="text-sm text-space-500 mt-1">Pipeline orchestration, task queue, and system monitoring</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { icon: Layers, label: "Active Tasks", value: activeCount, color: "text-neon-400" },
            { icon: CheckCircle2, label: "Completed", value: completedCount, color: "text-emerald-glow" },
            { icon: Clock, label: "Queued", value: queuedCount, color: "text-amber-glow" },
          ].map(({ icon: Icon, label, value, color }) => (
            <motion.div key={label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-5">
              <div className="flex items-center gap-3">
                <Icon className={`w-5 h-5 ${color}`} />
                <div>
                  <p className={`text-2xl font-bold ${color}`}>{value}</p>
                  <p className="text-xs text-space-500">{label}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {tasks.length === 0 ? (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-12 text-center">
            <Rocket className="w-12 h-12 text-space-700 mx-auto mb-4" />
            <h3 className="text-base font-medium text-space-300 mb-2">No active missions</h3>
            <p className="text-sm text-space-500 max-w-md mx-auto">
              Start a detection or processing pipeline to see tasks here. Mission Control provides real-time monitoring of all background operations.
            </p>
          </motion.div>
        ) : (
          <div className="space-y-3">
            {tasks.map(task => (
              <motion.div key={task.id} className="glass-card p-4 flex items-center gap-4">
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-space-100">{task.task_type.toUpperCase()}</h4>
                  <p className="text-xs text-space-500 mt-1">{task.message || "Running..."}</p>
                  <div className="w-full bg-space-800 rounded-full h-1.5 mt-2">
                    <div 
                      className={`h-1.5 rounded-full ${task.status === "completed" ? "bg-emerald-glow" : task.status === "error" ? "bg-rose-glow" : "bg-neon-500"}`}
                      style={{ width: `${task.progress}%` }}
                    />
                  </div>
                </div>
                <span className={`text-xs font-mono ${task.status === "completed" ? "text-emerald-glow" : task.status === "error" ? "text-rose-glow" : "text-neon-400"}`}>
                  {task.status} ({Math.round(task.progress)}%)
                </span>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
