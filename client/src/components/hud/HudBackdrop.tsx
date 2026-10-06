/** Fixed page backdrop: faint blue grid, vignette, and one slow scan line. */
export function HudBackdrop() {
  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      <div className="absolute inset-0 hud-grid" />
      <div
        className="absolute inset-0"
        style={{ background: "radial-gradient(ellipse at 50% 30%, transparent 0%, rgb(5 7 11 / 0.55) 55%, #05070b 100%)" }}
      />
      <div className="hud-scan absolute left-0 right-0 top-0 h-24 bg-gradient-to-b from-transparent via-hud/[0.05] to-transparent" />
    </div>
  );
}
