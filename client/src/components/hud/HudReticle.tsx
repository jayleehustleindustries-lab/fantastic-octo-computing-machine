import { useEffect, useState } from "react";

const C = 200; // viewBox centre

function arc(r: number, startDeg: number, endDeg: number) {
  const rad = (d: number) => ((d - 90) * Math.PI) / 180;
  const x1 = C + r * Math.cos(rad(startDeg));
  const y1 = C + r * Math.sin(rad(startDeg));
  const x2 = C + r * Math.cos(rad(endDeg));
  const y2 = C + r * Math.sin(rad(endDeg));
  const large = endDeg - startDeg > 180 ? 1 : 0;
  return `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`;
}

const TICKS = Array.from({ length: 72 }, (_, i) => i * 5);

function useClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const t = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(t);
  }, []);
  return now.toLocaleTimeString([], { hour12: false });
}

/**
 * Hero centrepiece: concentric rings with ticks, counter-rotating arc segments
 * and a pulsing core. Readouts are honest labels, not invented stats.
 */
export function HudReticle({ className = "" }: { className?: string }) {
  const clock = useClock();
  return (
    <div className={`relative aspect-square ${className}`}>
      <svg viewBox="0 0 400 400" className="h-full w-full" aria-hidden="true">
        <defs>
          <radialGradient id="hud-core" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#7dd9ff" stopOpacity="0.95" />
            <stop offset="45%" stopColor="#38c6ff" stopOpacity="0.45" />
            <stop offset="100%" stopColor="#2563ff" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Outer ring + ticks */}
        <circle cx={C} cy={C} r={190} fill="none" stroke="#38c6ff" strokeOpacity="0.18" />
        <g className="hud-spin-rev">
          {TICKS.map(d => {
            const major = d % 30 === 0;
            const r1 = 182;
            const r2 = major ? 168 : 175;
            const a = ((d - 90) * Math.PI) / 180;
            return (
              <line
                key={d}
                x1={C + r1 * Math.cos(a)} y1={C + r1 * Math.sin(a)}
                x2={C + r2 * Math.cos(a)} y2={C + r2 * Math.sin(a)}
                stroke="#38c6ff" strokeOpacity={major ? 0.8 : 0.3} strokeWidth={major ? 2 : 1}
              />
            );
          })}
        </g>

        {/* Rotating arc segments */}
        <g className="hud-spin">
          <path d={arc(150, 0, 70)} fill="none" stroke="#38c6ff" strokeWidth="3" strokeLinecap="round" />
          <path d={arc(150, 120, 160)} fill="none" stroke="#38c6ff" strokeOpacity="0.5" strokeWidth="3" />
          <path d={arc(150, 200, 300)} fill="none" stroke="#2563ff" strokeWidth="3" />
        </g>
        <g className="hud-spin-rev">
          <circle cx={C} cy={C} r={126} fill="none" stroke="#8b95a5" strokeOpacity="0.35" strokeDasharray="2 6" />
          <path d={arc(118, 30, 110)} fill="none" stroke="#38c6ff" strokeOpacity="0.7" strokeWidth="1.5" />
          <path d={arc(118, 210, 250)} fill="none" stroke="#38c6ff" strokeOpacity="0.7" strokeWidth="1.5" />
        </g>
        <g className="hud-spin-fast">
          <path d={arc(88, 0, 40)} fill="none" stroke="#7dd9ff" strokeWidth="2" />
          <path d={arc(88, 180, 220)} fill="none" stroke="#7dd9ff" strokeWidth="2" />
        </g>
        <circle cx={C} cy={C} r={74} fill="none" stroke="#38c6ff" strokeOpacity="0.25" />

        {/* Crosshair */}
        <g stroke="#38c6ff" strokeOpacity="0.35">
          <line x1={C} y1={20} x2={C} y2={60} />
          <line x1={C} y1={340} x2={C} y2={380} />
          <line x1={20} y1={C} x2={60} y2={C} />
          <line x1={340} y1={C} x2={380} y2={C} />
        </g>

        {/* Core */}
        <circle cx={C} cy={C} r={58} fill="url(#hud-core)" className="hud-pulse" />
        <circle cx={C} cy={C} r={22} fill="#05070b" stroke="#7dd9ff" strokeWidth="1.5" />
        <text x={C} y={C + 5} textAnchor="middle" fill="#e8f1fa" fontSize="14" letterSpacing="2"
          style={{ fontFamily: "'Chakra Petch', sans-serif", fontWeight: 600 }}>
          MAO
        </text>
      </svg>

      {/* Readouts */}
      <div className="pointer-events-none absolute left-0 top-[6%] font-['JetBrains_Mono'] text-[10px] leading-relaxed tracking-widest text-white/60">
        <div className="flex items-center gap-2 text-hud">
          <span className="h-1.5 w-1.5 rounded-full bg-hud shadow-[0_0_8px_rgb(56_198_255)] hud-pulse" />
          MAO SYSTEM · ONLINE
        </div>
      </div>
      <div className="pointer-events-none absolute right-0 top-[6%] text-right font-['JetBrains_Mono'] text-[10px] tracking-widest text-white/60">
        <div>LOCAL TIME</div>
        <div className="text-hud tabular-nums">{clock}</div>
      </div>
      <div className="pointer-events-none absolute -bottom-[2%] left-0 font-['JetBrains_Mono'] text-[10px] tracking-widest text-white/60">
        OPERATORS ADMITTED:<br />
        <span className="text-hud">BY APPLICATION</span>
      </div>
      <div className="pointer-events-none absolute -bottom-[2%] right-0 text-right font-['JetBrains_Mono'] text-[10px] tracking-widest text-white/60">
        PROTOCOL<br />
        <span className="text-hud">CONDITION · FOCUS<br />ACCOUNTABILITY</span>
      </div>
    </div>
  );
}
