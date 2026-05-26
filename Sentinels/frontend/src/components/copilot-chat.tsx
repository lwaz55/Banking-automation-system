"use client";

import { useState, useEffect, useRef } from "react";
import { MessageSquare, X, Send, Bot, Sparkles, AlertCircle } from "lucide-react";
import { chatWithCopilot } from "@/lib/api";
import { Button } from "./ui/button";

interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
}

export function CopilotChat({ ticketId }: { ticketId: string | number }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Initialize with welcome message when ticket changes
  useEffect(() => {
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        text: `Hello! I am your AI Risk Copilot. I have synthesized the original event data, the department-specific risk reports, and the Chief Risk Officer's final debate ruling.\n\nHow can I help you analyze the risk findings for Ticket #${ticketId} today?`,
      },
    ]);
  }, [ticketId]);

  // Scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading]);

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessageText = input.trim();
    setInput("");

    // Add user message
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      text: userMessageText,
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await chatWithCopilot(ticketId, userMessageText);
      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        text: response.reply || "I am unable to generate a response at the moment.",
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error(err);
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        text: "Sorry, I encountered an error trying to connect to the Copilot service. Please try again.",
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Floating Toggle Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 px-5 py-3 rounded-full bg-primary text-primary-foreground font-semibold shadow-2xl shadow-primary/30 border border-primary/20 hover:scale-105 transition-all duration-300 group hover:shadow-primary/50"
      >
        <div className="relative">
          <MessageSquare className="w-5 h-5 animate-pulse" />
          <span className="absolute -top-1.5 -right-1.5 flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sentinel-green opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-sentinel-green"></span>
          </span>
        </div>
        <span>AI Copilot</span>
        <Sparkles className="w-4 h-4 text-sentinel-amber opacity-80 group-hover:rotate-12 transition-transform" />
      </button>

      {/* Slide-over Panel Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-background/60 backdrop-blur-sm z-50 transition-opacity duration-300"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Slide-over Chat Panel */}
      <div
        className={`fixed right-0 top-0 h-full w-[420px] max-w-full bg-card/95 border-l border-border/80 shadow-2xl z-50 flex flex-col backdrop-blur-xl transition-all duration-300 ease-out transform ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Panel Header */}
        <div className="p-4 border-b border-border/50 flex items-center justify-between bg-secondary/20">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-primary/10 text-primary border border-primary/20 shadow-[0_0_15px_rgba(var(--primary-glow),0.1)]">
              <Bot className="w-5 h-5 text-sentinel-blue" />
            </div>
            <div>
              <h3 className="font-bold text-base flex items-center gap-1.5 text-foreground">
                AI Risk Copilot
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-sentinel-blue/10 text-sentinel-blue border border-sentinel-blue/20">
                  Active
                </span>
              </h3>
              <p className="text-[11px] text-muted-foreground">Contextualized on TKT-{String(ticketId).padStart(4, "0")}</p>
            </div>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Panel Messages Container */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 animate-in fade-in slide-in-from-bottom-2 duration-300 ${
                msg.role === "user" ? "flex-row-reverse" : "flex-row"
              }`}
            >
              {/* Avatar */}
              {msg.role === "assistant" && (
                <div className="w-7 h-7 rounded-full bg-secondary border border-border flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-sentinel-blue" />
                </div>
              )}

              {/* Message Bubble */}
              <div
                className={`p-3 rounded-xl text-sm leading-relaxed max-w-[85%] border shadow-sm ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground border-primary/20 rounded-tr-none"
                    : "glass-card text-foreground border-border/80 rounded-tl-none whitespace-pre-wrap"
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex gap-3 animate-pulse">
              <div className="w-7 h-7 rounded-full bg-secondary border border-border flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-sentinel-blue" />
              </div>
              <div className="glass-card text-muted-foreground p-4 rounded-xl rounded-tl-none border-border/80 flex items-center gap-2">
                <div className="spinner w-3.5 h-3.5 border-t-sentinel-blue border-sentinel-blue/20"></div>
                <span className="text-xs">Copilot is analyzing details...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Panel Input Area */}
        <form onSubmit={handleSend} className="p-4 border-t border-border/50 bg-secondary/10 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about this ticket..."
            disabled={isLoading}
            className="flex-1 px-3 py-2 bg-secondary/50 border border-border/80 rounded-lg text-sm placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors disabled:opacity-50"
          />
          <Button
            type="submit"
            disabled={!input.trim() || isLoading}
            variant="default"
            size="icon"
            className="bg-primary text-primary-foreground hover:bg-primary/90 flex items-center justify-center shrink-0"
          >
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </>
  );
}
