"use client";

import { usePathname } from "next/navigation";
import {
  Search,
  Bell,
  Cpu,
  ChevronRight,
} from "lucide-react";

interface HeaderProps {
  onCommandOpen: () => void;
}

const pathLabels: Record<string, string> = {
  "/": "Dashboard",
  "/datasets": "Dataset Manager",
  "/mission-control": "Mission Control",
  "/detection": "Detection Workspace",
  "/blink": "Blink Comparator",
  "/candidates": "Candidate Explorer",
  "/processing": "Image Processing",
  "/assistant": "AI Assistant",
  "/inspector": "Object Inspector",
  "/motion": "Motion Analytics",
  "/heatmaps": "Heatmaps",
  "/statistics": "Statistics",
  "/timeline": "Timeline",
  "/export": "Export Center",
  "/settings": "Settings",
  "/logs": "Logs",
  "/developer": "Developer Console",
};

export function Header({ onCommandOpen }: HeaderProps) {
  const pathname = usePathname();
  const pageTitle = pathLabels[pathname] || "AstraX AI";

  // Build breadcrumb
  const segments = pathname.split("/").filter(Boolean);
  const breadcrumbs = [
    { label: "AstraX", href: "/" },
    ...segments.map((seg, i) => ({
      label: seg.charAt(0).toUpperCase() + seg.slice(1).replace("-", " "),
      href: "/" + segments.slice(0, i + 1).join("/"),
    })),
  ];

  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-neon-500/10 glass-subtle shrink-0">
      {/* Breadcrumb */}
      <div className="flex items-center gap-1.5 text-sm">
        {breadcrumbs.map((crumb, i) => (
          <span key={crumb.href} className="flex items-center gap-1.5">
            {i > 0 && <ChevronRight className="w-3 h-3 text-space-600" />}
            <span
              className={
                i === breadcrumbs.length - 1
                  ? "text-space-100 font-medium"
                  : "text-space-500"
              }
            >
              {crumb.label}
            </span>
          </span>
        ))}
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-3">
        {/* Search */}
        <button
          onClick={onCommandOpen}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg glass-subtle hover:border-neon-500/30 transition-colors text-space-400 hover:text-space-200 text-xs"
        >
          <Search className="w-3.5 h-3.5" />
          <span>Search...</span>
          <kbd className="ml-2 px-1.5 py-0.5 rounded text-[10px] bg-space-800 text-space-500 border border-space-700">
            ⌘K
          </kbd>
        </button>

        {/* Processing Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg glass-subtle text-xs">
          <Cpu className="w-3.5 h-3.5 text-emerald-glow animate-glow" />
          <span className="text-space-400">Idle</span>
        </div>

        {/* Notifications */}
        <button className="relative p-2 rounded-lg hover:bg-space-800/50 transition-colors text-space-400 hover:text-space-200">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-neon-500" />
        </button>
      </div>
    </header>
  );
}
