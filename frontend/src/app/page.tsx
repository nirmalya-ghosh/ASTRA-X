"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  ArrowRight,
  BarChart3,
  Database,
  Download,
  Layers,
  Loader2,
  Microscope,
  Orbit,
  Play,
  Radar,
  Sparkles,
  UploadCloud,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { AppShell } from "@/components/layout/AppShell";
import { api, type Dataset } from "@/lib/api";

const workflows = [
  {
    title: "Upload and Detect",
    href: "/pipeline",
    icon: UploadCloud,
    copy: "Run FITS, image, and table inputs through source detection, motion checks, and ensemble anomaly scoring.",
  },
  {
    title: "RCNN-Style Masks",
    href: "/segmentation",
    icon: Layers,
    copy: "Segment sources into per-object masks, classify stars vs galaxies, and deblend crowded fields without heavy model weights.",
  },
  {
    title: "Candidate Review",
    href: "/candidates",
    icon: Radar,
    copy: "Triage detections with confidence, risk, persistence, and verification metadata in one review surface.",
  },
  {
    title: "Reports",
    href: "/export",
    icon: Download,
    copy: "Export CSV, JSON, and research-ready summaries for follow-up validation.",
  },
];

const engineSignals = [
  { label: "Astro R-CNN pattern", value: "Masks + deblending" },
  { label: "Astrokit pattern", value: "Photometry + airmass" },
  { label: "Tabular ML", value: "5-model ensemble" },
  { label: "Vision path", value: "OpenCV + morphology" },
];

export default function DashboardPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [health, setHealth] = useState<"online" | "offline" | "checking">("checking");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [datasetData] = await Promise.all([
          api.datasets.list({ limit: 6 }),
          api.health().then(() => setHealth("online")).catch(() => setHealth("offline")),
        ]);
        setDatasets(datasetData.datasets || []);
      } catch (err) {
        console.error("Failed to fetch dashboard data", err);
        setHealth((current) => (current === "checking" ? "offline" : current));
      } finally {
        setIsLoading(false);
      }
    }

    loadDashboard();
  }, []);

  const totalFiles = datasets.reduce((sum, dataset) => sum + dataset.file_count, 0);

  return (
    <AppShell>
      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr] mb-8">
        <div className="min-h-[360px] rounded-lg border border-[#333] bg-[#050505] overflow-hidden relative">
          <div className="absolute inset-0 opacity-70 bg-[linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:48px_48px]" />
          <div className="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-black to-transparent" />
          <div className="relative p-6 sm:p-8 h-full flex flex-col justify-between">
            <div>
              <div className="inline-flex items-center gap-2 border border-[#333] bg-black/70 rounded-full px-3 py-1 text-xs text-[#a1a1aa] mb-5">
                <Sparkles className="w-3.5 h-3.5 text-[#ededed]" />
                AstraX AI research console
              </div>
              <h1 className="text-3xl sm:text-5xl font-semibold tracking-tight text-[#ededed] max-w-2xl">
                Asteroid detection, source masks, and photometry in one working web lab.
              </h1>
              <p className="text-[#a1a1aa] text-sm sm:text-base mt-4 max-w-2xl leading-6">
                Built from this app&apos;s FastAPI/Next stack with lightweight ideas adapted from Astro R-CNN and astrokit, without shipping their notebooks, vendor assets, or heavy model weights.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 mt-8">
              <Link href="/pipeline" className="vercel-button-primary px-4 py-2.5 text-sm inline-flex items-center justify-center gap-2">
                <Play className="w-4 h-4" />
                Start Analysis
              </Link>
              <Link href="/segmentation" className="vercel-button-secondary px-4 py-2.5 text-sm inline-flex items-center justify-center gap-2">
                <Layers className="w-4 h-4" />
                Open Segmentation
              </Link>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-[#333] bg-[#0a0a0a] p-5">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-sm font-medium text-[#ededed]">System State</h2>
            <span className={`badge ${health === "online" ? "badge-success" : health === "offline" ? "badge-error" : ""}`}>
              {health}
            </span>
          </div>

          <div className="aspect-[4/3] rounded-md border border-[#222] bg-black relative overflow-hidden mb-5">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(80,227,194,0.08),transparent_52%)]" />
            <div className="absolute inset-8 border border-[#333] rounded-full" />
            <div className="absolute inset-16 border border-[#222] rounded-full" />
            <div className="absolute left-1/2 top-4 bottom-4 w-px bg-[#222]" />
            <div className="absolute top-1/2 left-4 right-4 h-px bg-[#222]" />
            <div className="absolute left-[28%] top-[35%] h-2 w-2 rounded-full bg-[#ededed] shadow-[0_0_20px_rgba(255,255,255,0.8)]" />
            <div className="absolute left-[54%] top-[46%] h-1.5 w-8 rounded-full bg-[#50e3c2] rotate-12" />
            <div className="absolute left-[67%] top-[62%] h-2.5 w-2.5 rounded-full border border-[#f5a623] bg-[#f5a623]/30" />
            <div className="absolute left-4 bottom-4 right-4 flex items-center justify-between text-[10px] text-[#71717a] font-mono">
              <span>MASK FIELD</span>
              <span>{datasets.length} DATASETS</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="border border-[#222] rounded-md p-3">
              <div className="text-2xl font-semibold text-[#ededed]">{datasets.length}</div>
              <div className="text-xs text-[#71717a] mt-1">recent datasets</div>
            </div>
            <div className="border border-[#222] rounded-md p-3">
              <div className="text-2xl font-semibold text-[#ededed]">{totalFiles}</div>
              <div className="text-xs text-[#71717a] mt-1">indexed files</div>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4 mb-8">
        {workflows.map((item) => (
          <Link key={item.href} href={item.href} className="vercel-card p-5 min-h-44 group">
            <div className="flex items-center justify-between mb-5">
              <div className="w-9 h-9 rounded-md bg-[#111] border border-[#333] flex items-center justify-center">
                <item.icon className="w-4 h-4 text-[#ededed]" />
              </div>
              <ArrowRight className="w-4 h-4 text-[#71717a] opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <h3 className="text-sm font-medium text-[#ededed] mb-2">{item.title}</h3>
            <p className="text-xs leading-5 text-[#a1a1aa]">{item.copy}</p>
          </Link>
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="vercel-card p-5">
          <h2 className="text-sm font-medium text-[#ededed] mb-4 flex items-center gap-2">
            <Microscope className="w-4 h-4" />
            Integrated Methods
          </h2>
          <div className="space-y-3">
            {engineSignals.map((signal) => (
              <div key={signal.label} className="flex items-center justify-between border-b border-[#111] pb-3 last:border-0 last:pb-0">
                <span className="text-xs text-[#71717a]">{signal.label}</span>
                <span className="text-xs text-[#ededed]">{signal.value}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="vercel-card overflow-hidden">
          <div className="p-5 border-b border-[#333] flex items-center justify-between">
            <h2 className="text-sm font-medium text-[#ededed] flex items-center gap-2">
              <Database className="w-4 h-4" />
              Recent Analyses
            </h2>
            <Link href="/datasets" className="text-xs text-[#a1a1aa] hover:text-[#ededed]">View all</Link>
          </div>

          {isLoading ? (
            <div className="h-44 flex items-center justify-center">
              <Loader2 className="w-5 h-5 text-[#71717a] animate-spin" />
            </div>
          ) : datasets.length === 0 ? (
            <div className="h-44 flex flex-col items-center justify-center text-center px-6">
              <Orbit className="w-8 h-8 text-[#71717a] mb-3" />
              <p className="text-sm text-[#a1a1aa]">No datasets have been indexed yet.</p>
              <Link href="/pipeline" className="text-sm text-[#ededed] mt-2 hover:underline">Upload the first observation</Link>
            </div>
          ) : (
            <div className="divide-y divide-[#111]">
              {datasets.map((dataset) => (
                <Link key={dataset.id} href={`/datasets/${dataset.id}`} className="flex items-center gap-4 p-4 hover:bg-[#111] transition-colors">
                  <div className="w-9 h-9 rounded-md bg-[#111] border border-[#333] flex items-center justify-center shrink-0">
                    <Activity className="w-4 h-4 text-[#ededed]" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm text-[#ededed] truncate">{dataset.name}</div>
                    <div className="text-xs text-[#71717a] mt-1">
                      {dataset.file_count} files · {formatDistanceToNow(new Date(dataset.created_at), { addSuffix: true })}
                    </div>
                  </div>
                  <div className="hidden sm:flex items-center gap-2 text-xs text-[#a1a1aa]">
                    <BarChart3 className="w-3.5 h-3.5" />
                    {dataset.status}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>
    </AppShell>
  );
}
