import { useEffect, useState } from "react";

const LINE = "INITIALIZING MAO PROTOCOL… READY";

/** Types the boot line once. Shows it complete for reduced-motion visitors. */
export function BootLine() {
  const [shown, setShown] = useState(LINE.length);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    setShown(0);
    let i = 0;
    const timer = window.setInterval(() => {
      i += 1;
      setShown(i);
      if (i >= LINE.length) window.clearInterval(timer);
    }, 38);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="font-['JetBrains_Mono'] text-[11px] tracking-widest text-hud" aria-label={LINE}>
      <span aria-hidden="true">
        {"> "}
        {LINE.slice(0, shown)}
        <span className="hud-blink">_</span>
      </span>
    </div>
  );
}
