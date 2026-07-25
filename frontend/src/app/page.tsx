"use client";

import { AppShell } from "@/components/layout/AppShell";
import {
  Database,
  Search,
  Users,
  Activity,
  Cpu,
  HardDrive,
  Rocket,
  TrendingUp,
  Clock,
  Sparkles,
  ArrowUpRight,
  Layers,
} from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

// Animation stagger for cards
const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06 },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

export default function DashboardPage() {
  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative overflow-hidden rounded-2xl glass-prominent p-8"
        >
          <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-neon-500/10 via-violet-glow/5 to-transparent rounded-full blur-3xl" />
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-2">
              <Sparkles className="w-5 h-5 text-neon-400 animate-glow" />
              <span className="badge badge-info">v0.1.0</span>
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-white via-neon-200 to-neon-400 bg-clip-text text-transparent mb-2">
              AstraX AI Observatory
            </h1>
            <p className="text-space-400 max-w-2xl text-sm leading-relaxed">
              Research-grade asteroid detection & astronomical image analysis platform.
              Import FITS datasets, run detection pipelines, and review moving-object
              candidates with AI-powered insights.
            </p>

            {/* Quick Actions */}
            <div className="flex gap-3 mt-6">
              <Link
                href="/datasets"
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-neon-500/15 text-neon-400 border border-neon-500/25 hover:bg-neon-500/25 transition-all text-sm font-medium neon-glow"
              >
                <Database className="w-4 h-4" />
                Import Dataset
              </Link>
              <Link
                href="/detection"
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-space-800/50 text-space-300 border border-space-700 hover:border-neon-500/30 hover:text-space-100 transition-all text-sm"
              >
                <Search className="w-4 h-4" />
                Run Detection
              </Link>
              <Link
                href="/assistant"
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-space-800/50 text-space-300 border border-space-700 hover:border-violet-glow/30 hover:text-space-100 transition-all text-sm"
              >
                <Sparkles className="w-4 h-4" />
                AI Assistant
              </Link>
            </div>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          <StatCard
            icon={Database}
            label="Datasets"
            value="0"
            change="Import to begin"
            color="neon"
          />
          <StatCard
            icon={Layers}
            label="Total Frames"
            value="0"
            change="FITS frames indexed"
            color="cyan"
          />
          <StatCard
            icon={Users}
            label="Candidates"
            value="0"
            change="Detected objects"
            color="violet"
          />
          <StatCard
            icon={Activity}
            label="Detections"
            value="0"
            change="Pipeline runs"
            color="emerald"
          />
        </motion.div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Activity */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="lg:col-span-2 glass-card p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-base font-semibold text-space-100">
                Recent Activity
              </h2>
              <Clock className="w-4 h-4 text-space-500" />
            </div>

            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="w-16 h-16 rounded-2xl bg-space-800/50 flex items-center justify-center mb-4">
                <Rocket className="w-7 h-7 text-space-600" />
              </div>
              <h3 className="text-sm font-medium text-space-300 mb-1">
                No activity yet
              </h3>
              <p className="text-xs text-space-500 max-w-xs">
                Import a FITS dataset to get started. The pipeline will
                automatically index files, detect sources, and analyze motion.
              </p>
              <Link
                href="/datasets"
                className="mt-4 flex items-center gap-1.5 text-xs text-neon-400 hover:text-neon-300 transition-colors"
              >
                Get Started <ArrowUpRight className="w-3 h-3" />
              </Link>
            </div>
          </motion.div>

          {/* System Status */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass-card p-6"
          >
            <h2 className="text-base font-semibold text-space-100 mb-6">
              System Status
            </h2>

            <div className="space-y-4">
              <SystemStatusItem
                icon={Cpu}
                label="Processing Engine"
                status="ready"
                detail="4 workers available"
              />
              <SystemStatusItem
                icon={HardDrive}
                label="Storage"
                status="ready"
                detail="Local filesystem"
              />
              <SystemStatusItem
                icon={Sparkles}
                label="AI Assistant"
                status="config"
                detail="Configure in Settings"
              />
              <SystemStatusItem
                icon={TrendingUp}
                label="GPU Acceleration"
                status="off"
                detail="Not detected"
              />
            </div>

            <div className="mt-6 pt-4 border-t border-space-700/50">
              <Link
                href="/settings"
                className="text-xs text-space-400 hover:text-neon-400 transition-colors flex items-center gap-1"
              >
                Configure Settings <ArrowUpRight className="w-3 h-3" />
              </Link>
            </div>
          </motion.div>
        </div>

        {/* Quick Navigation */}
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="grid grid-cols-2 md:grid-cols-4 gap-3"
        >
          <QuickNavCard
            href="/blink"
            icon={Search}
            title="Blink Comparator"
            description="Compare frames visually"
          />
          <QuickNavCard
            href="/processing"
            icon={Layers}
            title="Image Processing"
            description="Calibrate & enhance"
          />
          <QuickNavCard
            href="/motion"
            icon={Activity}
            title="Motion Analytics"
            description="Track moving objects"
          />
          <QuickNavCard
            href="/export"
            icon={Database}
            title="Export Center"
            description="CSV, PDF, reports"
          />
        </motion.div>
      </div>
    </AppShell>
  );
}

// ── Sub-components ───────────────────────────────────────────

function StatCard({
  icon: Icon,
  label,
  value,
  change,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  change: string;
  color: "neon" | "cyan" | "violet" | "emerald";
}) {
  const colorMap = {
    neon: "from-neon-500/20 to-neon-600/5 border-neon-500/20 text-neon-400",
    cyan: "from-cyan-glow/20 to-cyan-glow/5 border-cyan-glow/20 text-cyan-glow",
    violet: "from-violet-glow/20 to-violet-glow/5 border-violet-glow/20 text-violet-glow",
    emerald: "from-emerald-glow/20 to-emerald-glow/5 border-emerald-glow/20 text-emerald-glow",
  };

  return (
    <motion.div variants={item} className="glass-card p-5">
      <div className="flex items-center justify-between mb-3">
        <div
          className={`w-9 h-9 rounded-lg bg-gradient-to-br ${colorMap[color]} border flex items-center justify-center`}
        >
          <Icon className={`w-4 h-4`} />
        </div>
      </div>
      <p className="text-2xl font-bold text-space-100 mb-0.5">{value}</p>
      <p className="text-xs text-space-500">{label}</p>
      <p className="text-[10px] text-space-600 mt-1">{change}</p>
    </motion.div>
  );
}

function SystemStatusItem({
  icon: Icon,
  label,
  status,
  detail,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  status: "ready" | "config" | "off" | "error";
  detail: string;
}) {
  const statusColors = {
    ready: "status-dot-success",
    config: "status-dot-warning",
    off: "status-dot-info",
    error: "status-dot-danger",
  };

  return (
    <div className="flex items-center gap-3">
      <Icon className="w-4 h-4 text-space-500" />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-space-300">{label}</p>
        <p className="text-[10px] text-space-600">{detail}</p>
      </div>
      <span className={`status-dot ${statusColors[status]}`} />
    </div>
  );
}

function QuickNavCard({
  href,
  icon: Icon,
  title,
  description,
}: {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
}) {
  return (
    <motion.div variants={item}>
      <Link
        href={href}
        className="block glass-card p-4 group"
      >
        <Icon className="w-5 h-5 text-space-500 group-hover:text-neon-400 transition-colors mb-3" />
        <h3 className="text-sm font-medium text-space-200 group-hover:text-space-100 transition-colors mb-0.5">
          {title}
        </h3>
        <p className="text-[10px] text-space-600">{description}</p>
      </Link>
    </motion.div>
  );
}
