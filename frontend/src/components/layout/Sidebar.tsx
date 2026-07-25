"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
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
  ChevronLeft,
  ChevronRight,
  Sparkles,
} from "lucide-react";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const navItems = [
  { href: "/", icon: LayoutDashboard, label: "Dashboard", section: "Overview" },
  { href: "/datasets", icon: Database, label: "Datasets", section: "Overview" },
  { href: "/mission-control", icon: Rocket, label: "Mission Control", section: "Overview" },
  { href: "/detection", icon: Search, label: "Detection", section: "Analysis" },
  { href: "/blink", icon: ScanEye, label: "Blink Comparator", section: "Analysis" },
  { href: "/candidates", icon: Users, label: "Candidates", section: "Analysis" },
  { href: "/processing", icon: ImagePlus, label: "Processing", section: "Analysis" },
  { href: "/assistant", icon: Bot, label: "AI Assistant", section: "Tools" },
  { href: "/inspector", icon: Telescope, label: "Inspector", section: "Tools" },
  { href: "/motion", icon: Activity, label: "Motion", section: "Tools" },
  { href: "/heatmaps", icon: Flame, label: "Heatmaps", section: "Visualization" },
  { href: "/statistics", icon: BarChart3, label: "Statistics", section: "Visualization" },
  { href: "/timeline", icon: Clock, label: "Timeline", section: "Visualization" },
  { href: "/export", icon: Download, label: "Export", section: "System" },
  { href: "/settings", icon: Settings, label: "Settings", section: "System" },
  { href: "/logs", icon: ScrollText, label: "Logs", section: "System" },
  { href: "/developer", icon: Terminal, label: "Developer", section: "System" },
];

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname();

  // Group items by section
  const sections = navItems.reduce(
    (acc, item) => {
      if (!acc[item.section]) acc[item.section] = [];
      acc[item.section].push(item);
      return acc;
    },
    {} as Record<string, typeof navItems>
  );

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 64 : 240 }}
      transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
      className="h-screen flex flex-col glass-prominent z-30 border-r border-neon-500/10"
    >
      {/* Logo */}
      <div className="h-16 flex items-center px-4 border-b border-neon-500/10">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-neon-500 to-violet-glow flex items-center justify-center neon-glow shrink-0">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.15 }}
                className="overflow-hidden"
              >
                <h1 className="text-base font-bold bg-gradient-to-r from-neon-400 to-cyan-glow bg-clip-text text-transparent whitespace-nowrap">
                  AstraX AI
                </h1>
                <p className="text-[10px] text-space-400 whitespace-nowrap">
                  Observatory Platform
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-6">
        {Object.entries(sections).map(([section, items]) => (
          <div key={section}>
            <AnimatePresence>
              {!collapsed && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="text-[10px] font-semibold uppercase tracking-widest text-space-500 px-3 mb-2"
                >
                  {section}
                </motion.p>
              )}
            </AnimatePresence>

            <div className="space-y-0.5">
              {items.map((item) => {
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/" && pathname.startsWith(item.href));

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`
                      flex items-center gap-3 px-3 py-2 rounded-lg text-sm
                      transition-all duration-200 group relative
                      ${
                        isActive
                          ? "bg-neon-500/15 text-neon-400 neon-border"
                          : "text-space-400 hover:text-space-200 hover:bg-space-800/50"
                      }
                    `}
                    data-tooltip={collapsed ? item.label : undefined}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="sidebar-active"
                        className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-neon-500 rounded-full"
                        transition={{ type: "spring", stiffness: 350, damping: 30 }}
                      />
                    )}

                    <item.icon
                      className={`w-4 h-4 shrink-0 ${
                        isActive ? "text-neon-400" : "text-space-500 group-hover:text-space-300"
                      }`}
                    />

                    <AnimatePresence>
                      {!collapsed && (
                        <motion.span
                          initial={{ opacity: 0, x: -5 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: -5 }}
                          transition={{ duration: 0.1 }}
                          className="whitespace-nowrap"
                        >
                          {item.label}
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Collapse Toggle */}
      <div className="p-2 border-t border-neon-500/10">
        <button
          onClick={onToggle}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-space-500 hover:text-space-300 hover:bg-space-800/50 transition-colors text-xs"
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <>
              <ChevronLeft className="w-4 h-4" />
              <span>Collapse</span>
            </>
          )}
        </button>
      </div>
    </motion.aside>
  );
}
