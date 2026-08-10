"use client";

import { AppShell } from "@/components/layout/AppShell";
import { motion } from "framer-motion";
import { useRef, useState } from "react";
import {
  Bot,
  Send,
  Sparkles,
  FileText,
  HelpCircle,
  BarChart3,
  Telescope,
  Settings,
} from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function AssistantPage() {
  const idCounter = useRef(0);
  const nextMessageId = (prefix: string) => {
    idCounter.current += 1;
    return `${prefix}-${idCounter.current}`;
  };

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Welcome to AstraX AI Assistant! I can help you analyze detections, explain FITS metadata, draft observation reports, and answer astronomy questions. What would you like to explore?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");

  const chatMutation = useMutation({
    mutationFn: (message: string) => api.assistant.chat({ message }),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          id: nextMessageId(data.session_id || "assistant"),
          role: "assistant",
          content: data.content,
          timestamp: new Date(data.created_at),
        },
      ]);
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        {
          id: nextMessageId("err"),
          role: "assistant",
          content: "Sorry, I encountered an error connecting to the AI service.",
          timestamp: new Date(),
        },
      ]);
    },
  });

  const handleSend = (text: string = input) => {
    if (!text.trim()) return;

    const userMsg: Message = {
      id: nextMessageId("user"),
      role: "user",
      content: text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    chatMutation.mutate(text);
  };

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto h-[calc(100vh-8rem)] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-glow/20 to-neon-500/20 border border-violet-glow/20 flex items-center justify-center">
              <Bot className="w-5 h-5 text-violet-glow" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-space-100">AI Assistant</h1>
              <p className="text-xs text-space-500">
                Powered by your configured LLM provider
              </p>
            </div>
          </div>
          <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg glass-subtle text-space-400 hover:text-space-200 text-xs transition-colors">
            <Settings className="w-3.5 h-3.5" />
            Configure
          </button>
        </div>

        {/* Quick Actions */}
        <div className="flex gap-2 mb-4 shrink-0 overflow-x-auto pb-2">
          {[
            { icon: FileText, label: "Generate Report" },
            { icon: HelpCircle, label: "Explain Detection" },
            { icon: BarChart3, label: "Summarize Session" },
            { icon: Telescope, label: "FITS Metadata" },
          ].map(({ icon: Icon, label }) => (
            <button
              key={label}
              onClick={() => handleSend(label)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg glass-subtle text-space-400 hover:text-neon-400 hover:border-neon-500/20 text-xs transition-colors whitespace-nowrap"
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-2 mb-4">
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
            >
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-glow/20 to-neon-500/20 border border-violet-glow/15 flex items-center justify-center shrink-0 mt-1">
                  <Sparkles className="w-3.5 h-3.5 text-violet-glow" />
                </div>
              )}
              <div
                className={`max-w-[75%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-neon-500/15 text-neon-100 border border-neon-500/20"
                    : "glass-card text-space-200"
                }`}
              >
                {msg.content}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Input */}
        <div className="shrink-0 glass-prominent rounded-xl p-3">
          <div className="flex items-end gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={chatMutation.isPending}
              placeholder={chatMutation.isPending ? "AI is thinking..." : "Ask about detections, FITS metadata, or astronomy..."}
              rows={1}
              className="flex-1 bg-transparent text-sm text-space-200 placeholder:text-space-600 outline-none resize-none"
            />
            <button
              onClick={() => handleSend()}
              disabled={!input.trim()}
              className="p-2 rounded-lg bg-neon-500/15 text-neon-400 hover:bg-neon-500/25 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <div className="flex items-center gap-3 mt-2 pt-2 border-t border-space-700/30 text-[10px] text-space-600">
            <span>⏎ Send</span>
            <span>⇧⏎ New line</span>
            <span className="ml-auto">AI assists review — does not replace scientific validation</span>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
