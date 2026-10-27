import { useCallback, useEffect, useState, type FormEvent } from "react";
import { AgentModule } from "@/components/hud/AgentModule";
import { HudBackdrop } from "@/components/hud/HudBackdrop";

/**
 * The Neural HUD: Coach Jay's owner-only priority queue. Signal only: the
 * server ranks Airtable, Linear and Notion and mutes the noise. Read-only; it
 * proposes and never acts.
 */

type Signal = { id: string; source: string; kind: string; score: number; title: string; why: string; next: string; url?: string | null };
type SourceStatus = { source: string; label: string; connected: boolean; error?: string; count: number };
type Queue = {
  generated_at: string;
  do_now: Signal[];
  next: Signal[];
  more: number;
  muted: { reason: string; count: number }[];
  muted_total: number;
  sources: SourceStatus[];
};

type State = { phase: "loading" } | { phase: "signin"; error?: string } | { phase: "off" | "error"; error: string } | { phase: "ready"; queue: Queue };

const KIND: Record<string, { label: string; color: string }> = {
  money: { label: "MONEY", color: "text-[#ff5d6c] border-[#ff5d6c]" },
  lead: { label: "LEAD", color: "text-[#ffb547] border-[#ffb547]" },
  client: { label: "CLIENT", color: "text-hud border-hud" },
  task: { label: "TASK", color: "text-[#a5b4fc] border-[#a5b4fc]" },
  gate: { label: "APPROVAL", color: "text-[#4ade80] border-[#4ade80]" },
};

const mono = "font-['JetBrains_Mono']";
const head = "font-['Chakra_Petch'] font-semibold tracking-[0.2em]";
const display = "font-['Bebas_Neue']";

function Tag({ kind }: { kind: string }) {
  const k = KIND[kind] ?? KIND.task;
  return <span className={`${head} shrink-0 border px-1.5 py-1 text-[10px] ${k.color}`}>{k.label}</span>;
}

function SignalLink({ s }: { s: Signal }) {
  if (!s.url) return <span className="text-white/40">SRC · {s.source.toUpperCase()}</span>;
  return (
    <a href={s.url} target="_blank" rel="noreferrer" className="text-hud underline-offset-4 hover:underline">
      OPEN IN {s.source.toUpperCase()} →
    </a>
  );
}

export default function Brain() {
  const [state, setState] = useState<State>({ phase: "loading" });
  const [password, setPassword] = useState("");
  const [showMuted, setShowMuted] = useState(false);
  const [open, setOpen] = useState<string | null>(null);

  const load = useCallback(async () => {
    setState(s => (s.phase === "ready" ? s : { phase: "loading" }));
    try {
      const res = await fetch("/api/brain/queue", { credentials: "same-origin" });
      const body = await res.json().catch(() => ({}));
      if (res.status === 401) return setState({ phase: "signin" });
      if (res.status === 503) return setState({ phase: "off", error: body.error ?? "The Neural HUD is off." });
      if (!res.ok) return setState({ phase: "error", error: body.error ?? "The queue couldn't load." });
      setState({ phase: "ready", queue: body });
    } catch {
      setState({ phase: "error", error: "Can't reach the server. Check your connection and refresh." });
    }
  }, []);

  useEffect(() => {
    document.title = "Neural HUD · Everyday Hustle Co.";
    const robots = document.createElement("meta");
    robots.name = "robots";
    robots.content = "noindex, nofollow";
    document.head.appendChild(robots);
    void load();
    return () => robots.remove();
  }, [load]);

  async function signIn(e: FormEvent) {
    e.preventDefault();
    const res = await fetch("/api/brain/login", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });
    const body = await res.json().catch(() => ({}));
    setPassword("");
    if (!res.ok) return setState({ phase: "signin", error: body.error ?? "Sign-in failed." });
    await load();
  }

  async function signOut() {
    await fetch("/api/brain/logout", { method: "POST", credentials: "same-origin" });
    setState({ phase: "signin" });
  }

  const queue = state.phase === "ready" ? state.queue : null;
  const signalCount = queue ? queue.do_now.length + queue.next.length + queue.more : 0;

  return (
    <div className={`relative min-h-screen bg-[#05070b] text-white ${mono}`}>
      <HudBackdrop />
      <div className="relative z-10 mx-auto grid max-w-[1240px] gap-6 px-4 py-6 sm:px-6">
        <header className="flex flex-wrap items-end justify-between gap-4 border-b border-hud/20 pb-4">
          <div>
            <p className={`${head} text-[11px] text-hud`}>&gt; SIGNAL ONLY. NO NOISE.</p>
            <h1 className={`${display} mt-2 text-[clamp(40px,7vw,72px)] leading-[0.9] [text-shadow:0_0_24px_rgb(56_198_255/0.35)]`}>
              EVERYDAY HUSTLE CO. <span className="text-hud">//</span> NEURAL HUD
            </h1>
            <p className={`${head} mt-2 text-[12px] text-white/50`}>JAYLEE HUSTLE · COACH JAY · FITNESS</p>
          </div>
          {queue && (
            <div className="grid gap-2 text-right text-[12px] text-white/50">
              <span>
                Last scan <b className="font-medium text-white">{new Date(queue.generated_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}</b>
              </span>
              <span className="flex justify-end gap-2">
                <button onClick={() => void load()} className={`${head} border border-hud/40 px-2 py-1.5 text-[10px] text-white hover:bg-hud/10`}>RESCAN</button>
                <button onClick={() => void signOut()} className={`${head} border border-white/15 px-2 py-1.5 text-[10px] text-white/60 hover:bg-white/5`}>SIGN OUT</button>
              </span>
            </div>
          )}
        </header>

        {state.phase === "loading" && <p className="text-white/60">Scanning sources…</p>}

        {(state.phase === "off" || state.phase === "error") && (
          <AgentModule code="SYS/00" name="NEURAL HUD" status="offline" bodyClassName="p-5 text-white/70">
            {state.error}
          </AgentModule>
        )}

        {state.phase === "signin" && (
          <AgentModule code="AUTH/00" name="OWNER SIGN-IN" status="standby" label="LOCKED" className="max-w-md" bodyClassName="p-5">
            <form onSubmit={signIn} className="grid gap-3">
              <label htmlFor="brain-password" className={`${head} text-[11px] text-white/60`}>OWNER PASSWORD</label>
              <input
                id="brain-password"
                type="password"
                autoComplete="current-password"
                required
                autoFocus
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="border border-white/20 bg-[#05070b] p-3 text-white outline-none focus:border-hud"
              />
              {state.error && <p role="alert" className="text-[13px] text-[#ff6b6b]">{state.error}</p>}
              <button type="submit" className={`${head} bg-hud p-3 text-[12px] text-[#05070b] hover:brightness-110`}>UNLOCK</button>
              <p className="text-[12px] text-white/40">Same password as your Claude connector. You stay signed in for 12 hours on this device.</p>
            </form>
          </AgentModule>
        )}

        {queue && (
          <div className="grid items-start gap-5 lg:grid-cols-[300px_minmax(0,1fr)]">
            <aside className="grid gap-5">
              <AgentModule code="CORE/01" name="SIGNAL" status="online" label="LIVE" bodyClassName="p-5 grid gap-4">
                <div className="grid place-items-center">
                  <div className="grid aspect-square w-44 place-content-center rounded-full border border-hud/40 text-center shadow-[0_0_40px_rgb(56_198_255/0.15)_inset]">
                    <span className={`${display} text-6xl leading-none [text-shadow:0_0_20px_rgb(56_198_255/0.6)]`}>{signalCount}</span>
                    <span className={`${head} text-[10px] text-hud`}>SIGNALS</span>
                  </div>
                </div>
                <div className="flex justify-between text-[12px] tabular-nums text-white/50">
                  <span>Signal <b className="font-medium text-white">{signalCount}</b></span>
                  <span>Muted <b className="font-medium text-white">{queue.muted_total}</b></span>
                </div>
              </AgentModule>

              <AgentModule code="SRC/02" name="INPUTS" status="online" label={`${queue.sources.filter(s => s.connected && !s.error).length}/${queue.sources.length}`} bodyClassName="p-4 grid gap-3 text-[12px]">
                {queue.sources.map(s => (
                  <div key={s.source} className="grid grid-cols-[10px_1fr] items-start gap-3">
                    <span className={`mt-1.5 h-2 w-2 rounded-full ${s.connected && !s.error ? "bg-[#4ade80] shadow-[0_0_8px_#4ade80]" : s.error && s.connected ? "bg-[#ff5d6c]" : "bg-white/25"}`} />
                    <span className="min-w-0">
                      {s.label}
                      {s.error && <span className="block text-[11px] text-white/40">{s.error}</span>}
                    </span>
                  </div>
                ))}
                <p className="border-t border-hud/15 pt-3 text-[11px] text-white/40">
                  Calendar, Gmail and Drive are merged in Claude: ask it for your daily brief.
                </p>
              </AgentModule>

              <AgentModule code="LAW/03" name="GATES" status="standby" label="READ-ONLY" bodyClassName="p-4 grid gap-2 text-[12px] text-white/50">
                <b className="font-medium text-white">The brain proposes. Jordan approves.</b>
                <span>It never sends, publishes, charges or approves anything.</span>
              </AgentModule>
            </aside>

            <main className="grid min-w-0 gap-6">
              <section aria-labelledby="now-h">
                <div className="mb-3 flex items-baseline justify-between gap-3">
                  <h2 id="now-h" className={`${display} text-3xl tracking-wide`}>DO NOW</h2>
                  <small className={`${head} text-[10px] text-white/40`}>TOP 3</small>
                </div>
                {queue.do_now.length === 0 && !queue.sources.some(s => s.connected && !s.error) ? (
                  <AgentModule code="Q/00" name="NO INPUT" status="offline" label="BLIND" bodyClassName="p-5 text-white/60">
                    No sources are connected yet, so there's nothing to rank. Add the keys listed under Inputs in Railway.
                  </AgentModule>
                ) : queue.do_now.length === 0 ? (
                  <AgentModule code="Q/00" name="CLEAR" status="online" label="ALL CLEAR" bodyClassName="p-5 text-white/60">
                    Nothing needs you right now. Go train.
                  </AgentModule>
                ) : (
                  <div className="grid gap-4 xl:grid-cols-3">
                    {queue.do_now.map((s, i) => (
                      <AgentModule key={s.id} code={`NOW/0${i + 1}`} name={s.source.toUpperCase()} status="online" label={String(s.score)} bodyClassName="p-4 grid gap-3">
                        <div className="flex items-center justify-between gap-2">
                          <span className={`${display} text-4xl leading-none tabular-nums`}>{s.score}</span>
                          <Tag kind={s.kind} />
                        </div>
                        <div className="h-[3px] bg-white/5"><div className="h-full bg-hud shadow-[0_0_10px_#38c6ff]" style={{ width: `${s.score}%` }} /></div>
                        <h3 className="font-['Chakra_Petch'] text-[16px] font-semibold leading-snug [text-wrap:balance]">{s.title}</h3>
                        <p className="text-[12px] text-white/50">{s.why}</p>
                        <div className="grid gap-1 border-t border-dashed border-hud/25 pt-3 text-[12px]">
                          <span className={`${head} text-[10px] text-hud`}>NEXT MOVE</span>
                          {s.next}
                        </div>
                        <span className="text-[11px]"><SignalLink s={s} /></span>
                      </AgentModule>
                    ))}
                  </div>
                )}
              </section>

              {queue.next.length > 0 && (
                <AgentModule code="Q/04" name="NEXT" status="standby" label={queue.more ? `+${queue.more} MORE` : "TAP FOR WHY"}>
                  <ul>
                    {queue.next.map(s => (
                      <li key={s.id} className="border-b border-hud/15 last:border-0">
                        <button
                          onClick={() => setOpen(open === s.id ? null : s.id)}
                          aria-expanded={open === s.id}
                          className="grid w-full grid-cols-[48px_minmax(0,1fr)_auto] items-center gap-3 px-4 py-3 text-left hover:bg-white/[0.03] focus-visible:outline focus-visible:outline-2 focus-visible:outline-hud"
                        >
                          <span className={`${display} text-3xl leading-none tabular-nums`}>{s.score}</span>
                          <span className="font-['Chakra_Petch'] text-[14px] font-semibold">{s.title}</span>
                          <Tag kind={s.kind} />
                        </button>
                        {open === s.id && (
                          <div className="grid gap-1 px-4 pb-3 pl-[76px] text-[12px] text-white/50">
                            <span>{s.why}</span>
                            <span><b className="font-medium text-white">Next:</b> {s.next}</span>
                            <SignalLink s={s} />
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                </AgentModule>
              )}

              <AgentModule code="NZ/05" name="MUTED NOISE" status="offline" label={`${queue.muted_total} HIDDEN`} bodyClassName="p-4 grid gap-3">
                {queue.muted_total === 0 ? (
                  <p className="text-[12px] text-white/50">No noise this scan.</p>
                ) : (
                  <>
                    <button
                      onClick={() => setShowMuted(v => !v)}
                      aria-expanded={showMuted}
                      className={`${head} justify-self-start border border-hud/20 px-2.5 py-2 text-[10px] text-white/50 hover:text-white`}
                    >
                      {showMuted ? "HIDE REASONS" : "SHOW WHY THEY WERE MUTED"}
                    </button>
                    {showMuted && (
                      <ul className="grid gap-1.5 text-[12px] text-white/50">
                        {queue.muted.map(m => (
                          <li key={m.reason} className="flex justify-between gap-3 border-b border-dotted border-hud/20 pb-1.5">
                            <span>{m.reason}</span>
                            <b className="font-medium tabular-nums text-white">{m.count}</b>
                          </li>
                        ))}
                      </ul>
                    )}
                  </>
                )}
              </AgentModule>
            </main>
          </div>
        )}

        <footer className="flex flex-wrap justify-between gap-2 border-t border-hud/15 pt-3 text-[11px] tracking-wider text-white/40">
          <span>EVERYDAY HUSTLE CO. · JAYLEE HUSTLE INDUSTRIES LLC</span>
          <span>Owner only. Not linked from the public site.</span>
        </footer>
      </div>
    </div>
  );
}
