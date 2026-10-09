import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import { trpc } from "@/lib/trpc";
import { AgentModule } from "@/components/hud/AgentModule";
import { AskJay } from "@/components/hud/AskJay";
import { HudBackdrop } from "@/components/hud/HudBackdrop";
import { captureRef, takeRemapPrefill, visitRef } from "@/lib/visit";
import { REMAP } from "@shared/maoContent";
import {
  ACTIVITY_LEVELS,
  GOALS,
  PROGRAM_WEEKS,
  basalMetabolicRate,
  inchesToCm,
  lbToKg,
  type ActivityLevel,
  type Experience,
  type Goal,
  type Sex,
} from "@shared/remap";

type Units = "imperial" | "metric";
type Equipment = "full-gym" | "home-gym" | "dumbbells-bands" | "bodyweight";

const EXPERIENCE: Record<Experience, string> = {
  beginner: "Beginner — under 1 year of consistent lifting",
  intermediate: "Intermediate — 1–3 years, know the main lifts",
  advanced: "Advanced — 3+ years, programmed training",
};

const EQUIPMENT: Record<Equipment, string> = {
  "full-gym": "Full gym",
  "home-gym": "Home gym (rack, barbell, bench, dumbbells)",
  "dumbbells-bands": "Dumbbells and bands",
  bodyweight: "Bodyweight only",
};

const inputCls = "w-full min-h-11 bg-white/5 border border-white/25 text-white font-['JetBrains_Mono'] text-sm px-3 py-2 focus:outline-none focus:border-hud transition-colors placeholder:text-white/30";
const labelCls = "block font-['JetBrains_Mono'] text-xs tracking-widest text-white/65 mb-1.5";

const num = (value: string) => (value.trim() === "" ? NaN : Number(value));

export default function Remap() {
  const offer = trpc.remap.offer.useQuery();
  const capabilities = trpc.site.capabilities.useQuery();
  const checkout = trpc.remap.checkout.useMutation({
    onSuccess: ({ url }) => window.location.assign(url),
  });

  const [units, setUnits] = useState<Units>("imperial");
  const [form, setForm] = useState({
    name: "", email: "", sex: "male" as Sex, age: "",
    heightFt: "", heightIn: "", heightCm: "",
    weight: "", goalWeight: "",
    goal: "fat-loss" as Goal, experience: "beginner" as Experience, activity: "light" as ActivityLevel,
    daysPerWeek: "4", sessionMinutes: "60", equipment: "full-gym" as Equipment,
    injuries: "", foodNotes: "", notes: "",
  });
  const set = <K extends keyof typeof form>(key: K, value: (typeof form)[K]) => setForm(f => ({ ...f, [key]: value }));
  const canceled = new URLSearchParams(window.location.search).get("canceled") === "1";

  useEffect(() => {
    captureRef();
    const prefill = takeRemapPrefill();
    if (prefill) {
      setForm(f => ({
        ...f,
        name: f.name || prefill.name || "",
        email: f.email || prefill.email || "",
        notes: f.notes || (prefill.goalNote ? `From my chat with Jay: ${prefill.goalNote}` : ""),
      }));
    }
  }, []);

  // Metric values for the calculator and the order.
  const heightCm = units === "imperial" ? inchesToCm(num(form.heightFt) * 12 + (num(form.heightIn) || 0)) : num(form.heightCm);
  const weightKg = units === "imperial" ? lbToKg(num(form.weight)) : num(form.weight);
  const goalWeightKg = form.goalWeight.trim() ? (units === "imperial" ? lbToKg(num(form.goalWeight)) : num(form.goalWeight)) : undefined;
  const age = num(form.age);

  const preview = useMemo(() => {
    if (![heightCm, weightKg, age].every(Number.isFinite) || heightCm < 120 || weightKg < 35 || age < 16) return null;
    const bmr = basalMetabolicRate({ sex: form.sex, age, heightCm, weightKg });
    const factor = ACTIVITY_LEVELS[form.activity].factor;
    return { bmr: Math.round(bmr), factor, tdee: Math.round(bmr * factor) };
  }, [heightCm, weightKg, age, form.sex, form.activity]);

  const weeks = PROGRAM_WEEKS[form.experience];
  const price = offer.data?.priceCents ? `$${(offer.data.priceCents / 100).toFixed(offer.data.priceCents % 100 ? 2 : 0)}` : null;
  const open = offer.data?.available === true;

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!open) return;
    checkout.mutate({
      name: form.name,
      email: form.email,
      sex: form.sex,
      age,
      heightCm: Math.round(heightCm * 10) / 10,
      weightKg: Math.round(weightKg * 10) / 10,
      goalWeightKg: goalWeightKg !== undefined && Number.isFinite(goalWeightKg) ? Math.round(goalWeightKg * 10) / 10 : undefined,
      units,
      goal: form.goal,
      experience: form.experience,
      activity: form.activity,
      daysPerWeek: Number(form.daysPerWeek),
      sessionMinutes: Number(form.sessionMinutes),
      equipment: form.equipment,
      injuries: form.injuries,
      foodNotes: form.foodNotes,
      notes: form.notes,
      source: visitRef(),
    });
  }

  return (
    <div className="bg-background text-white min-h-screen">
      <HudBackdrop />
      <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-hud/20">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <a href="/" className="flex items-center gap-2 font-['Chakra_Petch'] font-semibold text-base tracking-[0.25em] text-white">
            <span aria-hidden="true" className="h-2 w-2 rotate-45 border border-hud bg-hud/30" />JAYLEE FIT
          </a>
          <a href="/#investment" className="font-['JetBrains_Mono'] text-[10px] tracking-widest text-white/60 hover:text-white">COACHING PACKAGES</a>
        </div>
      </header>

      <main className="relative z-10 max-w-6xl mx-auto px-4 pt-24 pb-24">
        <div className="mb-10 max-w-3xl">
          <div className="font-['JetBrains_Mono'] text-[11px] tracking-widest text-hud mb-3">{"> REMAP // PERSONAL PROGRAM"}</div>
          <h1 className="font-['Chakra_Petch'] font-semibold text-4xl md:text-6xl tracking-[0.12em] text-white hud-glow">REMAP</h1>
          <p className="font-['JetBrains_Mono'] text-sm text-white/70 leading-relaxed mt-4">{REMAP.tagline} {REMAP.desc}</p>
        </div>

        {canceled && (
          <p className="mb-6 border border-white/20 p-4 font-['JetBrains_Mono'] text-xs text-white/70">Checkout was canceled, and you weren't charged. Your answers are still here.</p>
        )}

        <form onSubmit={submit} className="grid lg:grid-cols-[1.25fr_0.75fr] gap-8 items-start">
          <AgentModule code="MOD-R1" name="INTAKE" status={open ? "online" : offer.isPending ? "standby" : "offline"} label={open ? "OPEN" : offer.isPending ? "STANDBY" : "OPENING SOON"}>
            <div className="p-5 md:p-6 space-y-8">
              <Group title="ABOUT YOU">
                <Field label="NAME *" id="r-name"><input id="r-name" required className={inputCls} value={form.name} onChange={e => set("name", e.target.value)} autoComplete="name" /></Field>
                <Field label="EMAIL *" id="r-email" hint="Your receipt goes here; your program link shows right after checkout.">
                  <input id="r-email" type="email" required className={inputCls} value={form.email} onChange={e => set("email", e.target.value)} autoComplete="email" />
                </Field>
                <div className="grid grid-cols-2 gap-4">
                  <Field label="SEX *" id="r-sex">
                    <select id="r-sex" className={inputCls} value={form.sex} onChange={e => set("sex", e.target.value as Sex)}>
                      <option value="male">Male</option><option value="female">Female</option><option value="unspecified">Prefer not to say</option>
                    </select>
                  </Field>
                  <Field label="AGE *" id="r-age"><input id="r-age" type="number" inputMode="numeric" min={16} max={90} required className={inputCls} value={form.age} onChange={e => set("age", e.target.value)} /></Field>
                </div>
              </Group>

              <Group title="BODY" action={
                <div role="group" aria-label="Units" className="flex border border-white/20">
                  {(["imperial", "metric"] as Units[]).map(u => (
                    <button key={u} type="button" onClick={() => setUnits(u)} aria-pressed={units === u}
                      className={`px-3 py-1 font-['JetBrains_Mono'] text-[10px] tracking-widest ${units === u ? "bg-hud/20 text-hud" : "text-white/50"}`}>
                      {u === "imperial" ? "LB / FT" : "KG / CM"}
                    </button>
                  ))}
                </div>
              }>
                {units === "imperial" ? (
                  <div className="grid grid-cols-2 gap-4">
                    <Field label="HEIGHT (FT) *" id="r-ft"><input id="r-ft" type="number" inputMode="numeric" min={4} max={7} required className={inputCls} value={form.heightFt} onChange={e => set("heightFt", e.target.value)} /></Field>
                    <Field label="HEIGHT (IN)" id="r-in"><input id="r-in" type="number" inputMode="numeric" min={0} max={11} className={inputCls} value={form.heightIn} onChange={e => set("heightIn", e.target.value)} /></Field>
                  </div>
                ) : (
                  <Field label="HEIGHT (CM) *" id="r-cm"><input id="r-cm" type="number" inputMode="decimal" min={120} max={230} required className={inputCls} value={form.heightCm} onChange={e => set("heightCm", e.target.value)} /></Field>
                )}
                <div className="grid grid-cols-2 gap-4">
                  <Field label={`WEIGHT (${units === "imperial" ? "LB" : "KG"}) *`} id="r-weight"><input id="r-weight" type="number" inputMode="decimal" required className={inputCls} value={form.weight} onChange={e => set("weight", e.target.value)} /></Field>
                  <Field label={`GOAL WEIGHT (${units === "imperial" ? "LB" : "KG"})`} id="r-goalweight"><input id="r-goalweight" type="number" inputMode="decimal" className={inputCls} value={form.goalWeight} onChange={e => set("goalWeight", e.target.value)} placeholder="Optional" /></Field>
                </div>
                <Field label="DAILY ACTIVITY (OUTSIDE WORKOUTS COUNTS) *" id="r-activity" hint={`${ACTIVITY_LEVELS[form.activity].detail}. Multiplier ×${ACTIVITY_LEVELS[form.activity].factor}.`}>
                  <select id="r-activity" className={inputCls} value={form.activity} onChange={e => set("activity", e.target.value as ActivityLevel)}>
                    {Object.entries(ACTIVITY_LEVELS).map(([key, a]) => <option key={key} value={key}>{a.label} (×{a.factor})</option>)}
                  </select>
                </Field>
              </Group>

              <Group title="TRAINING">
                <Field label="GOAL *" id="r-goal">
                  <select id="r-goal" className={inputCls} value={form.goal} onChange={e => set("goal", e.target.value as Goal)}>
                    {Object.entries(GOALS).map(([key, g]) => <option key={key} value={key}>{g.label}</option>)}
                  </select>
                </Field>
                <Field label="EXPERIENCE *" id="r-exp" hint={`Your Remap runs ${weeks.min}–${weeks.max} weeks at this level.`}>
                  <select id="r-exp" className={inputCls} value={form.experience} onChange={e => set("experience", e.target.value as Experience)}>
                    {Object.entries(EXPERIENCE).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
                  </select>
                </Field>
                <div className="grid grid-cols-2 gap-4">
                  <Field label="DAYS / WEEK *" id="r-days">
                    <select id="r-days" className={inputCls} value={form.daysPerWeek} onChange={e => set("daysPerWeek", e.target.value)}>
                      {[2, 3, 4, 5, 6].map(d => <option key={d} value={d}>{d} days</option>)}
                    </select>
                  </Field>
                  <Field label="MINUTES / SESSION *" id="r-mins">
                    <select id="r-mins" className={inputCls} value={form.sessionMinutes} onChange={e => set("sessionMinutes", e.target.value)}>
                      {[30, 45, 60, 75, 90].map(m => <option key={m} value={m}>{m} min</option>)}
                    </select>
                  </Field>
                </div>
                <Field label="EQUIPMENT *" id="r-equip">
                  <select id="r-equip" className={inputCls} value={form.equipment} onChange={e => set("equipment", e.target.value as Equipment)}>
                    {Object.entries(EQUIPMENT).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
                  </select>
                </Field>
                <Field label="INJURIES OR LIMITS" id="r-inj"><textarea id="r-inj" maxLength={600} className={`${inputCls} h-20 resize-none`} value={form.injuries} onChange={e => set("injuries", e.target.value)} placeholder="e.g. left shoulder impingement, no running" /></Field>
                <Field label="FOOD PREFERENCES OR RESTRICTIONS" id="r-food"><textarea id="r-food" maxLength={600} className={`${inputCls} h-20 resize-none`} value={form.foodNotes} onChange={e => set("foodNotes", e.target.value)} placeholder="e.g. vegetarian, no dairy, eat out a lot" /></Field>
                <Field label="ANYTHING ELSE COACH JAY SHOULD KNOW" id="r-notes"><textarea id="r-notes" maxLength={1000} className={`${inputCls} h-20 resize-none`} value={form.notes} onChange={e => set("notes", e.target.value)} /></Field>
              </Group>
            </div>
          </AgentModule>

          <div className="lg:sticky lg:top-20 space-y-6">
            <AgentModule code="MOD-R2" name="METABOLIC READOUT" status={preview ? "online" : "standby"} label={preview ? "LIVE" : "WAITING FOR STATS"}>
              <div className="p-5 space-y-4" aria-live="polite">
                <Readout label="BMR (MIFFLIN-ST JEOR)" value={preview ? `${preview.bmr.toLocaleString()} kcal` : "—"} note="What your body burns at rest." />
                <Readout label="ACTIVITY MULTIPLIER" value={`×${ACTIVITY_LEVELS[form.activity].factor}`} note={ACTIVITY_LEVELS[form.activity].label} />
                <Readout label="DAILY BURN (TDEE)" value={preview ? `${preview.tdee.toLocaleString()} kcal` : "—"} note="BMR × activity." />
                <div className="border border-hud/30 bg-hud/5 p-3 font-['JetBrains_Mono'] text-[11px] text-white/70 leading-relaxed">
                  <span className="text-hud">LOCKED // </span>Your calorie target and protein, carb and fat grams unlock with your Remap, along with the full {weeks.min}–{weeks.max} week program.
                </div>
              </div>
            </AgentModule>

            <AgentModule code="MOD-R3" name="CHECKOUT" status={open ? "online" : "offline"} label={open ? "SECURE · STRIPE" : "OPENING SOON"}>
              <div className="p-5 space-y-4">
                <ul className="space-y-1.5">
                  {REMAP.features.map(f => (
                    <li key={f} className="flex gap-2 font-['JetBrains_Mono'] text-[11px] text-white/70"><span className="text-hud">▸</span>{f}</li>
                  ))}
                </ul>
                {checkout.error && <p role="alert" className="font-['JetBrains_Mono'] text-xs text-destructive">{checkout.error.message}</p>}
                <button type="submit" disabled={!open || checkout.isPending}
                  className="w-full py-4 bg-hud-deep text-white font-['JetBrains_Mono'] text-sm tracking-widest shadow-[0_0_18px_rgb(37_99_255/0.35)] hover:bg-[#1f54e6] hover:shadow-[0_0_28px_rgb(56_198_255/0.55)] transition-[background-color,box-shadow] disabled:opacity-50">
                  {checkout.isPending ? "OPENING CHECKOUT…" : open ? `BUY MY REMAP${price ? ` — ${price}` : ""} →` : "CHECKOUT OPENS SOON"}
                </button>
                <p className="font-['JetBrains_Mono'] text-[10px] text-white/40 leading-relaxed">
                  One-time payment through Stripe. Your program is built right after checkout, usually in 1–3 minutes, on a private page you can save as a PDF. General fitness guidance, not medical advice.
                </p>
              </div>
            </AgentModule>
          </div>
        </form>
      </main>

      <AskJay available={capabilities.data?.aiChat === true} checking={capabilities.isPending} onApply={() => window.location.assign("/#apply")} />
    </div>
  );
}

function Group({ title, action, children }: { title: string; action?: ReactNode; children: ReactNode }) {
  return (
    <fieldset className="space-y-4">
      <legend className="mb-4 flex w-full items-center justify-between gap-3 font-['Chakra_Petch'] font-semibold text-sm tracking-[0.2em] text-hud">
        <span>{title}</span>
        {action}
      </legend>
      {children}
    </fieldset>
  );
}

function Field({ label, id, hint, children }: { label: string; id: string; hint?: string; children: ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className={labelCls}>{label}</label>
      {children}
      {hint && <p className="font-['JetBrains_Mono'] text-[11px] text-white/40 mt-1">{hint}</p>}
    </div>
  );
}

function Readout({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-white/10 pb-3">
      <div>
        <div className="font-['JetBrains_Mono'] text-[10px] tracking-widest text-white/50">{label}</div>
        <div className="font-['JetBrains_Mono'] text-[11px] text-white/35">{note}</div>
      </div>
      <div className="font-['Chakra_Petch'] font-semibold text-2xl text-hud tabular-nums">{value}</div>
    </div>
  );
}
