import { useEffect, useRef, useState } from "react";
import { trpc } from "@/lib/trpc";
import { AIChatBox, type Message } from "@/components/AIChatBox";
import { AgentModule } from "./AgentModule";

export type AskJayLead = { name: string; email: string };

type ChatMessage = Message & { role: "user" | "assistant" };

const OPEN_EVENT = "askjay:open";
const STORAGE_KEY = "askJayChat";
const SUGGESTED_PROMPTS = [
  "What's included in Recomp?",
  "Build me a starting plan",
  "How does applying work?",
];

/** Opens the Ask Jay panel from anywhere on the page, optionally sending a first message. */
export function openAskJay(prompt?: string) {
  window.dispatchEvent(new CustomEvent(OPEN_EVENT, { detail: { prompt } }));
}

function loadHistory(): ChatMessage[] {
  try {
    const saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY) ?? "[]");
    return Array.isArray(saved) ? saved : [];
  } catch {
    return [];
  }
}

/**
 * The "Ask Jay" assistant: a floating button that opens a chat panel. It answers
 * questions, builds sample plans, and when a visitor is ready it saves them as a
 * lead and hands them to the application with their details filled in.
 * The conversation lives only in this browser tab.
 */
export function AskJay({ available, checking, onApply }: {
  available: boolean;
  checking: boolean;
  onApply: (lead: AskJayLead) => void;
}) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>(loadHistory);
  const [lead, setLead] = useState<AskJayLead | null>(null);
  const [failed, setFailed] = useState<{ text: string; error: string } | null>(null);
  const pendingPrompt = useRef<string | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const sendMut = trpc.chat.send.useMutation();

  useEffect(() => {
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages)); } catch {}
  }, [messages]);

  function send(text: string) {
    if (sendMut.isPending) return;
    const history: ChatMessage[] = [...messages, { role: "user", content: text }];
    setMessages(history);
    setFailed(null);
    sendMut.mutate({ messages: history }, {
      onSuccess: result => {
        setMessages([...history, { role: "assistant", content: result.reply }]);
        if (result.lead) setLead(result.lead);
      },
      onError: error => {
        // Drop the unanswered message so the history stays user/assistant pairs.
        setMessages(messages);
        setFailed({ text, error: error.message });
      },
    });
  }

  useEffect(() => {
    const onOpen = (event: Event) => {
      const prompt = (event as CustomEvent<{ prompt?: string }>).detail?.prompt;
      setOpen(true);
      if (prompt) pendingPrompt.current = prompt;
    };
    window.addEventListener(OPEN_EVENT, onOpen);
    return () => window.removeEventListener(OPEN_EVENT, onOpen);
  }, []);

  // Send a prompt handed over by a page button once the panel is open and live.
  useEffect(() => {
    if (!open || !available || !pendingPrompt.current) return;
    const prompt = pendingPrompt.current;
    pendingPrompt.current = null;
    send(prompt);
  });

  useEffect(() => {
    if (!open) return;
    panelRef.current?.querySelector<HTMLTextAreaElement>("textarea")?.focus();
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") setOpen(false); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  function continueToApplication() {
    if (!lead) return;
    setOpen(false);
    onApply(lead);
  }

  const status = checking ? "standby" : available ? "online" : "offline";

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-4 right-4 z-[60] flex items-center gap-2 border border-hud/60 bg-[#0e1218]/95 px-3 py-2 sm:bottom-5 sm:right-5 sm:px-4 sm:py-3 font-['Chakra_Petch'] text-xs sm:text-sm font-semibold tracking-[0.2em] text-white shadow-[0_0_24px_rgb(56_198_255/0.25)] backdrop-blur hover:border-hud hover:shadow-[0_0_32px_rgb(56_198_255/0.45)] transition-shadow"
      >
        <span aria-hidden="true" className={`h-2 w-2 rounded-full ${available ? "bg-hud hud-pulse shadow-[0_0_8px_rgb(56_198_255)]" : "bg-[#4b5563]"}`} />
        ASK JAY
      </button>
    );
  }

  return (
    <div
      ref={panelRef}
      role="dialog"
      aria-label="Ask Jay"
      className="fixed inset-0 z-[60] flex flex-col bg-background sm:inset-auto sm:bottom-5 sm:right-5 sm:h-[min(620px,calc(100dvh-5rem))] sm:w-[400px] sm:bg-transparent"
    >
      <AgentModule code="MOD-07" name="ASK JAY" status={status} className="flex h-full flex-col" bodyClassName="flex min-h-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1 flex-col">
          <div className="flex items-start justify-between gap-3 px-4 pt-3 pb-2">
            <p className="font-['JetBrains_Mono'] text-[11px] leading-relaxed text-white/55">
              Jay is Coach Jay's AI assistant. Ask about coaching, get a starting plan, or start your application.
            </p>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close Ask Jay"
              className="min-h-9 min-w-9 shrink-0 font-['JetBrains_Mono'] text-xs text-white/60 hover:text-white"
            >
              ✕
            </button>
          </div>

          {available ? (
            <AIChatBox
              messages={messages}
              onSendMessage={send}
              isLoading={sendMut.isPending}
              placeholder="Ask Jay anything…"
              inputLabel="Message Ask Jay"
              emptyStateMessage="What are you working toward?"
              suggestedPrompts={SUGGESTED_PROMPTS}
              height="100%"
              reserveSpaceForReply={false}
              className="min-h-0 flex-1 rounded-none border-0 border-t border-white/[0.08] bg-transparent shadow-none"
              footer={
                <div className="space-y-2 px-4 pb-1 pt-2">
                  {failed && (
                    <p role="alert" className="font-['JetBrains_Mono'] text-xs text-destructive">
                      {failed.error}{" "}
                      <button type="button" onClick={() => send(failed.text)} className="underline">Try again</button>
                    </p>
                  )}
                  {lead && (
                    <button
                      type="button"
                      onClick={continueToApplication}
                      className="w-full bg-hud-deep py-3 font-['JetBrains_Mono'] text-xs tracking-widest text-white hover:bg-[#1f54e6] hover:shadow-[0_0_24px_rgb(56_198_255/0.45)] transition-colors"
                    >
                      CONTINUE MY APPLICATION →
                    </button>
                  )}
                  <p className="font-['JetBrains_Mono'] text-[10px] text-white/35">
                    AI assistant · answers can be wrong · we only save your details if you ask us to.
                  </p>
                </div>
              }
            />
          ) : (
            <div className="flex flex-1 flex-col justify-center gap-4 border-t border-white/[0.08] p-6 text-center">
              <div className="font-['Chakra_Petch'] text-xl font-semibold tracking-[0.15em] text-white">
                {checking ? "CONNECTING…" : "ASK JAY — COMING SOON"}
              </div>
              {!checking && (
                <>
                  <p className="font-['JetBrains_Mono'] text-xs text-white/55">
                    The assistant isn't switched on yet. You can still build a starting plan on this page or apply directly.
                  </p>
                  <a href="#ai-engine" onClick={() => setOpen(false)} className="border border-hud/50 py-3 font-['JetBrains_Mono'] text-xs tracking-widest text-hud hover:bg-hud/10">
                    BUILD A STARTING PLAN
                  </a>
                  <a href="#apply" onClick={() => setOpen(false)} className="bg-hud-deep py-3 font-['JetBrains_Mono'] text-xs tracking-widest text-white">
                    APPLY
                  </a>
                </>
              )}
            </div>
          )}
        </div>
      </AgentModule>
    </div>
  );
}
