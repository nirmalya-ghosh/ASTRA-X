"use client";

import { AppShell } from "@/components/layout/AppShell";
import { motion } from "framer-motion";
import { useState } from "react";
import {
  Settings,
  Cpu,
  Sliders,
  Bot,
  Palette,
  Keyboard,
  Shield,
  Save,
  RotateCcw,
  Zap,
} from "lucide-react";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("general");

  const tabs = [
    { id: "general", label: "General", icon: Settings },
    { id: "processing", label: "Processing", icon: Cpu },
    { id: "detection", label: "Detection", icon: Sliders },
    { id: "ai", label: "AI Assistant", icon: Bot },
    { id: "appearance", label: "Appearance", icon: Palette },
    { id: "shortcuts", label: "Shortcuts", icon: Keyboard },
  ];

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-space-100">Settings</h1>
            <p className="text-sm text-space-500 mt-1">
              Configure application behavior, processing parameters, and integrations
            </p>
          </div>
          <div className="flex gap-2">
            <button className="flex items-center gap-2 px-3 py-2 rounded-lg bg-space-800/50 text-space-400 border border-space-700 hover:text-space-200 text-xs transition-colors">
              <RotateCcw className="w-3.5 h-3.5" />
              Reset
            </button>
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-neon-500/15 text-neon-400 border border-neon-500/25 hover:bg-neon-500/25 text-xs font-medium transition-colors neon-glow">
              <Save className="w-3.5 h-3.5" />
              Save Changes
            </button>
          </div>
        </div>

        <div className="flex gap-6">
          {/* Tab Navigation */}
          <div className="w-48 shrink-0 space-y-1">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                  activeTab === id
                    ? "bg-neon-500/10 text-neon-400 border border-neon-500/15"
                    : "text-space-400 hover:text-space-200 hover:bg-space-800/50"
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>

          {/* Settings Content */}
          <div className="flex-1">
            {activeTab === "general" && (
              <SettingsSection title="General Settings" icon={Settings}>
                <SettingField label="Application Name" hint="Display name for reports">
                  <input
                    type="text"
                    defaultValue="AstraX AI"
                    className="w-full px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-200 focus:border-neon-500/30 focus:outline-none"
                  />
                </SettingField>
                <SettingField label="Data Directory" hint="Where datasets and cache are stored">
                  <input
                    type="text"
                    defaultValue="./data"
                    className="w-full px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-200 font-mono focus:border-neon-500/30 focus:outline-none"
                  />
                </SettingField>
                <SettingField label="Log Level">
                  <select className="w-full px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-300 focus:border-neon-500/30 focus:outline-none">
                    <option>INFO</option>
                    <option>DEBUG</option>
                    <option>WARNING</option>
                    <option>ERROR</option>
                  </select>
                </SettingField>
              </SettingsSection>
            )}

            {activeTab === "processing" && (
              <SettingsSection title="Processing Engine" icon={Cpu}>
                <SettingToggle
                  label="GPU Acceleration"
                  hint="Use CuPy/CUDA when available"
                  icon={Zap}
                  defaultChecked={false}
                />
                <SettingField label="CPU Worker Threads" hint="Number of parallel processing threads">
                  <input
                    type="number"
                    defaultValue={4}
                    min={1}
                    max={32}
                    className="w-full px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-200 focus:border-neon-500/30 focus:outline-none"
                  />
                </SettingField>
                <SettingField label="Upload Chunk Size" hint="MB per chunk for file uploads">
                  <input
                    type="number"
                    defaultValue={10}
                    min={1}
                    max={100}
                    className="w-full px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-200 focus:border-neon-500/30 focus:outline-none"
                  />
                </SettingField>
              </SettingsSection>
            )}

            {activeTab === "detection" && (
              <SettingsSection title="Detection Defaults" icon={Sliders}>
                <SettingField label="Default FWHM" hint="Full-width at half-maximum (pixels)">
                  <input type="number" defaultValue={3.0} step={0.5} className="w-full px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-200 focus:border-neon-500/30 focus:outline-none" />
                </SettingField>
                <SettingField label="Detection Threshold (σ)" hint="Sigma above background for detection">
                  <input type="number" defaultValue={5.0} step={0.5} className="w-full px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-200 focus:border-neon-500/30 focus:outline-none" />
                </SettingField>
                <SettingField label="Motion Threshold" hint="Minimum motion (pixels) to flag as candidate">
                  <input type="number" defaultValue={2.0} step={0.5} className="w-full px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-200 focus:border-neon-500/30 focus:outline-none" />
                </SettingField>
                <SettingField label="Confidence Threshold" hint="Minimum score to include in results (0-1)">
                  <input type="number" defaultValue={0.5} step={0.05} min={0} max={1} className="w-full px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-200 focus:border-neon-500/30 focus:outline-none" />
                </SettingField>
                <SettingField label="Noise Sigma Clip" hint="Sigma clipping level for background estimation">
                  <input type="number" defaultValue={3.0} step={0.5} className="w-full px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-200 focus:border-neon-500/30 focus:outline-none" />
                </SettingField>
              </SettingsSection>
            )}

            {activeTab === "ai" && (
              <SettingsSection title="AI Assistant Configuration" icon={Bot}>
                <SettingField label="LLM Provider" hint="Select your preferred AI provider">
                  <select className="w-full px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-300 focus:border-neon-500/30 focus:outline-none">
                    <option value="">Not configured</option>
                    <option value="gemini">Google Gemini</option>
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="openrouter">OpenRouter</option>
                  </select>
                </SettingField>
                <SettingField label="Model" hint="Specific model to use">
                  <input type="text" placeholder="e.g., gemini-2.0-flash, gpt-4o, claude-sonnet-4-20250514" className="w-full px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-200 placeholder:text-space-600 focus:border-neon-500/30 focus:outline-none" />
                </SettingField>
                <SettingField label="API Key" hint="Stored securely. Set via ASTRAX_LLM_API_KEY environment variable for production.">
                  <input type="password" placeholder="sk-..." className="w-full px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-200 placeholder:text-space-600 focus:border-neon-500/30 focus:outline-none font-mono" />
                </SettingField>
                <SettingField label="Base URL (optional)" hint="Custom API endpoint for OpenAI-compatible providers">
                  <input type="text" placeholder="https://api.openai.com/v1" className="w-full px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-200 placeholder:text-space-600 focus:border-neon-500/30 focus:outline-none font-mono" />
                </SettingField>

                <div className="mt-4 p-3 rounded-lg bg-amber-glow/5 border border-amber-glow/15">
                  <div className="flex items-start gap-2">
                    <Shield className="w-4 h-4 text-amber-glow shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs text-amber-glow font-medium">Security Note</p>
                      <p className="text-xs text-space-400 mt-1">
                        For production deployments, store API keys using environment
                        variables (ASTRAX_LLM_API_KEY) rather than this UI. Keys entered
                        here are only stored in memory for the current session.
                      </p>
                    </div>
                  </div>
                </div>
              </SettingsSection>
            )}

            {activeTab === "appearance" && (
              <SettingsSection title="Appearance" icon={Palette}>
                <SettingField label="Theme" hint="Color scheme for the interface">
                  <select className="w-full px-3 py-2 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-300 focus:border-neon-500/30 focus:outline-none">
                    <option>Deep Space (Default)</option>
                    <option>Midnight Observatory</option>
                    <option>Nebula Purple</option>
                  </select>
                </SettingField>
                <SettingToggle label="Animations" hint="Enable smooth transitions and effects" defaultChecked={true} />
                <SettingToggle label="Star Field Background" hint="Show animated star particles" defaultChecked={true} />
              </SettingsSection>
            )}

            {activeTab === "shortcuts" && (
              <SettingsSection title="Keyboard Shortcuts" icon={Keyboard}>
                <div className="space-y-2">
                  {[
                    { keys: "⌘K", action: "Open Command Palette" },
                    { keys: "⌘B", action: "Toggle Sidebar" },
                    { keys: "←→", action: "Navigate Frames" },
                    { keys: "Space", action: "Play/Pause Blink" },
                    { keys: "A", action: "Approve Candidate" },
                    { keys: "R", action: "Reject Candidate" },
                    { keys: "F", action: "Flag Candidate" },
                    { keys: "⌘E", action: "Export" },
                    { keys: "?", action: "Show Help" },
                  ].map(({ keys, action }) => (
                    <div key={action} className="flex items-center justify-between py-2 border-b border-space-800/50">
                      <span className="text-sm text-space-300">{action}</span>
                      <kbd className="px-2 py-1 rounded text-xs bg-space-800 text-space-400 border border-space-700 font-mono">
                        {keys}
                      </kbd>
                    </div>
                  ))}
                </div>
              </SettingsSection>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function SettingsSection({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-6 space-y-5"
    >
      <h2 className="text-base font-semibold text-space-100 flex items-center gap-2">
        <Icon className="w-4 h-4 text-neon-400" />
        {title}
      </h2>
      {children}
    </motion.div>
  );
}

function SettingField({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="text-sm text-space-300 font-medium block mb-1">{label}</label>
      {hint && <p className="text-xs text-space-600 mb-2">{hint}</p>}
      {children}
    </div>
  );
}

function SettingToggle({
  label,
  hint,
  icon: Icon,
  defaultChecked = false,
}: {
  label: string;
  hint?: string;
  icon?: React.ComponentType<{ className?: string }>;
  defaultChecked?: boolean;
}) {
  const [checked, setChecked] = useState(defaultChecked);
  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center gap-2">
        {Icon && <Icon className="w-4 h-4 text-space-500" />}
        <div>
          <p className="text-sm text-space-300">{label}</p>
          {hint && <p className="text-xs text-space-600">{hint}</p>}
        </div>
      </div>
      <button
        onClick={() => setChecked(!checked)}
        className={`w-10 h-5 rounded-full transition-colors relative ${
          checked ? "bg-neon-500/30" : "bg-space-700"
        }`}
      >
        <div
          className={`absolute top-0.5 w-4 h-4 rounded-full transition-all ${
            checked
              ? "left-[calc(100%-18px)] bg-neon-400 shadow-[0_0_6px_rgba(59,130,246,0.5)]"
              : "left-0.5 bg-space-500"
          }`}
        />
      </button>
    </div>
  );
}
