"use client";

import { useState } from "react";
import { Sparkles, X, Send, Loader2 } from "lucide-react";

export function FloatingAssistant() {
  const [isOpen, setIsOpen] = useState(false);
  const [provider, setProvider] = useState("openrouter");
  const [messages, setMessages] = useState<{ role: "user" | "ai"; content: string }[]>([
    { role: "ai", content: "Hi. I'm AstraX AI. Ask me to explain a dataset, identify a candidate, or walk you through the detection process." }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;

    const userMessage = input.trim();
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setInput("");
    setIsTyping(true);

    try {
      // Send to FastAPI Backend
      const { getApiUrl } = await import("@/lib/api");
      const response = await fetch(`${getApiUrl()}/assistant/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, provider }),
      });
      
      const data = await response.json();
      
      if (data.response) {
        setMessages(prev => [...prev, { role: "ai", content: data.response }]);
      } else if (data.content) {
        setMessages(prev => [...prev, { role: "ai", content: data.content }]);
      } else {
        setMessages(prev => [...prev, { role: "ai", content: "I encountered an error connecting to the intelligence engine." }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: "ai", content: "System error: Network unreachable. Ensure the backend is running." }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 w-12 h-12 bg-[#ededed] text-black rounded-full flex items-center justify-center shadow-lg hover:scale-105 transition-transform z-40 ${isOpen ? "hidden" : "flex"}`}
      >
        <Sparkles className="w-5 h-5" />
      </button>

      {/* Floating Chat Widget */}
      {isOpen && (
        <div className="fixed bottom-4 left-4 right-4 sm:left-auto sm:right-6 sm:bottom-6 w-auto sm:w-[400px] h-[450px] sm:h-[500px] max-h-[80vh] bg-[#0a0a0a] border border-[#333] rounded-xl shadow-2xl flex flex-col z-50 overflow-hidden animate-slide-in-up">
          {/* Header */}
          <div className="flex items-center justify-between p-3 border-b border-[#333] bg-[#000]">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#ededed]" />
              <span className="font-medium text-sm text-[#ededed]">AstraX Assistant</span>
            </div>
            
            <div className="flex items-center gap-3">
              <select 
                value={provider} 
                onChange={(e) => setProvider(e.target.value)}
                className="bg-[#111] border border-[#333] text-xs text-[#ededed] rounded px-2 py-1 outline-none focus:border-[#666]"
              >
                <option value="openrouter">OpenRouter (Claude 3.5)</option>
                <option value="deepseek">DeepSeek</option>
                <option value="openai">OpenAI (GPT-4o)</option>
                <option value="gemini">Google Gemini</option>
                <option value="grok">xAI Grok</option>
              </select>
              <button onClick={() => setIsOpen(false)} className="text-[#a1a1aa] hover:text-[#ededed] transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#0a0a0a]">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div 
                  className={`max-w-[85%] rounded-lg p-3 text-sm ${
                    msg.role === "user" 
                      ? "bg-[#333] text-[#ededed]" 
                      : "bg-[#000] border border-[#333] text-[#a1a1aa]"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <div className="max-w-[85%] rounded-lg p-3 text-sm bg-[#000] border border-[#333] text-[#a1a1aa]">
                  <Loader2 className="w-4 h-4 animate-spin" />
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <form onSubmit={handleSubmit} className="p-3 border-t border-[#333] bg-[#000]">
            <div className="relative">
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="Ask about datasets or candidates..."
                className="w-full bg-[#111] border border-[#333] rounded-lg py-2.5 pl-3 pr-10 text-sm text-[#ededed] focus:outline-none focus:border-[#666] transition-colors"
                disabled={isTyping}
              />
              <button
                type="submit"
                disabled={!input.trim() || isTyping}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-[#a1a1aa] hover:text-[#ededed] disabled:opacity-50 transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
