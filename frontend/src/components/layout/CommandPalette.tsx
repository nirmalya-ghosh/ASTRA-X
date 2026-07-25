"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Database,
  Rocket,
  Search,
  ScanEye,
  Users,
  ImagePlus,
  Bot,
  Telescope,
  Activity,
  Flame,
  BarChart3,
  Clock,
  Download,
  Settings,
  ScrollText,
  Terminal,
  type LucideIcon,
} from "lucide-react";

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

interface CommandItem {
  id: string;
  label: string;
  href: string;
  icon: LucideIcon;
  section: string;
  keywords?: string[];
}

const commands: CommandItem[] = [
  { id: "dashboard", label: "Dashboard", href: "/", icon: LayoutDashboard, section: "Pages", keywords: ["home", "overview"] },
  { id: "datasets", label: "Dataset Manager", href: "/datasets", icon: Database, section: "Pages", keywords: ["fits", "upload", "import"] },
  { id: "mission", label: "Mission Control", href: "/mission-control", icon: Rocket, section: "Pages", keywords: ["pipeline", "queue"] },
  { id: "detection", label: "Detection Workspace", href: "/detection", icon: Search, section: "Pages", keywords: ["detect", "find", "sources"] },
  { id: "blink", label: "Blink Comparator", href: "/blink", icon: ScanEye, section: "Pages", keywords: ["compare", "animation", "frames"] },
  { id: "candidates", label: "Candidate Explorer", href: "/candidates", icon: Users, section: "Pages", keywords: ["review", "objects"] },
  { id: "processing", label: "Image Processing", href: "/processing", icon: ImagePlus, section: "Pages", keywords: ["calibrate", "enhance", "filter"] },
  { id: "assistant", label: "AI Assistant", href: "/assistant", icon: Bot, section: "Pages", keywords: ["chat", "ai", "explain"] },
  { id: "inspector", label: "Object Inspector", href: "/inspector", icon: Telescope, section: "Pages", keywords: ["detail", "examine"] },
  { id: "motion", label: "Motion Analytics", href: "/motion", icon: Activity, section: "Pages", keywords: ["track", "velocity"] },
  { id: "heatmaps", label: "Heatmaps", href: "/heatmaps", icon: Flame, section: "Pages", keywords: ["density", "distribution"] },
  { id: "statistics", label: "Statistics", href: "/statistics", icon: BarChart3, section: "Pages", keywords: ["stats", "charts"] },
  { id: "timeline", label: "Timeline", href: "/timeline", icon: Clock, section: "Pages", keywords: ["time", "history"] },
  { id: "export", label: "Export Center", href: "/export", icon: Download, section: "Pages", keywords: ["csv", "pdf", "report"] },
  { id: "settings", label: "Settings", href: "/settings", icon: Settings, section: "Pages", keywords: ["config", "preferences"] },
  { id: "logs", label: "Logs", href: "/logs", icon: ScrollText, section: "Pages", keywords: ["log", "debug"] },
  { id: "developer", label: "Developer Console", href: "/developer", icon: Terminal, section: "Pages", keywords: ["dev", "api"] },
];

export function CommandPalette({ open, onClose }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);

  const filtered = commands.filter((cmd) => {
    const q = query.toLowerCase();
    if (!q) return true;
    return (
      cmd.label.toLowerCase().includes(q) ||
      cmd.id.includes(q) ||
      cmd.keywords?.some((kw) => kw.includes(q))
    );
  });

  const handleSelect = useCallback(
    (item: CommandItem) => {
      router.push(item.href);
      onClose();
      setQuery("");
      setSelectedIndex(0);
    },
    [router, onClose]
  );

  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        setQuery("");
        setSelectedIndex(0);
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((i) => Math.min(i + 1, filtered.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((i) => Math.max(i - 1, 0));
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (filtered[selectedIndex]) {
          handleSelect(filtered[selectedIndex]);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, filtered, selectedIndex, onClose, handleSelect]);

  // Reset selection when query changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ duration: 0.15 }}
            className="fixed top-[15%] left-1/2 -translate-x-1/2 w-full max-w-xl z-50"
          >
            <div className="glass-prominent rounded-xl overflow-hidden shadow-2xl">
              {/* Search Input */}
              <div className="flex items-center gap-3 px-4 py-3 border-b border-neon-500/10">
                <Search className="w-4 h-4 text-neon-500" />
                <input
                  autoFocus
                  type="text"
                  placeholder="Search pages, actions..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="flex-1 bg-transparent text-sm text-space-100 placeholder:text-space-500 outline-none"
                />
                <kbd className="px-1.5 py-0.5 rounded text-[10px] bg-space-800 text-space-500 border border-space-700">
                  ESC
                </kbd>
              </div>

              {/* Results */}
              <div className="max-h-80 overflow-y-auto py-2">
                {filtered.length === 0 ? (
                  <p className="text-center text-space-500 text-sm py-8">
                    No results found
                  </p>
                ) : (
                  filtered.map((item, i) => (
                    <button
                      key={item.id}
                      onClick={() => handleSelect(item)}
                      onMouseEnter={() => setSelectedIndex(i)}
                      className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                        i === selectedIndex
                          ? "bg-neon-500/10 text-neon-400"
                          : "text-space-300 hover:bg-space-800/50"
                      }`}
                    >
                      <item.icon className="w-4 h-4 shrink-0" />
                      <span>{item.label}</span>
                      <span className="ml-auto text-xs text-space-600">
                        {item.section}
                      </span>
                    </button>
                  ))
                )}
              </div>

              {/* Footer */}
              <div className="flex items-center gap-4 px-4 py-2 border-t border-neon-500/10 text-[10px] text-space-600">
                <span>↑↓ Navigate</span>
                <span>↵ Select</span>
                <span>ESC Close</span>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
