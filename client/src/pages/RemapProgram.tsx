import { useState } from "react";
import { useParams } from "wouter";
import { trpc } from "@/lib/trpc";
import { AgentModule } from "@/components/hud/AgentModule";
import { HudBackdrop } from "@/components/hud/HudBackdrop";
import { HudReticle } from "@/components/hud/HudReticle";
import { GOALS } from "@shared/remap";
import type { RemapProgram as Program } from "@shared/remapProgram";

const BUILDING = new Set(["Awaiting payment", "Paid", "Generating"]);

/** A buyer's private Remap page: waits for payment and the build, then shows the program. */
export default function RemapProgram() {
  const { token = "" } = useParams<{ token: string }>();
  const sessionId = new URLSearchParams(window.location.search).get("session_id") ?? undefined;
  const status = trpc.remap.status.useQuery(
    { token, sessionId },
    {
      retry: false,
      refetchInterval: query => (query.state.data && BUILDING.has(query.state.data.status) ? 3000 : false),
    },
  );
  const data = status.data;

  return (
    <div className="bg-background text-white min-h-screen print:bg-white print:text-black">
      <div className="print:hidden"><HudBackdrop /></div>
      <header className="relative z-10 border-b border-hud/20 print:hidden">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <a href="/" className="flex items-center gap-2 font-['Chakra_Petch'] font-semibold text-base tracking-[0.25em] text-white">
            <span aria-hidden="true" className="h-2 w-2 rotate-45 border border-hud bg-hud/30" />JAYLEE FIT
          </a>
          <span className="font-['JetBrains_Mono'] text-[10px] tracking-widest text-hud">REMAP // PRIVATE</span>
        </div>
      </header>

      <main className="relative z-10 max-w-5xl mx-auto px-4 py-10">
        {status.isPending && <Waiting title="LOADING YOUR REMAP…" />}
        {status.error && (
          <Message title="LINK NOT FOUND" body="We couldn't find a Remap at this link. Check that you copied the whole link, or email Jay.everydayhustleco@gmail.com with the email you paid with." />
        )}
        {data?.status === "Awaiting payment" && (
          <Waiting title="CONFIRMING PAYMENT…" body="This usually takes a few seconds after checkout. If you closed checkout before paying, you can start again from the Remap page." />
        )}
        {(data?.status === "Paid" || data?.status === "Generating") && (
          <Waiting
            title={`BUILDING YOUR REMAP, ${data.firstName.toUpperCase()}`}
            body="Your numbers are locked in and your program is being written now. This usually takes 1–3 minutes. Keep this page open, or bookmark it and come back."
          />
        )}
        {data?.status === "Failed" && (
          <Message title="WE HIT A SNAG" body="Your payment went through, but your program didn't finish building. Coach Jay has the details and will get it to you. You can also reload this page in a few minutes." />
        )}
        {data?.status === "Ready" && data.program && data.numbers && (
          <ProgramView program={data.program} numbers={data.numbers} firstName={data.firstName} goal={data.goal} units={data.units} />
        )}
      </main>
    </div>
  );
}

function Waiting({ title, body }: { title: string; body?: string }) {
  return (
    <div className="grid md:grid-cols-[1fr_280px] gap-8 items-center py-10" aria-live="polite">
      <div>
        <div className="font-['Chakra_Petch'] font-semibold text-2xl md:text-3xl tracking-[0.12em] text-white">{title}</div>
        {body && <p className="font-['JetBrains_Mono'] text-sm text-white/65 leading-relaxed mt-4 max-w-xl">{body}</p>}
      </div>
      <div className="w-[260px] max-w-full justify-self-center [&_div_div]:hidden"><HudReticle /></div>
    </div>
  );
}

function Message({ title, body }: { title: string; body: string }) {
  return (
    <div className="border border-white/15 p-6 max-w-2xl" role="alert">
      <div className="font-['Chakra_Petch'] font-semibold text-xl tracking-[0.12em] text-white mb-3">{title}</div>
      <p className="font-['JetBrains_Mono'] text-sm text-white/65 leading-relaxed">{body}</p>
    </div>
  );
}

type Numbers = { bmr: number; activityFactor: number; tdee: number; targetCalories: number; proteinG: number; fatG: number; carbsG: number };

function ProgramView({ program, numbers, firstName, goal, units }: {
  program: Program;
  numbers: Numbers;
  firstName: string;
  goal: keyof typeof GOALS;
  units: "imperial" | "metric";
}) {
  const [copied, setCopied] = useState(false);
  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.origin + window.location.pathname);
      setCopied(true);
    } catch {}
  };

  return (
    <article className="space-y-8">
      <div>
        <div className="font-['JetBrains_Mono'] text-[11px] tracking-widest text-hud print:text-black">{`REMAP // ${firstName.toUpperCase()} // ${program.weeks} WEEKS // ${GOALS[goal].label.toUpperCase()}`}</div>
        <h1 className="font-['Chakra_Petch'] font-semibold text-3xl md:text-5xl tracking-[0.08em] text-white mt-2 hud-glow print:text-black print:[text-shadow:none]">{program.title}</h1>
        <p className="font-['JetBrains_Mono'] text-sm text-white/75 leading-relaxed mt-4 max-w-3xl print:text-black">{program.summary}</p>
        <div className="flex flex-wrap gap-3 mt-5 print:hidden">
          <button type="button" onClick={() => window.print()} className="px-5 py-2.5 bg-hud-deep text-white font-['JetBrains_Mono'] text-xs tracking-widest hover:bg-[#1f54e6]">SAVE AS PDF</button>
          <button type="button" onClick={copyLink} className="px-5 py-2.5 border border-hud/50 text-hud font-['JetBrains_Mono'] text-xs tracking-widest hover:bg-hud/10">{copied ? "LINK COPIED" : "COPY MY LINK"}</button>
          <span className="self-center font-['JetBrains_Mono'] text-[11px] text-white/45">Bookmark this page: the link is your access.</span>
        </div>
      </div>

      <AgentModule code="R-01" name="YOUR NUMBERS" status="online" label="LOCKED IN">
        <div className="p-5 grid grid-cols-2 md:grid-cols-4 gap-4">
          <Stat label="BMR" value={`${numbers.bmr.toLocaleString()}`} unit="kcal at rest" />
          <Stat label="ACTIVITY" value={`×${numbers.activityFactor}`} unit="multiplier" />
          <Stat label="DAILY BURN" value={`${numbers.tdee.toLocaleString()}`} unit="kcal (TDEE)" />
          <Stat label="TARGET" value={`${numbers.targetCalories.toLocaleString()}`} unit="kcal / day" highlight />
          <Stat label="PROTEIN" value={`${numbers.proteinG} g`} unit={`${numbers.proteinG * 4} kcal`} highlight />
          <Stat label="CARBS" value={`${numbers.carbsG} g`} unit={`${numbers.carbsG * 4} kcal`} highlight />
          <Stat label="FAT" value={`${numbers.fatG} g`} unit={`${numbers.fatG * 9} kcal`} highlight />
          <Stat label="LENGTH" value={`${program.weeks} wk`} unit={program.phases.length + " phases"} />
        </div>
        <p className="px-5 pb-5 font-['JetBrains_Mono'] text-[11px] text-white/50 leading-relaxed print:text-black">{program.lengthRationale}</p>
      </AgentModule>

      <Block title="WARM-UP">{program.warmup}</Block>

      {program.phases.map((phase, i) => (
        <AgentModule key={phase.name} code={`P-${String(i + 1).padStart(2, "0")}`} name={phase.name.toUpperCase()} status="online" label={`WEEKS ${phase.startWeek}–${phase.endWeek}`}>
          <div className="p-5 space-y-5 break-inside-avoid-page">
            <p className="font-['JetBrains_Mono'] text-sm text-white/75 leading-relaxed print:text-black">{phase.goal}</p>
            {phase.days.map(day => (
              <div key={day.label} className="border border-white/10 print:border-black/30">
                <div className="flex flex-wrap items-baseline justify-between gap-2 px-4 py-2 bg-white/[0.03] border-b border-white/10 print:border-black/30">
                  <div className="font-['Chakra_Petch'] font-semibold tracking-[0.1em] text-white print:text-black">{day.label} · {day.title}</div>
                  <div className="font-['JetBrains_Mono'] text-[11px] text-white/50 print:text-black">{day.focus}</div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[640px] text-left">
                    <thead>
                      <tr className="font-['JetBrains_Mono'] text-[10px] tracking-widest text-white/45 print:text-black">
                        {["EXERCISE", "SETS", "REPS", "REST", "EFFORT", "NOTES"].map(h => <th key={h} className="px-4 py-2 font-normal">{h}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {day.exercises.map((ex, j) => (
                        <tr key={j} className="border-t border-white/5 font-['JetBrains_Mono'] text-xs text-white/80 align-top print:text-black">
                          <td className="px-4 py-2 text-white print:text-black">{ex.name}</td>
                          <td className="px-4 py-2">{ex.sets}</td>
                          <td className="px-4 py-2">{ex.reps}</td>
                          <td className="px-4 py-2">{ex.rest}</td>
                          <td className="px-4 py-2">{ex.effort}</td>
                          <td className="px-4 py-2 text-white/55 print:text-black">{ex.notes}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {day.finisher && <p className="px-4 py-2 border-t border-white/5 font-['JetBrains_Mono'] text-[11px] text-white/60 print:text-black"><span className="text-hud print:text-black">FINISHER // </span>{day.finisher}</p>}
              </div>
            ))}
            <p className="font-['JetBrains_Mono'] text-xs text-white/70 leading-relaxed print:text-black"><span className="text-hud print:text-black">PROGRESSION // </span>{phase.progression}</p>
          </div>
        </AgentModule>
      ))}

      <div className="grid md:grid-cols-2 gap-6">
        <Block title="DELOAD">{program.deload}</Block>
        <Block title="CARDIO & STEPS">{program.cardioAndSteps}</Block>
      </div>

      <AgentModule code="R-02" name="NUTRITION" status="online" label="TARGETS ABOVE">
        <div className="p-5 space-y-4 font-['JetBrains_Mono'] text-sm text-white/75 leading-relaxed print:text-black">
          <p>{program.nutrition.summary}</p>
          <List title="BUILD MEALS AROUND" items={program.nutrition.priorities} />
          <List title="PROTEIN" items={program.nutrition.proteinTips} />
          <p><span className="text-hud print:text-black">TIMING // </span>{program.nutrition.timing}</p>
          <p><span className="text-hud print:text-black">ADJUSTING // </span>{program.nutrition.adjustments}</p>
          <p className="text-[11px] text-white/45 print:text-black">Weigh in daily if you can and watch the 7-day average{units === "imperial" ? " in pounds" : ""}, not single days.</p>
        </div>
      </AgentModule>

      <div className="grid md:grid-cols-2 gap-6">
        <Block title="HABITS"><ul className="space-y-1.5">{program.habits.map(h => <li key={h}>▸ {h}</li>)}</ul></Block>
        <Block title="WEEKLY CHECK-IN">{program.checkIns}</Block>
      </div>

      <Block title="SAFETY"><ul className="space-y-1.5">{program.safety.map(s => <li key={s}>▸ {s}</li>)}</ul></Block>

      <p className="font-['JetBrains_Mono'] text-[11px] text-white/40 leading-relaxed print:text-black">
        General fitness guidance built for you by JayLee Fit's AI coach from your answers, not medical advice. Want Coach Jay reviewing your progress and adjusting this with you? Apply for 1:1 coaching at jayleefit.com.
      </p>
    </article>
  );
}

function Stat({ label, value, unit, highlight }: { label: string; value: string; unit: string; highlight?: boolean }) {
  return (
    <div className={`border p-3 ${highlight ? "border-hud/40 bg-hud/5" : "border-white/10"} print:border-black/30`}>
      <div className="font-['JetBrains_Mono'] text-[10px] tracking-widest text-white/50 print:text-black">{label}</div>
      <div className={`font-['Chakra_Petch'] font-semibold text-2xl tabular-nums ${highlight ? "text-hud" : "text-white"} print:text-black`}>{value}</div>
      <div className="font-['JetBrains_Mono'] text-[10px] text-white/40 print:text-black">{unit}</div>
    </div>
  );
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="border border-white/10 p-5 print:border-black/30 break-inside-avoid-page">
      <h2 className="font-['Chakra_Petch'] font-semibold text-sm tracking-[0.2em] text-hud mb-3 print:text-black">{title}</h2>
      <div className="font-['JetBrains_Mono'] text-sm text-white/75 leading-relaxed print:text-black">{children}</div>
    </section>
  );
}

function List({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <div className="text-hud text-xs tracking-widest mb-1 print:text-black">{title}</div>
      <ul className="space-y-1">{items.map(i => <li key={i}>▸ {i}</li>)}</ul>
    </div>
  );
}
