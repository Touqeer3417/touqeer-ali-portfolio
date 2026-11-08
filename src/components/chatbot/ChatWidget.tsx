"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { MessageCircle, Send, X } from "lucide-react";

type Msg = { role: "user" | "assistant"; content: string };

const GREETING: Msg = {
  role: "assistant",
  content:
    "Hi! I'm Touqeer's AI assistant. Ask me about his projects, skills or services. English ya Roman Urdu, dono chalega.",
};

const SUGGESTIONS = [
  "What has Touqeer built?",
  "Can he build a RAG chatbot for my business?",
  "Touqeer ki skills kya hain?",
  "How can I contact him?",
];

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Msg[]>([GREETING]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const warmed = useRef(false);
  const listRef = useRef<HTMLDivElement>(null);

  // wake the (free-tier) backend as soon as the visitor opens the chat
  useEffect(() => {
    if (open && !warmed.current) {
      warmed.current = true;
      fetch("/api/chat").catch(() => {});
    }
  }, [open]);

  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, open]);

  async function send(text: string) {
    const question = text.trim();
    if (!question || loading) return;

    const history: Msg[] = [
      ...messages.filter((m) => m !== GREETING),
      { role: "user" as const, content: question },
    ].slice(-10);

    setMessages((m) => [
      ...m,
      { role: "user", content: question },
      { role: "assistant", content: "" },
    ]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history }),
      });
      if (res.status === 429) throw new Error("rate");
      if (!res.ok || !res.body) throw new Error("upstream");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let acc = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        acc += decoder.decode(value, { stream: true });
        setMessages((m) => [
          ...m.slice(0, -1),
          { role: "assistant", content: acc },
        ]);
      }
    } catch (e) {
      const text =
        e instanceof Error && e.message === "rate"
          ? "Too many messages. Please wait a minute and try again."
          : "Sorry, I couldn't reach the server. Please try again in a moment.";
      setMessages((m) => [...m.slice(0, -1), { role: "assistant", content: text }]);
    } finally {
      setLoading(false);
    }
  }

  return (
      <div className="fixed bottom-4 right-4 z-[60] sm:bottom-6 sm:right-6">
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 16, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.96 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="absolute bottom-16 right-0 flex h-[min(70vh,540px)] w-[min(calc(100vw-2rem),380px)] origin-bottom-right flex-col overflow-hidden rounded-2xl border border-white/10 bg-[#0a0a12]/90 shadow-[0_0_60px_-12px_rgba(124,58,237,0.5)] backdrop-blur-xl"
          >
            {/* header */}
            <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
              <div>
                <p className="text-sm font-semibold text-white">Ask about Touqeer</p>
                <p className="text-xs text-white/50">AI assistant · English / Roman Urdu</p>
              </div>
              <button
                onClick={() => setOpen(false)}
                aria-label="Close chat"
                className="rounded-full p-1.5 text-white/60 transition hover:bg-white/10 hover:text-white"
              >
                <X size={16} />
              </button>
            </div>

            {/* messages. data-lenis-prevent = wheel scrolls THIS box, not the page */}
            <div
              ref={listRef}
              data-lenis-prevent
              className="flex-1 space-y-3 overflow-y-auto overscroll-contain px-4 py-4"
            >
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={m.role === "user" ? "flex justify-end" : "flex justify-start"}
                >
                  <div
                    className={
                      "max-w-[85%] whitespace-pre-wrap rounded-2xl px-3.5 py-2 text-sm leading-relaxed " +
                      (m.role === "user"
                        ? "bg-linear-to-br from-violet-600 to-indigo-600 text-white"
                        : "border border-white/10 bg-white/5 text-white/90")
                    }
                  >
                    {m.content || (
                      <span className="animate-pulse text-white/50">typing...</span>
                    )}
                  </div>
                </div>
              ))}

              {messages.length === 1 && (
                <div className="flex flex-wrap gap-2 pt-1">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => send(s)}
                      className="rounded-full border border-cyan-400/30 px-3 py-1 text-xs text-cyan-200 transition hover:bg-cyan-400/10"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* input */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                send(input);
              }}
              className="flex items-center gap-2 border-t border-white/10 p-3"
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                maxLength={500}
                placeholder="Ask anything about Touqeer..."
                className="flex-1 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white placeholder:text-white/40 focus:border-violet-400/60 focus:outline-none"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                aria-label="Send message"
                className="grid h-9 w-9 place-items-center rounded-full bg-linear-to-br from-violet-600 to-cyan-500 text-white transition disabled:opacity-40"
              >
                <Send size={16} />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* floating button */}
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "Close chat" : "Open chat"}
        className="grid h-14 w-14 place-items-center rounded-full bg-linear-to-br from-violet-600 to-cyan-500 text-white shadow-[0_0_30px_rgba(34,211,238,0.4)] transition-transform hover:scale-105 active:scale-95"
      >
        {open ? <X size={22} /> : <MessageCircle size={22} />}
      </button>
    </div>
  );
}
