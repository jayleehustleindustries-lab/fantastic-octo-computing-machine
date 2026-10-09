import { useState, useEffect, useRef } from "react";
import { trpc } from "@/lib/trpc";
import ReactMarkdown from "react-markdown";
import { ProgramArchitect } from "@/components/ProgramArchitect";
import { AgentModule } from "@/components/hud/AgentModule";
import { BootLine } from "@/components/hud/BootLine";
import { HudBackdrop } from "@/components/hud/HudBackdrop";
import { HudReticle } from "@/components/hud/HudReticle";
import { AskJay, openAskJay, type AskJayLead } from "@/components/hud/AskJay";
import { COACH, REMAP, SERVICES, TERMS, TIERS } from "@shared/maoContent";
import { captureRef } from "@/lib/visit";

// ── Versioned campaign assets served with the application ──────────────────
const ASSETS = {
  coachPortrait: "/images/coach-jay-mao.jpg",
  galleryOperatorFocus: "/images/operator-focus.jpg",
  galleryAbsoluteFocus: "/images/absolute-focus.jpg",
  galleryTheVisionary: "/images/the-visionary.jpg",
};

// ── Nav component ────────────────────────────────────────────────────────────
function Nav({ activeSection }: { activeSection: string }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const links = [
    { label: "WHAT YOU GET", href: "#services" },
    { label: "PACKAGES", href: "#investment" },
    { label: "COACH JAY", href: "#coach-jay" },
    { label: "APPLY", href: "#apply" },
  ];
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-hud/20">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
        <a href="#" className="flex items-center gap-2 font-['Chakra_Petch'] font-semibold text-base tracking-[0.25em] text-white"><span aria-hidden="true" className="h-2 w-2 rotate-45 border border-hud bg-hud/30" />JAYLEE FIT</a>
        {/* Desktop nav */}
        <div className="hidden lg:flex items-center gap-5">
          {links.map(l => (
            <a key={l.href} href={l.href}
              className={`font-['JetBrains_Mono'] text-[10px] tracking-widest transition-colors ${activeSection === l.href.slice(1) ? 'text-hud' : 'text-white/60 hover:text-white'}`}>
              {l.label}
            </a>
          ))}
          <button type="button" onClick={() => openAskJay()} className="ml-2 px-3 py-1.5 border border-hud/60 text-hud font-['JetBrains_Mono'] text-[10px] tracking-widest hover:bg-hud/10 transition-colors">
            ASK JAY
          </button>
          <a href="#apply" className="px-3 py-1.5 bg-hud-deep text-white font-['JetBrains_Mono'] text-[10px] tracking-widest hover:bg-[#1f54e6] hover:shadow-[0_0_24px_rgb(56_198_255/0.45)] transition-colors">
            APPLY
          </a>
        </div>
        {/* Mobile hamburger */}
        <button className="lg:hidden text-white p-3" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle navigation" aria-expanded={menuOpen} aria-controls="mobile-navigation">
          <div className="w-5 h-0.5 bg-white mb-1" />
          <div className="w-5 h-0.5 bg-white mb-1" />
          <div className="w-5 h-0.5 bg-white" />
        </button>
      </div>
      {/* Mobile overlay */}
      {menuOpen && (
        <div id="mobile-navigation" className="lg:hidden fixed inset-0 top-14 bg-background z-40 flex flex-col items-center justify-center gap-6">
          {links.map(l => (
            <a key={l.href} href={l.href} onClick={() => setMenuOpen(false)}
              className="font-['JetBrains_Mono'] text-lg tracking-widest text-white/80 hover:text-hud transition-colors">
              {l.label}
            </a>
          ))}
          <button type="button" onClick={() => { setMenuOpen(false); openAskJay(); }}
            className="mt-4 px-6 py-3 border border-hud/60 text-hud font-['JetBrains_Mono'] text-sm tracking-widest">
            ASK JAY
          </button>
          <a href="#apply" onClick={() => setMenuOpen(false)}
            className="px-6 py-3 bg-hud-deep text-white font-['JetBrains_Mono'] text-sm tracking-widest">
            APPLY NOW
          </a>
        </div>
      )}
    </nav>
  );
}

// ── Section wrapper ──────────────────────────────────────────────────────────
function Section({ id, index, title, children, className = "" }: {
  id: string; index: string; title: string; children: React.ReactNode; className?: string;
}) {
  // The blue rail draws in when the header first scrolls into view; the grey
  // rail underneath is always there, so nothing waits hidden.
  const railRef = useRef<HTMLDivElement>(null);
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    const el = railRef.current;
    if (!el || typeof IntersectionObserver === "undefined") { setSeen(true); return; }
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) { setSeen(true); observer.disconnect(); }
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return (
    <section id={id} className={`py-20 scroll-mt-14 relative ${className}`}>
      <div className="max-w-6xl mx-auto px-4">
        <div className="mb-10">
          <div className="flex flex-wrap items-center gap-3">
            <span className="border border-hud/40 bg-hud/10 px-2 py-0.5 font-['JetBrains_Mono'] text-[10px] text-hud tracking-widest">{index}</span>
            <h2 className="font-['Chakra_Petch'] font-semibold text-2xl md:text-3xl tracking-[0.12em] text-white">{title}</h2>
          </div>
          <div ref={railRef} className="relative mt-3 h-px overflow-hidden bg-white/10">
            <div className={`absolute inset-0 origin-left bg-gradient-to-r from-hud via-hud/40 to-transparent ${seen ? "hud-draw" : "scale-x-0"}`} />
          </div>
        </div>
        {children}
      </div>
    </section>
  );
}

// ── 4-Phase Application Form ─────────────────────────────────────────────────
function ApplyForm({ onQualified, prefill }: {
  onQualified: (pricing: Record<string, string>) => void;
  /** Name and email handed over by Ask Jay; fills Phase 1 without overwriting typed answers. */
  prefill?: AskJayLead | null;
}) {
  const capabilities = trpc.site.capabilities.useQuery();
  const intakeAvailable = capabilities.data?.applicationIntake === true;
  const [phase, setPhase] = useState(1);
  const [email, setEmail] = useState("");
  const [done, setDone] = useState(false);

  // Phase 1 state
  const [p1, setP1] = useState({ fullName: "", phone: "", location: "" });
  useEffect(() => {
    if (!prefill) return;
    setEmail(current => current || prefill.email);
    setP1(current => (current.fullName ? current : { ...current, fullName: prefill.name }));
  }, [prefill]);
  // Phase 2 state
  const [p2, setP2] = useState({ goal: "", trainingFrequency: "", trainingHistory: "", currentStats: "" });
  // Phase 3 state
  const [p3, setP3] = useState({ hoursPerWeek: "", equipmentAccess: "", biggestObstacle: "", willLog: "" });
  // Phase 4 state
  const [p4, setP4] = useState({ whyNow: "", startWindow: "", investmentAck: false, reviewAgreement: false });

  const phase1Mut = trpc.application.submitPhase1.useMutation();
  const phase2Mut = trpc.application.submitPhase2.useMutation();
  const phase3Mut = trpc.application.submitPhase3.useMutation();
  const phase4Mut = trpc.application.submitPhase4.useMutation();
  const applicationError = phase1Mut.error ?? phase2Mut.error ?? phase3Mut.error ?? phase4Mut.error;

  const inputCls = "w-full bg-white/5 border border-white/20 text-white font-['JetBrains_Mono'] text-sm px-3 py-2 focus:outline-none focus:border-hud transition-colors placeholder:text-white/30";
  const labelCls = "block font-['JetBrains_Mono'] text-xs tracking-widest text-white/60 mb-1";
  const selectCls = `${inputCls} appearance-none`;

  async function handlePhase1() {
    if (!email || !p1.fullName || !p1.location) return;
    await phase1Mut.mutateAsync({ email, fullName: p1.fullName, phone: p1.phone || undefined, location: p1.location });
    setPhase(2);
  }
  async function handlePhase2() {
    if (!p2.goal || !p2.trainingFrequency || !p2.trainingHistory) return;
    await phase2Mut.mutateAsync({ email, ...p2 });
    setPhase(3);
  }
  async function handlePhase3() {
    if (!p3.hoursPerWeek || !p3.equipmentAccess || !p3.biggestObstacle || !p3.willLog) return;
    await phase3Mut.mutateAsync({ email, ...p3 });
    setPhase(4);
  }
  async function handlePhase4() {
    if (!p4.whyNow || !p4.startWindow || !p4.investmentAck || !p4.reviewAgreement) return;
    const result = await phase4Mut.mutateAsync({ email, ...p4 });
    onQualified(result.pricing as Record<string, string>);
    setDone(true);
  }

  if (done) {
    return (
      <div className="text-center py-16">
        <div className="font-['JetBrains_Mono'] text-xs text-hud tracking-widest mb-4">// APPLICATION RECEIVED</div>
        <div className="font-['Bebas_Neue'] text-4xl text-white mb-4">QUALIFICATION COMPLETE</div>
        <p className="font-['JetBrains_Mono'] text-sm text-white/60 mb-8">Your application is queued for Coach Jay's review. Investment packages are now unlocked.</p>
        <a href="#investment" className="inline-block px-6 py-3 bg-hud-deep text-white font-['JetBrains_Mono'] text-xs tracking-widest hover:bg-[#1f54e6] hover:shadow-[0_0_24px_rgb(56_198_255/0.45)] transition-colors">
          VIEW INVESTMENT PACKAGES →
        </a>
      </div>
    );
  }

  return (
    <div>
      {/* Stepper */}
      <div className="flex gap-2 mb-8">
        {[1,2,3,4].map(n => (
          <div key={n} className={`flex-1 h-1 ${n <= phase ? 'bg-hud-deep' : 'bg-white/10'} transition-colors`} />
        ))}
      </div>
      <div className="font-['JetBrains_Mono'] text-xs text-white/40 tracking-widest mb-6">
        PHASE {phase} OF 4 · APPLICATIONS ARE REVIEWED BY COACH JAY.
      </div>
      {!capabilities.isPending && !intakeAvailable && (
        <div className="mb-6 border border-amber-400/40 bg-amber-400/5 p-4 font-['JetBrains_Mono'] text-xs text-amber-200">
          ONLINE APPLICATIONS ARE TEMPORARILY PAUSED. No information entered below will be submitted until secure intake storage is connected.
        </div>
      )}
      {applicationError && (
        <p className="mb-5 font-['JetBrains_Mono'] text-xs text-destructive">SUBMISSION ERROR: {applicationError.message}</p>
      )}

      {/* Phase 1 */}
      {phase === 1 && (
        <div className="space-y-5">
          <div className="font-['Bebas_Neue'] text-2xl text-white mb-2">PHASE 1 — IDENTITY <span className="text-white/40 text-lg">// WHO IS APPLYING?</span></div>
          <div>
            <label className={labelCls}>EMAIL *</label>
            <input type="email" className={inputCls} placeholder="operator@company.com"
              value={email} onChange={e => setEmail(e.target.value)}
              required />
            <p className="font-['JetBrains_Mono'] text-xs text-white/30 mt-1">We'll use this email to contact you with your qualification results and next steps.</p>
          </div>
          <div>
            <label className={labelCls}>FULL NAME *</label>
            <input type="text" className={inputCls} placeholder="First and last name"
              value={p1.fullName} onChange={e => setP1({...p1, fullName: e.target.value})} required />
            <p className="font-['JetBrains_Mono'] text-xs text-white/30 mt-1">First and last. Coach Jay reviews every application personally.</p>
          </div>
          <div>
            <label className={labelCls}>PHONE</label>
            <input type="tel" className={inputCls} placeholder="Optional"
              value={p1.phone} onChange={e => setP1({...p1, phone: e.target.value})} />
            <p className="font-['JetBrains_Mono'] text-xs text-white/30 mt-1">Optional — for faster scheduling once you're approved.</p>
          </div>
          <div>
            <label className={labelCls}>LOCATION / TIMEZONE *</label>
            <input type="text" className={inputCls} placeholder="City, state, timezone"
              value={p1.location} onChange={e => setP1({...p1, location: e.target.value})} required />
            <p className="font-['JetBrains_Mono'] text-xs text-white/30 mt-1">City, state, timezone. Check-ins and Zoom calls are scheduled around it.</p>
          </div>
          <button onClick={handlePhase1} disabled={phase1Mut.isPending || !intakeAvailable}
            className="w-full py-3 bg-hud-deep text-white font-['JetBrains_Mono'] text-xs tracking-widest hover:bg-[#1f54e6] hover:shadow-[0_0_24px_rgb(56_198_255/0.45)] transition-colors disabled:opacity-50">
            {phase1Mut.isPending ? "PROCESSING..." : "NEXT PHASE →"}
          </button>
        </div>
      )}

      {/* Phase 2 */}
      {phase === 2 && (
        <div className="space-y-5">
          <div className="font-['Bebas_Neue'] text-2xl text-white mb-2">PHASE 2 — MISSION PROFILE <span className="text-white/40 text-lg">// WHAT ARE WE BUILDING?</span></div>
          <div>
            <label className={labelCls}>YOUR SINGLE MOST IMPORTANT 12-WEEK GOAL *</label>
            <textarea className={`${inputCls} h-24 resize-none`} placeholder="One goal. Be specific. 'Get in shape' is not a mission."
              value={p2.goal} onChange={e => setP2({...p2, goal: e.target.value})} required />
          </div>
          <div>
            <label className={labelCls}>CURRENT TRAINING FREQUENCY *</label>
            <select className={selectCls} value={p2.trainingFrequency} onChange={e => setP2({...p2, trainingFrequency: e.target.value})} required>
              <option value="">SELECT —</option>
              <option value="NOT TRAINING RIGHT NOW">NOT TRAINING RIGHT NOW</option>
              <option value="1–2 DAYS PER WEEK">1–2 DAYS PER WEEK</option>
              <option value="3–4 DAYS PER WEEK">3–4 DAYS PER WEEK</option>
              <option value="5+ DAYS PER WEEK">5+ DAYS PER WEEK</option>
            </select>
          </div>
          <div>
            <label className={labelCls}>TRAINING HISTORY *</label>
            <select className={selectCls} value={p2.trainingHistory} onChange={e => setP2({...p2, trainingHistory: e.target.value})} required>
              <option value="">SELECT —</option>
              <option value="NEW TO STRUCTURED TRAINING">NEW TO STRUCTURED TRAINING</option>
              <option value="1–3 YEARS">1–3 YEARS</option>
              <option value="3–10 YEARS">3–10 YEARS</option>
              <option value="10+ YEARS">10+ YEARS</option>
            </select>
          </div>
          <div>
            <label className={labelCls}>CURRENT STATS</label>
            <input type="text" className={inputCls} placeholder="Height, weight, body fat % (estimates fine)"
              value={p2.currentStats} onChange={e => setP2({...p2, currentStats: e.target.value})} />
          </div>
          <button onClick={handlePhase2} disabled={phase2Mut.isPending || !intakeAvailable}
            className="w-full py-3 bg-hud-deep text-white font-['JetBrains_Mono'] text-xs tracking-widest hover:bg-[#1f54e6] hover:shadow-[0_0_24px_rgb(56_198_255/0.45)] transition-colors disabled:opacity-50">
            {phase2Mut.isPending ? "PROCESSING..." : "NEXT PHASE →"}
          </button>
        </div>
      )}

      {/* Phase 3 */}
      {phase === 3 && (
        <div className="space-y-5">
          <div className="font-['Bebas_Neue'] text-2xl text-white mb-2">PHASE 3 — LOGISTICS & COMMITMENT <span className="text-white/40 text-lg">// CAN YOU EXECUTE?</span></div>
          <div>
            <label className={labelCls}>HOURS PER WEEK YOU CAN TRAIN *</label>
            <select className={selectCls} value={p3.hoursPerWeek} onChange={e => setP3({...p3, hoursPerWeek: e.target.value})} required>
              <option value="">SELECT —</option>
              <option value="2–3 HOURS">2–3 HOURS</option>
              <option value="4–6 HOURS">4–6 HOURS</option>
              <option value="7–9 HOURS">7–9 HOURS</option>
              <option value="10+ HOURS">10+ HOURS</option>
            </select>
          </div>
          <div>
            <label className={labelCls}>EQUIPMENT ACCESS *</label>
            <select className={selectCls} value={p3.equipmentAccess} onChange={e => setP3({...p3, equipmentAccess: e.target.value})} required>
              <option value="">SELECT —</option>
              <option value="FULL GYM">FULL GYM</option>
              <option value="HOME SETUP (DUMBBELLS / BANDS)">HOME SETUP (DUMBBELLS / BANDS)</option>
              <option value="BODYWEIGHT ONLY">BODYWEIGHT ONLY</option>
              <option value="GYM + HOME">GYM + HOME</option>
            </select>
          </div>
          <div>
            <label className={labelCls}>YOUR BIGGEST OBSTACLE *</label>
            <textarea className={`${inputCls} h-24 resize-none`} placeholder="What has killed your consistency before?"
              value={p3.biggestObstacle} onChange={e => setP3({...p3, biggestObstacle: e.target.value})} required />
          </div>
          <div>
            <label className={labelCls}>WILL YOU LOG WORKOUTS AND MEALS DAILY? *</label>
            <div className="flex gap-4 mt-2">
              {["YES — EVERY DAY", "NO"].map(opt => (
                <label key={opt} className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" name="willLog" value={opt}
                    checked={p3.willLog === opt} onChange={() => setP3({...p3, willLog: opt})}
                    className="accent-hud-deep" />
                  <span className="font-['JetBrains_Mono'] text-xs text-white/70">{opt}</span>
                </label>
              ))}
            </div>
            <p className="font-['JetBrains_Mono'] text-xs text-white/30 mt-1">The Accountability Loop only works if you feed it. 'No' does not disqualify you, but say it now.</p>
          </div>
          <button onClick={handlePhase3} disabled={phase3Mut.isPending || !intakeAvailable}
            className="w-full py-3 bg-hud-deep text-white font-['JetBrains_Mono'] text-xs tracking-widest hover:bg-[#1f54e6] hover:shadow-[0_0_24px_rgb(56_198_255/0.45)] transition-colors disabled:opacity-50">
            {phase3Mut.isPending ? "PROCESSING..." : "NEXT PHASE →"}
          </button>
        </div>
      )}

      {/* Phase 4 */}
      {phase === 4 && (
        <div className="space-y-5">
          <div className="font-['Bebas_Neue'] text-2xl text-white mb-2">PHASE 4 — READINESS <span className="text-white/40 text-lg">// FINAL GATE.</span></div>
          <div>
            <label className={labelCls}>WHY NOW? *</label>
            <textarea className={`${inputCls} h-24 resize-none`} placeholder="What changed? Why is this the 12-week block where it actually happens?"
              value={p4.whyNow} onChange={e => setP4({...p4, whyNow: e.target.value})} required />
          </div>
          <div>
            <label className={labelCls}>PREFERRED START WINDOW *</label>
            <select className={selectCls} value={p4.startWindow} onChange={e => setP4({...p4, startWindow: e.target.value})} required>
              <option value="">SELECT —</option>
              <option value="IMMEDIATELY">IMMEDIATELY</option>
              <option value="WITHIN 2 WEEKS">WITHIN 2 WEEKS</option>
              <option value="WITHIN 30 DAYS">WITHIN 30 DAYS</option>
              <option value="JUST SCOUTING">JUST SCOUTING</option>
            </select>
          </div>
          <label className="flex items-start gap-3 cursor-pointer">
            <input type="checkbox" checked={p4.investmentAck} onChange={e => setP4({...p4, investmentAck: e.target.checked})}
              className="mt-0.5 accent-hud-deep" />
            <span className="font-['JetBrains_Mono'] text-xs text-white/70">I understand MAO packages are premium coaching investments, not subscriptions, and pricing is revealed after qualification.</span>
          </label>
          <label className="flex items-start gap-3 cursor-pointer">
            <input type="checkbox" checked={p4.reviewAgreement} onChange={e => setP4({...p4, reviewAgreement: e.target.checked})}
              className="mt-0.5 accent-hud-deep" />
            <span className="font-['JetBrains_Mono'] text-xs text-white/70">I understand this application will be reviewed and submission does not guarantee acceptance.</span>
          </label>
          <button onClick={handlePhase4} disabled={phase4Mut.isPending || !intakeAvailable}
            className="w-full py-3 bg-hud-deep text-white font-['JetBrains_Mono'] text-xs tracking-widest hover:bg-[#1f54e6] hover:shadow-[0_0_24px_rgb(56_198_255/0.45)] transition-colors disabled:opacity-50">
            {phase4Mut.isPending ? "PROCESSING..." : "COMPLETE QUALIFICATION →"}
          </button>
        </div>
      )}
    </div>
  );
}

// ── Main Home page ───────────────────────────────────────────────────────────
export default function Home() {
  const capabilities = trpc.site.capabilities.useQuery();
  const paymentReportingAvailable = capabilities.data?.paymentReporting === true;
  const [activeSection, setActiveSection] = useState("hero");
  const [qualified, setQualified] = useState(false);
  const [pricing, setPricing] = useState<Record<string, string>>({});
  const chatAvailable = capabilities.data?.aiChat === true;
  const remapOffer = trpc.remap.offer.useQuery();
  const remapPrice = remapOffer.data?.priceCents ? `$${(remapOffer.data.priceCents / 100).toFixed(remapOffer.data.priceCents % 100 ? 2 : 0)}` : null;
  useEffect(() => { captureRef(); }, []);
  const [applyPrefill, setApplyPrefill] = useState<AskJayLead | null>(null);
  const [lightboxImg, setLightboxImg] = useState<string | null>(null);
  const [payForm, setPayForm] = useState({ name: "", email: "", method: "PayPal", amount: "", orderId: "", transactionId: "", note: "" });
  const [payDone, setPayDone] = useState(false);
  const payMut = trpc.payment.report.useMutation({ onSuccess: () => setPayDone(true) });

  // Scroll spy
  useEffect(() => {
    const sections = ["services","investment","coach-jay","apply"];
    const observer = new IntersectionObserver(
      entries => { entries.forEach(e => { if (e.isIntersecting) setActiveSection(e.target.id); }); },
      { rootMargin: "-40% 0px -40% 0px" }
    );
    sections.forEach(id => { const el = document.getElementById(id); if (el) observer.observe(el); });
    return () => observer.disconnect();
  }, []);

  // The invoice panel is collapsed by default; open it when linked to directly.
  useEffect(() => {
    const openInvoice = () => {
      const panel = document.getElementById("pay-invoice");
      if (window.location.hash === "#pay-invoice" && panel instanceof HTMLDetailsElement) panel.open = true;
    };
    openInvoice();
    window.addEventListener("hashchange", openInvoice);
    return () => window.removeEventListener("hashchange", openInvoice);
  }, []);

  // Restore qualification from session storage
  useEffect(() => {
    if (sessionStorage.getItem("maoQualified") === "true") {
      setQualified(true);
      try { setPricing(JSON.parse(sessionStorage.getItem("maoPricing") ?? "{}")); } catch {}
    }
  }, []);

  useEffect(() => {
    if (!lightboxImg) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setLightboxImg(null);
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [lightboxImg]);

  // Ask Jay hands a ready visitor to the application with their details filled in.
  function handleAskJayApply(lead: AskJayLead) {
    setApplyPrefill({ ...lead });
    document.getElementById("apply")?.scrollIntoView({ behavior: "smooth" });
  }

  function handleQualified(p: Record<string, string>) {
    setQualified(true);
    setPricing(p);
    sessionStorage.setItem("maoQualified", "true");
    sessionStorage.setItem("maoPricing", JSON.stringify(p));
  }

  const inputCls = "w-full bg-white/5 border border-white/20 text-white font-['JetBrains_Mono'] text-sm px-3 py-2 focus:outline-none focus:border-hud transition-colors placeholder:text-white/30";
  const labelCls = "block font-['JetBrains_Mono'] text-xs tracking-widest text-white/60 mb-1";

  return (
    <div className="bg-background text-white min-h-screen">
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <HudBackdrop />
      <Nav activeSection={activeSection} />
      <main id="main-content" className="relative z-10">

      {/* ── HERO ─────────────────────────────────────────────────────────── */}
      <section id="hero" className="min-h-screen flex flex-col justify-center pt-14 relative overflow-hidden">
        <div aria-hidden="true" className="absolute inset-0" style={{ background: "radial-gradient(circle at 72% 45%, rgb(37 99 255 / 0.16), transparent 55%)" }} />
        {/* Phone: reticle sits behind the headline */}
        <div aria-hidden="true" className="lg:hidden absolute -right-24 top-24 w-[360px] opacity-25 pointer-events-none [&_div_div]:hidden">
          <HudReticle />
        </div>
        <div className="max-w-6xl mx-auto px-4 relative z-10 w-full grid lg:grid-cols-[1.15fr_0.85fr] gap-10 items-center">
          <div>
            <BootLine />
            <div className="font-['JetBrains_Mono'] text-xs text-white/40 tracking-widest mt-4 mb-6">
              JAYLEE FIT ·· EST. JAYLEE HUSTLE INDUSTRIES LLC
            </div>
            <div className="mb-4">
              <h1 className="font-['Bebas_Neue'] text-[120px] md:text-[180px] leading-none text-white tracking-tight hud-glow">MAO</h1>
              <div className="font-['Chakra_Petch'] font-semibold text-2xl md:text-4xl tracking-[0.3em] text-hud">METHODOLOGY</div>
              <div className="font-['JetBrains_Mono'] text-xs text-white/30 tracking-widest mt-2">JAYLEE HUSTLE INDUSTRIES</div>
            </div>
            <div className="relative w-40 h-px bg-white/10 mb-6 overflow-hidden">
              <div className="absolute inset-0 hud-draw bg-gradient-to-r from-hud to-hud-deep" />
            </div>
            <p className="font-['JetBrains_Mono'] text-sm text-white/70 max-w-2xl leading-relaxed mb-3">
              JayLee Hustle Industries uses the MAO (Massive Action Orientation) Framework—a practical system combining physical conditioning, focused habits, and accountability for busy founders and career professionals.
            </p>
            <p className="font-['JetBrains_Mono'] text-sm text-white/70 max-w-2xl leading-relaxed mb-10">
              Adaptation is the game. Ask Jay anything or build a starting plan in a two-minute chat, then apply for 1:1 coaching.
            </p>
            <div className="flex flex-wrap gap-4">
              <a href="#apply" className="px-8 py-4 bg-hud-deep text-white font-['JetBrains_Mono'] text-xs tracking-widest shadow-[0_0_18px_rgb(37_99_255/0.35)] hover:bg-[#1f54e6] hover:shadow-[0_0_28px_rgb(56_198_255/0.55)] transition-[background-color,box-shadow,transform] active:scale-[0.97]">
                APPLY FOR A PACKAGE
              </a>
              <a href="#ai-engine" onClick={event => { if (chatAvailable) { event.preventDefault(); openAskJay("Build me a starting plan"); } }} className="px-8 py-4 border border-hud/50 text-hud font-['JetBrains_Mono'] text-xs tracking-widest hover:bg-hud/10 hover:border-hud transition-colors active:scale-[0.97]">
                BUILD MY STARTING PLAN
              </a>
            </div>
            <a href="/remap" className="inline-block mt-6 font-['JetBrains_Mono'] text-xs tracking-widest text-hud hover:text-white">OR START TODAY WITH REMAP →</a>
            <div className="mt-12 font-['JetBrains_Mono'] text-xs text-hud/50 tracking-widest animate-bounce">↓ SCROLL</div>
          </div>
          <HudReticle className="hidden lg:block w-full max-w-[460px] justify-self-end" />
        </div>
      </section>

      {/* ── SERVICES ─────────────────────────────────────────────────────── */}
      <Section id="services" index="01 /" title="WHAT YOU GET" className="border-t border-white/5">
        <p className="font-['JetBrains_Mono'] text-sm text-white/60 max-w-2xl mb-8">
          Coaching for busy founders, athletes and professionals who are done starting over. One system for your training, your habits and your accountability.
        </p>
        <div className="grid md:grid-cols-3 gap-6">
          {SERVICES.map(s => (
            <div key={s.code} className="border border-white/10 p-6 hover:border-hud/40 transition-colors group">
              <div className="font-['JetBrains_Mono'] text-xs text-hud tracking-widest mb-2">{s.code}</div>
              <div className="font-['Bebas_Neue'] text-2xl text-white mb-3 group-hover:text-hud transition-colors">{s.title}</div>
              <p className="font-['JetBrains_Mono'] text-xs text-white/60 leading-relaxed mb-5">{s.desc}</p>
              <div className="space-y-2">
                {s.features.map(f => (
                  <div key={f} className="flex items-center gap-2">
                    <div className="w-1 h-1 bg-hud-deep flex-shrink-0" />
                    <span className="font-['JetBrains_Mono'] text-[10px] text-white/50 tracking-wider">{f}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        <dl className="mt-8 grid md:grid-cols-2 gap-4">
          {TERMS.filter(t => t.code === "G/01" || t.code === "G/02").map(t => (
            <div key={t.code} className="border-l-2 border-hud/50 pl-4">
              <dt className="font-['JetBrains_Mono'] text-[10px] text-hud tracking-widest mb-1">{t.term}</dt>
              <dd className="font-['JetBrains_Mono'] text-xs text-white/55 leading-relaxed">{t.def}</dd>
            </div>
          ))}
        </dl>
      </Section>

      {/* ── INVESTMENT ───────────────────────────────────────────────────── */}
      <Section id="investment" index="02 /" title="PACKAGES" className="border-t border-white/5">
        <p className="font-['JetBrains_Mono'] text-sm text-white/60 max-w-2xl mb-8">
          Two ways in. Start today with a Remap built around your body and schedule, or apply for 1:1 coaching with Coach Jay on the MAO methodology.
        </p>
        <AgentModule code="INV/00" name={REMAP.name} status={remapOffer.data?.available ? "online" : "standby"} label={remapOffer.data?.available ? "AVAILABLE NOW" : "OPENING SOON"} className="mb-12 border-hud/70! shadow-[0_0_32px_rgb(56_198_255/0.12)]">
          <div className="p-6 grid md:grid-cols-[1.1fr_0.9fr] gap-6 items-center">
            <div>
              <div className="inline-block mb-3 bg-hud-deep px-3 py-0.5 font-['JetBrains_Mono'] text-[10px] tracking-widest text-white">NO APPLICATION</div>
              <div className="font-['Chakra_Petch'] font-semibold text-3xl tracking-[0.12em] text-white">{REMAP.name}{remapPrice && <span className="text-hud"> · {remapPrice}</span>}</div>
              <p className="font-['JetBrains_Mono'] text-sm text-white/70 leading-relaxed mt-3">{REMAP.tagline} {REMAP.desc}</p>
              <a href="/remap" className="inline-block mt-5 px-6 py-3 bg-hud-deep text-white font-['JetBrains_Mono'] text-xs tracking-widest hover:bg-[#1f54e6] hover:shadow-[0_0_24px_rgb(56_198_255/0.45)] transition-colors">
                {remapOffer.data?.available ? "BUILD MY REMAP →" : "SEE REMAP + FREE BMR CALCULATOR →"}
              </a>
            </div>
            <ul className="space-y-2">
              {REMAP.features.map(f => (
                <li key={f} className="flex items-start gap-2 font-['JetBrains_Mono'] text-[11px] text-white/65"><span className="text-hud">▸</span>{f}</li>
              ))}
            </ul>
          </div>
        </AgentModule>
        <h3 className="font-['Chakra_Petch'] font-semibold text-lg tracking-[0.18em] text-white mb-4">1:1 COACHING <span className="text-white/40 text-sm">// BY APPLICATION</span></h3>
        {!qualified && (
          <div className="border border-hud/40 p-5 bg-hud-deep/5 mb-8 text-center">
            <div className="font-['JetBrains_Mono'] text-xs text-hud tracking-widest">COACHING PRICING IS REVEALED AFTER YOU COMPLETE THE APPLICATION.</div>
          </div>
        )}
        <div className="grid md:grid-cols-3 gap-6">
          {TIERS.map(tier => (
            <AgentModule key={tier.code} code={tier.code} name={tier.title}
              status={qualified ? "online" : "standby"} label={qualified ? "UNLOCKED" : "LOCKED"}
              className={`${tier.badge ? 'border-hud/70! shadow-[0_0_32px_rgb(56_198_255/0.12)]' : ''} hover:border-hud/60 transition-colors`}>
            <div className="p-6">
              {tier.badge && (
                <div className="inline-block mb-3 bg-hud-deep px-3 py-0.5 font-['JetBrains_Mono'] text-[10px] tracking-widest text-white">{tier.badge}</div>
              )}
              <div className="font-['Bebas_Neue'] text-3xl text-white mb-2">{tier.title}</div>
              <div className="font-['JetBrains_Mono'] text-sm text-white/40 mb-4">
                {qualified ? (pricing[tier.priceKey] ?? "Contact for Pricing") : "[PRICING HIDDEN] / REVEALED AFTER QUALIFICATION"}
              </div>
              <p className="font-['JetBrains_Mono'] text-xs text-white/60 leading-relaxed mb-5">{tier.desc}</p>
              <div className="space-y-2 mb-6">
                {tier.features.map(f => (
                  <div key={f} className="flex items-start gap-2">
                    <div className="w-1 h-1 bg-hud-deep flex-shrink-0 mt-1.5" />
                    <span className="font-['JetBrains_Mono'] text-[10px] text-white/50">{f}</span>
                  </div>
                ))}
              </div>
              <a href="#apply" className="block text-center py-2.5 border border-hud text-hud font-['JetBrains_Mono'] text-xs tracking-widest hover:bg-hud-deep hover:text-white transition-colors">
                {tier.cta}
              </a>
            </div>
            </AgentModule>
          ))}
        </div>
        <p className="font-['JetBrains_Mono'] text-[10px] text-white/30 mt-6">* IN-PERSON INTENSIVES SUBJECT TO COACH AVAILABILITY AND SCHEDULING. ALL PACKAGES BY APPLICATION VIA THE MAO INTAKE.</p>
      </Section>

      {/* ── COACH JAY ────────────────────────────────────────────────────── */}
      <Section id="coach-jay" index="03 /" title="COACH JAY" className="border-t border-white/5">
        <div className="grid lg:grid-cols-2 gap-12 items-start">
          <div>
            <img src={ASSETS.coachPortrait} alt="Coach Jay — Jordan Lee" className="w-full max-w-sm object-cover" />
            <div className="font-['JetBrains_Mono'] text-[10px] text-white/30 tracking-widest mt-3">
              FOUNDER & COACH · HOT SPRINGS, ARKANSAS · JAYLEE FIT — JLH INDUSTRIES LLC
            </div>
          </div>
          <div>
            <div className="font-['Bebas_Neue'] text-2xl text-white mb-6 border-l-2 border-hud pl-4">
              JAYLEE FIT IS NOT A GYM. IT IS AN OPERATING SYSTEM FOR YOUR BODY.
            </div>
            {COACH.bio.map((para, i) => (
              <p key={i} className={`font-['JetBrains_Mono'] text-sm text-white/70 leading-relaxed ${i === COACH.bio.length - 1 ? "mb-8" : "mb-4"}`}>{para}</p>
            ))}
            <div className="grid grid-cols-2 gap-6 mb-8">
              {COACH.blocks.map(b => (
                <div key={b.label}>
                  <div className="font-['JetBrains_Mono'] text-[10px] text-hud tracking-widest mb-2">{b.label}</div>
                  <ul className="space-y-1">
                    {b.items.map(i => (
                      <li key={i} className="font-['JetBrains_Mono'] text-[10px] text-white/50">{i}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { stat: "100%", label: "Home-based programs" },
                { stat: "1:1", label: "Personal coaching" },
                { stat: "CUSTOM", label: "Every plan" },
                { stat: "REAL", label: "Accountability" },
              ].map(s => (
                <div key={s.stat} className="border border-white/10 p-3 text-center">
                  <div className="font-['Bebas_Neue'] text-2xl text-hud">{s.stat}</div>
                  <div className="font-['JetBrains_Mono'] text-[9px] text-white/40 tracking-wider">{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="mt-12 grid grid-cols-3 gap-2 md:gap-4">
          {[
            { src: ASSETS.galleryOperatorFocus, caption: "OPERATOR FOCUS" },
            { src: ASSETS.galleryAbsoluteFocus, caption: "ABSOLUTE FOCUS" },
            { src: ASSETS.galleryTheVisionary, caption: "THE VISIONARY" },
          ].map(img => (
            <button key={img.caption} type="button" aria-label={`Open ${img.caption} image`} className="relative group cursor-pointer overflow-hidden aspect-[4/5] text-left"
              onClick={() => setLightboxImg(img.src)}>
              <img src={img.src} alt={img.caption} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
              <div className="absolute inset-0 bg-black/40 group-hover:bg-black/20 transition-colors" />
              <div className="absolute bottom-4 left-4 font-['JetBrains_Mono'] text-xs text-white tracking-widest">{img.caption}</div>
            </button>
          ))}
        </div>
        {lightboxImg && (
          <div role="dialog" aria-modal="true" aria-label="Expanded gallery image" className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4" onClick={() => setLightboxImg(null)}>
            <img src={lightboxImg} alt="Expanded JayLee Fit gallery" className="max-h-[90vh] max-w-full object-contain" onClick={event => event.stopPropagation()} />
            <button type="button" autoFocus onClick={() => setLightboxImg(null)} className="absolute top-4 right-4 min-h-11 px-4 text-white bg-black/70 font-['JetBrains_Mono'] text-xs tracking-widest hover:text-hud">CLOSE ✕</button>
          </div>
        )}
        <p className="mt-8 border border-white/10 p-4 font-['JetBrains_Mono'] text-xs text-white/50">
          <span className="text-hud tracking-widest">CLIENT RESULTS //</span> Verified testimonials are publishing soon. Ask Coach Jay for references during your application review.
        </p>
      </Section>

      {/* ── APPLY ────────────────────────────────────────────────────────── */}
      <Section id="apply" index="04 /" title="APPLY" className="border-t border-white/5">
        <div className="grid lg:grid-cols-2 gap-12">
          <div>
            <p className="font-['JetBrains_Mono'] text-sm text-white/60 leading-relaxed mb-8">
              Four short steps. Coach Jay reads every application himself and replies with next steps. Package pricing is shown once you finish. Not sure yet? Ask Jay any question first.
            </p>
            <div className="border border-hud/30 p-5 mb-8 bg-hud-deep/5">
              <div className="font-['JetBrains_Mono'] text-xs text-hud tracking-widest mb-2">VELVET ROPE // PROTOCOL</div>
              <p className="font-['JetBrains_Mono'] text-xs text-white/60 leading-relaxed">Coaching has no "buy now" button and no discount codes. Pricing is revealed by application only, and Coach Jay reviews every completed application himself. Want to start on your own today? That's what Remap is for.</p>
            </div>
            <div className="font-['JetBrains_Mono'] text-xs text-white/30 space-y-1">
              <div>4-PHASE STRICT QUALIFICATION</div>
              <div>PHASE 1 — IDENTITY</div>
              <div>PHASE 2 — MISSION PROFILE</div>
              <div>PHASE 3 — LOGISTICS & COMMITMENT</div>
              <div>PHASE 4 — READINESS</div>
            </div>
          </div>
          <AgentModule
            code="MOD-02"
            name="ADMISSION"
            status={capabilities.data ? (capabilities.data.applicationIntake ? "online" : "offline") : "standby"}
          >
            <div className="p-5 md:p-6">
              <ApplyForm onQualified={handleQualified} prefill={applyPrefill} />
            </div>
          </AgentModule>
        </div>
      </Section>

      {/* ── AI ENGINE ────────────────────────────────────────────────────── */}
      {capabilities.data && !chatAvailable && (
      <Section id="ai-engine" index="05 /" title="BUILD A STARTING PLAN" className="border-t border-white/5">
        <AgentModule code="MOD-05" name="PROGRAM ARCHITECT" status="online" label="LOCAL · ONLINE">
          <div className="p-4 md:p-6">
            <ProgramArchitect />
          </div>
        </AgentModule>
      </Section>
      )}

      </main>

      {/* ── PAY INVOICE (existing clients) ──────────────────────────────── */}
      <section className="relative z-10 border-t border-white/5">
        <details id="pay-invoice" className="max-w-6xl mx-auto px-4 py-8 group scroll-mt-14">
          <summary className="cursor-pointer list-none font-['JetBrains_Mono'] text-xs text-white/60 tracking-widest hover:text-white">
            <span className="text-hud">+</span> EXISTING CLIENT? PAY AN INVOICE
          </summary>
          <div className="pt-6">
        <p className="font-['JetBrains_Mono'] text-sm text-white/60 max-w-2xl mb-4">
          For already-onboarded clients only. Once Coach Jay has approved your application and issued an Order ID, settle your invoice via PayPal below.
        </p>
        <div className="border border-hud/30 p-4 bg-hud-deep/5 mb-8 inline-block">
          <span className="font-['JetBrains_Mono'] text-xs text-hud tracking-widest">NEW HERE? RUN THE INTAKE ABOVE. MAO DOES NOT SELL OFF THE SHELF.</span>
        </div>
        <div className="grid lg:grid-cols-2 gap-10">
          {/* PayPal panel */}
          <div className="border border-white/10 p-6 min-w-0">
            <div className="font-['JetBrains_Mono'] text-xs text-hud tracking-widest mb-3">PAYPAL</div>
            <p className="font-['JetBrains_Mono'] text-xs text-white/60 mb-4">Send to the JayLee Hustle Industries PayPal handle:</p>
            <div className="flex items-center gap-3 bg-white/5 border border-white/20 px-4 py-3 mb-4 min-w-0">
              <span className="font-['JetBrains_Mono'] text-sm text-white flex-1 min-w-0 break-all">magicdeals.wholesale@gmail.com</span>
              <button onClick={() => navigator.clipboard.writeText("magicdeals.wholesale@gmail.com")}
                className="font-['JetBrains_Mono'] text-[10px] text-white/40 hover:text-white tracking-widest transition-colors">COPY</button>
            </div>
            <a href="https://www.paypal.com/" target="_blank" rel="noopener noreferrer"
              className="inline-block px-5 py-2.5 border border-white/20 text-white font-['JetBrains_Mono'] text-xs tracking-widest hover:border-white/40 transition-colors">
              OPEN PAYPAL →
            </a>
          </div>
          {/* Self-report form */}
          <div className="border border-white/10 p-6 min-w-0">
            <div className="font-['JetBrains_Mono'] text-xs text-hud tracking-widest mb-1">PAYMENT // SELF-REPORT</div>
            <div className="font-['Bebas_Neue'] text-2xl text-white mb-2">ALREADY SENT PAYMENT?</div>
            <p className="font-['JetBrains_Mono'] text-xs text-white/50 mb-6">Submit your details and PayPal Transaction ID for manual review. A payment report is not confirmation; access begins only after the transaction is verified.</p>
            {payDone ? (
              <div className="text-center py-8">
                <div className="font-['JetBrains_Mono'] text-xs text-hud tracking-widest mb-2">// RECEIVED</div>
                <div className="font-['Bebas_Neue'] text-2xl text-white">PAYMENT REPORT RECEIVED</div>
                <p className="font-['JetBrains_Mono'] text-xs text-white/50 mt-2">Awaiting manual review.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {[
                  { label: "NAME *", key: "name", type: "text", placeholder: "Full name" },
                  { label: "EMAIL *", key: "email", type: "email", placeholder: "your@email.com" },
                  { label: "AMOUNT *", key: "amount", type: "text", placeholder: "e.g. 500.00" },
                  { label: "ORDER ID *", key: "orderId", type: "text", placeholder: "Issued by Coach Jay" },
                  { label: "PAYPAL TRANSACTION ID *", key: "transactionId", type: "text", placeholder: "From your PayPal receipt" },
                ].map(f => (
                  <div key={f.key}>
                    <label className={labelCls}>{f.label}</label>
                    <input type={f.type} className={inputCls} placeholder={f.placeholder}
                      value={payForm[f.key as keyof typeof payForm]}
                      onChange={e => setPayForm({...payForm, [f.key]: e.target.value})} required />
                  </div>
                ))}
                <div>
                  <label className={labelCls}>METHOD *</label>
                  <select className={inputCls + " appearance-none"} value={payForm.method}
                    onChange={e => setPayForm({...payForm, method: e.target.value})}>
                    <option value="PayPal">PayPal</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label className={labelCls}>NOTE</label>
                  <textarea className={`${inputCls} h-16 resize-none`} placeholder="Optional note"
                    value={payForm.note} onChange={e => setPayForm({...payForm, note: e.target.value})} />
                </div>
                {!capabilities.isPending && !paymentReportingAvailable && (
                  <p className="font-['JetBrains_Mono'] text-xs text-amber-200">PAYMENT REPORTING IS TEMPORARILY PAUSED. Do not submit transaction details until secure storage is connected.</p>
                )}
                {payMut.error && <p className="font-['JetBrains_Mono'] text-xs text-destructive">{payMut.error.message}</p>}
                <button onClick={() => payMut.mutate(payForm)} disabled={payMut.isPending || !paymentReportingAvailable || !payForm.name || !payForm.email || !payForm.amount || !payForm.orderId || !payForm.transactionId}
                  className="w-full py-3 bg-hud-deep text-white font-['JetBrains_Mono'] text-xs tracking-widest hover:bg-[#1f54e6] hover:shadow-[0_0_24px_rgb(56_198_255/0.45)] transition-colors disabled:opacity-50">
                  {payMut.isPending ? "PROCESSING..." : "REPORT PAYMENT →"}
                </button>
              </div>
            )}
          </div>
        </div>
          </div>
        </details>
      </section>

      <AskJay available={chatAvailable} checking={capabilities.isPending} onApply={handleAskJayApply} />

      {/* ── FOOTER ───────────────────────────────────────────────────────── */}
      <footer className="border-t border-white/10 py-12">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-8 mb-8">
            <div>
              <div className="font-['Bebas_Neue'] text-2xl text-white mb-3">JAYLEE FIT</div>
              <p className="font-['JetBrains_Mono'] text-xs text-white/40 leading-relaxed">High-performance coaching portal. Body recomposition, personal training, and hustle coaching orchestrated by the MAO operating system. Investment tiers — not subscriptions. By application only.</p>
            </div>
            <div>
              <div className="font-['JetBrains_Mono'] text-xs text-hud tracking-widest mb-3">CONTACT</div>
              <div className="font-['JetBrains_Mono'] text-xs text-white/50 space-y-1">
                <div>Jay.everydayhustleco@gmail.com</div>
                <div>PayPal: magicdeals.wholesale@gmail.com</div>
              </div>
            </div>
            <div>
              <div className="font-['JetBrains_Mono'] text-xs text-hud tracking-widest mb-3">SITEMAP</div>
              <div className="grid grid-cols-2 gap-1">
                {[["#services","WHAT YOU GET"],["#investment","PACKAGES"],["#coach-jay","COACH JAY"],["#apply","APPLY"],["#pay-invoice","PAY AN INVOICE"]].map(([href, label]) => (
                  <a key={href} href={href} className="font-['JetBrains_Mono'] text-[10px] text-white/30 hover:text-white/60 tracking-widest transition-colors">
                    {label}
                  </a>
                ))}
              </div>
            </div>
          </div>
          <div className="border-t border-white/5 pt-6">
            <p className="font-['JetBrains_Mono'] text-[10px] text-white/20 tracking-widest">
              © 2026 JAYLEE FIT · JAYLEE HUSTLE INDUSTRIES LLC — JAYLEEFIT.COM · MAO METHODOLOGY
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
