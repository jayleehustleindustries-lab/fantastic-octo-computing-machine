export default function AboutPage() {
  const showCrossPromo = process.env.NEXT_PUBLIC_SHOW_CROSS_PROMO !== "false";
  const jayLeeFitUrl = process.env.NEXT_PUBLIC_JAYLEEFIT_URL || "https://www.jayleefit.com";
  const jayLeeFitLabel = process.env.NEXT_PUBLIC_JAYLEEFIT_LABEL || "JayLeeFit Coaching";

  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <p className="font-mono text-xs uppercase tracking-widest text-gold">About</p>
      <h1 className="mt-2 font-display text-4xl font-semibold tracking-wide sm:text-5xl">
        EVERYTHING HERE IS OLD LIGHT.
      </h1>

      <div className="mt-8 flex flex-col gap-6 font-sans text-base leading-relaxed text-chalk/90">
        <p>
          Look up on a clear night and nothing you&apos;re looking at is really there
          anymore — it&apos;s light that left years, centuries, sometimes longer ago,
          only now arriving. Astronomers call it old light. It&apos;s the same trick a
          good secondhand find pulls off: someone else already spent the years
          breaking it in, softening the cotton, giving it a crease that only comes
          from being worn and loved — and it still arrives at you as if freshly lit.
        </p>
        <p>
          We didn&apos;t make anything new here. One closet, one thrift run at a time —
          no warehouse, no liquidation pallets, no bots sniping every good find before
          you see it. Every item gets graded honestly, photographed as-is, and priced
          below what you&apos;d pay chasing the same piece through a resale app&apos;s
          bidding war. One price. No games.
        </p>
        <p>
          Old Light doesn&apos;t sell new. It sells things that already caught the
          light once, and are ready to travel again.
        </p>
      </div>

      {showCrossPromo && (
        <div className="mt-12 border border-line p-6">
          <p className="font-mono text-xs uppercase tracking-widest text-ash">
            From the same corner as
          </p>
          <a
            href={jayLeeFitUrl}
            className="mt-2 inline-block font-display text-2xl font-semibold tracking-wide text-chalk hover:text-gold"
          >
            {jayLeeFitLabel} →
          </a>
          <p className="mt-2 max-w-md font-sans text-sm text-ash">
            If you&apos;re here for the fits, you might also be into the fitness
            coaching side of the house.
          </p>
        </div>
      )}
    </div>
  );
}
