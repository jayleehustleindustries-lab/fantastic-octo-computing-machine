import type { ReactNode } from "react";

type Status = "online" | "offline" | "standby";

const STATUS_LABEL: Record<Status, string> = {
  online: "ONLINE",
  offline: "OFFLINE",
  standby: "STANDBY",
};

/**
 * HUD frame for an interactive block: corner brackets, a header strip with a
 * module code, and a status light. Pass `status` from site capabilities so the
 * light tells the truth about whether the feature works right now.
 */
export function AgentModule({
  code,
  name,
  status = "standby",
  label,
  children,
  className = "",
  bodyClassName = "",
}: {
  code: string;
  name: string;
  status?: Status;
  /** Overrides the status text, e.g. "LOCKED" or "PREVIEW". */
  label?: string;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  const led =
    status === "online"
      ? "bg-hud shadow-[0_0_10px_rgb(56_198_255/0.9)] hud-pulse"
      : status === "offline"
        ? "bg-[#4b5563]"
        : "bg-hud/50";
  return (
    <div className={`relative border border-white/[0.12] bg-[#0e1218]/80 backdrop-blur-sm print:bg-white print:border-black/30 print:backdrop-blur-none print:break-inside-avoid-page ${className}`}>
      <Corner className="left-0 top-0" />
      <Corner className="right-0 top-0 rotate-90" />
      <Corner className="right-0 bottom-0 rotate-180" />
      <Corner className="left-0 bottom-0 -rotate-90" />
      <div className="relative flex items-center justify-between gap-3 overflow-hidden border-b border-white/[0.08] bg-[#161b23]/70 px-4 py-2 print:bg-white print:border-black/30">
        <div aria-hidden="true" className="hud-sweep print:hidden absolute inset-y-0 left-0 w-1/4 bg-gradient-to-r from-transparent via-hud/15 to-transparent" />
        <span className="relative font-['Chakra_Petch'] text-[11px] font-semibold tracking-[0.2em] text-white/80 print:text-black">
          <span className="text-hud">{code}</span> // {name}
        </span>
        <span className="relative flex items-center gap-2 font-['JetBrains_Mono'] text-[10px] tracking-widest text-white/50">
          <span className={`h-1.5 w-1.5 rounded-full ${led}`} />
          {label ?? STATUS_LABEL[status]}
        </span>
      </div>
      <div className={`relative ${bodyClassName}`}>{children}</div>
    </div>
  );
}

function Corner({ className }: { className: string }) {
  return (
    <span
      aria-hidden="true"
      className={`pointer-events-none absolute z-10 h-3 w-3 border-l-2 border-t-2 border-hud ${className}`}
      style={{ margin: -1 }}
    />
  );
}
