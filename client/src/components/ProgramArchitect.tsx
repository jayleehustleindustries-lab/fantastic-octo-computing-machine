import { useRef, useState, type FormEvent } from "react";
import { buildProgram, type EquipmentAccess, type ExperienceLevel, type ProgramArchitectOutput, type ProgramGoal } from "@/lib/programArchitect";

export function ProgramArchitect() {
  const [form, setForm] = useState({ weightLb: "", goal: "recomposition" as ProgramGoal, experience: "intermediate" as ExperienceLevel, daysPerWeek: 4 as 3 | 4 | 5 | 6, equipment: "home" as EquipmentAccess, focus: "" });
  const [result, setResult] = useState<ProgramArchitectOutput | null>(null);
  const [error, setError] = useState("");
  const outputRef = useRef<HTMLDivElement>(null);
  const inputCls = "w-full min-h-11 bg-white/5 border border-white/30 text-white font-['JetBrains_Mono'] text-sm px-3 py-2 focus:border-hud transition-colors";
  const labelCls = "block font-['JetBrains_Mono'] text-xs tracking-widest text-white/70 mb-2";

  function generate(event: FormEvent) {
    event.preventDefault();
    try {
      setResult(buildProgram({ ...form, weightLb: Number(form.weightLb) }));
      setError("");
      requestAnimationFrame(() => outputRef.current?.focus());
    } catch (caught) {
      setResult(null);
      setError(caught instanceof Error ? caught.message : "Check your inputs and try again.");
    }
  }

  return (
    <div className="grid lg:grid-cols-[0.9fr_1.1fr] gap-8 items-start">
      <form onSubmit={generate} className="border border-white/15 p-6 md:p-8 space-y-5" aria-describedby="architect-privacy architect-disclaimer">
        <div>
          <div className="font-['JetBrains_Mono'] text-xs text-hud tracking-widest mb-1">LOCAL-FIRST // NO ACCOUNT REQUIRED</div>
          <h3 className="font-['Bebas_Neue'] text-3xl text-white">BUILD YOUR STARTING BLUEPRINT</h3>
          <p id="architect-privacy" className="font-['JetBrains_Mono'] text-xs text-white/60 mt-2">Runs in this browser. Your answers are not uploaded or saved.</p>
        </div>
        <div>
          <label htmlFor="architect-weight" className={labelCls}>BODY WEIGHT (LB) *</label>
          <input id="architect-weight" type="number" min="80" max="500" inputMode="decimal" required className={inputCls} value={form.weightLb} onChange={e => setForm({ ...form, weightLb: e.target.value })} placeholder="e.g. 185" />
        </div>
        <div>
          <label htmlFor="architect-goal" className={labelCls}>PRIMARY GOAL *</label>
          <select id="architect-goal" className={inputCls} value={form.goal} onChange={e => setForm({ ...form, goal: e.target.value as ProgramGoal })}>
            <option value="recomposition">Body recomposition</option>
            <option value="fat-loss">Fat loss</option>
            <option value="hypertrophy">Hypertrophy</option>
            <option value="strength">Strength</option>
          </select>
        </div>
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="architect-level" className={labelCls}>EXPERIENCE *</label>
            <select id="architect-level" className={inputCls} value={form.experience} onChange={e => setForm({ ...form, experience: e.target.value as ExperienceLevel })}>
              <option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option>
            </select>
          </div>
          <div>
            <label htmlFor="architect-days" className={labelCls}>DAYS / WEEK *</label>
            <select id="architect-days" className={inputCls} value={form.daysPerWeek} onChange={e => setForm({ ...form, daysPerWeek: Number(e.target.value) as 3 | 4 | 5 | 6 })}>
              {[3, 4, 5, 6].map(day => <option key={day} value={day}>{day} days</option>)}
            </select>
          </div>
        </div>
        <div>
          <label htmlFor="architect-equipment" className={labelCls}>EQUIPMENT *</label>
          <select id="architect-equipment" className={inputCls} value={form.equipment} onChange={e => setForm({ ...form, equipment: e.target.value as EquipmentAccess })}>
            <option value="full-gym">Full gym</option><option value="home">Home equipment / dumbbells / bands</option><option value="bodyweight">Bodyweight only</option>
          </select>
        </div>
        <div>
          <label htmlFor="architect-focus" className={labelCls}>WEAK POINT OR FOCUS (OPTIONAL)</label>
          <input id="architect-focus" type="text" className={inputCls} maxLength={80} value={form.focus} onChange={e => setForm({ ...form, focus: e.target.value })} placeholder="e.g. shoulders, conditioning" />
        </div>
        {error && <p role="alert" className="font-['JetBrains_Mono'] text-xs text-destructive">{error}</p>}
        <button type="submit" className="w-full min-h-12 py-3 bg-hud-deep text-white font-['JetBrains_Mono'] text-xs tracking-widest hover:bg-[#1f54e6] hover:shadow-[0_0_24px_rgb(56_198_255/0.45)] transition-colors">GENERATE MY STARTING PLAN →</button>
        <p id="architect-disclaimer" className="font-['JetBrains_Mono'] text-[11px] leading-relaxed text-white/60">For generally healthy adults. Stop if a movement causes sharp pain. If you have a medical condition, injury, are pregnant, or have a history of disordered eating, consult a qualified clinician before changing training or nutrition.</p>
      </form>

      <div ref={outputRef} tabIndex={-1} aria-live="polite" aria-atomic="true" className="border border-white/15 p-6 md:p-8 min-h-[32rem] focus:outline-none">
        <div className="font-['JetBrains_Mono'] text-xs text-hud tracking-widest mb-3">OUTPUT // PROGRAM ARCHITECT</div>
        {!result ? (
          <div className="h-full min-h-96 flex items-center justify-center border border-dashed border-white/15 p-8 text-center">
            <div><div className="font-['Bebas_Neue'] text-3xl text-white/70 mb-2">YOUR BLUEPRINT LOADS HERE</div><p className="font-['JetBrains_Mono'] text-sm text-white/60">Choose the inputs that match your real week. The useful plan is the one you can repeat.</p></div>
          </div>
        ) : (
          <div>
            <div className="flex flex-wrap items-end justify-between gap-4 border-b border-white/15 pb-5 mb-6">
              <div><div className="font-['JetBrains_Mono'] text-[10px] text-white/60 tracking-widest">PRESCRIBED SPLIT</div><div className="font-['Bebas_Neue'] text-3xl md:text-4xl text-white">{result.split}</div></div>
              <div className="font-['JetBrains_Mono'] text-xs text-hud">STARTING ESTIMATE // REVIEW WEEKLY</div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-7">
              {[{ label: "CALORIES", value: result.calories ? `${result.calories}` : "REVIEW" }, { label: "PROTEIN", value: `${result.protein}g` }, { label: "CARBS", value: result.carbs ? `${result.carbs}g` : "REVIEW" }, { label: "FATS", value: result.fats ? `${result.fats}g` : "REVIEW" }].map(item => (
                <div key={item.label} className="bg-white/5 border border-white/15 p-3"><div className="font-['JetBrains_Mono'] text-[10px] text-white/60">{item.label}</div><div className="font-['Bebas_Neue'] text-2xl text-white">{item.value}</div></div>
              ))}
            </div>
            <h4 className="font-['Bebas_Neue'] text-2xl text-white mb-3">WEEKLY SCHEDULE</h4>
            <ol className="grid sm:grid-cols-2 gap-2 mb-7">{result.schedule.map(day => <li key={day} className="border-l-2 border-hud bg-white/5 px-4 py-3 font-['JetBrains_Mono'] text-xs text-white/80">{day}</li>)}</ol>
            <div className="border border-hud/35 bg-hud-deep/5 p-5 mb-5"><div className="font-['JetBrains_Mono'] text-[10px] text-hud tracking-widest mb-2">COACH JAY DIRECTIVE</div><p className="font-['JetBrains_Mono'] text-xs leading-relaxed text-white/80">{result.directive}</p></div>
            <p className="font-['JetBrains_Mono'] text-[11px] leading-relaxed text-white/60 mb-6">{result.nutritionNote}</p>
            <a href="#apply" className="inline-flex min-h-12 items-center px-5 py-3 border border-white/30 text-white font-['JetBrains_Mono'] text-xs tracking-widest hover:border-hud hover:text-hud">WANT THE FULL PRESCRIPTION? APPLY FOR 1:1 →</a>
          </div>
        )}
      </div>
    </div>
  );
}
