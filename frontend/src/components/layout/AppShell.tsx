"use client";

import { useState, useEffect } from "react";
import { Header } from "@/components/layout/Header";
import { CommandPalette } from "@/components/layout/CommandPalette";

import { FloatingAssistant } from "@/components/assistant/FloatingAssistant";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [commandOpen, setCommandOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // ⌘K or Ctrl+K for command palette
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCommandOpen((prev) => !prev);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden flex-col">
      <Header onCommandOpen={() => setCommandOpen(true)} />

      <main className="flex-1 overflow-auto bg-[#000]">
        <div className="animate-fade-in max-w-7xl mx-auto p-6 md:p-12">{children}</div>
      </main>

      <CommandPalette open={commandOpen} onClose={() => setCommandOpen(false)} />
      <FloatingAssistant />
    </div>
  );
}
