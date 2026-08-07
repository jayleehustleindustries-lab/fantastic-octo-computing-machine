import { useMemo, useState } from "react";
import rawProducts from "./products.json";

/* ------------------------------------------------------------------ *
 * Old Light — the EHC resale storefront, as a self-contained artifact.
 *
 * Every product below is a real row from the live EHC inventory
 * database (78 items). Nothing is mock data, and nothing claims a
 * capability the real operation doesn't have yet — the photo state in
 * particular is reported honestly, because storefront/BRAND-VOICE.md
 * makes "say the flaw first" the brand's first principle and a demo
 * that lies about its own readiness would break it on page one.
 * ------------------------------------------------------------------ */

type Product = {
  sku: string;
  name: string;
  brand: string;
  gender: string;
  type: string;
  size: string;
  color: string;
  condition: string;
  score: number;
  price: number;
  desc: string;
  status: string;
  available: boolean;
  location: string;
};

const PRODUCTS = rawProducts as Product[];

/** Same thresholds as phaseForScore() in storefront/lib/products.ts. */
function phaseForScore(score: number) {
  if (score <= 4) return { phase: "crescent", label: "Old Light" };
  if (score <= 6) return { phase: "half", label: "Half-Light" };
  if (score <= 8) return { phase: "gibbous", label: "Waxing" };
  return { phase: "full", label: "Full Illumination" };
}

const money = (n: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: n % 1 === 0 ? 0 : 2,
  }).format(n);

function MoonPhase({ score, condition }: { score: number; condition?: string }) {
  const { phase, label } = phaseForScore(score);
  return (
    <span className="inline-flex items-center gap-1.5" title={condition}>
      <span className={`moon phase-${phase}`} aria-hidden="true" />
      <span className="font-mono2 text-[10px] uppercase tracking-[0.18em] text-ash">{label}</span>
    </span>
  );
}

/* The marquee is the brand's most-repeated sentence, so it says what we
   do for the buyer rather than what they lose by waiting. Verbatim from
   the post-audit copy in storefront/components/marquee.tsx. */
const MARQUEE = [
  "EVERY PIECE ALREADY HAS A PAST",
  "GRADED BEFORE IT'S PRICED",
  "CLOSE CALLS ROUND DOWN, NEVER UP",
  "MEN'S & WOMEN'S",
  "ONE PRICE — NO BIDDING WAR",
];

function Marquee() {
  const track = [...MARQUEE, ...MARQUEE];
  return (
    <div className="overflow-hidden border-y border-line bg-gold text-[#0a0a14]">
      <div className="marquee-track flex w-max whitespace-nowrap py-1.5">
        {track.map((item, i) => (
          <span key={i} className="mx-4 font-mono2 text-[10px] font-bold uppercase tracking-[0.2em]">
            {item} <span className="mx-4">{"//"}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

const CARE_STEPS = [
  {
    step: "01",
    title: "Found one at a time",
    body: "Closets and thrift runs — no liquidation pallets, no bulk bins, no bots sniping the good finds before a human ever sees them.",
  },
  {
    step: "02",
    title: "Checked by hand",
    body: "Seams, zips, pilling, fading, measurements. Whatever we find goes in the description — the flaws especially.",
  },
  {
    step: "03",
    title: "Graded, then priced",
    body: "Condition gets called before the price does, and close calls round down, never up. The grade sets the price, not the other way around.",
  },
  {
    step: "04",
    title: "Sold at one price",
    body: "No bidding war, no countdown timer, no invented “original” price to discount from.",
  },
];

const PHASES = [
  { score: 10, body: "Mint. Every original detail still visible." },
  { score: 8, body: "Excellent. Barely worn, no real story yet." },
  { score: 6, body: "Good. Honest, visible wear — worn the way it was meant to be." },
  { score: 3, body: "Vintage character. What's left is what makes it worth keeping." },
];

function PhotoPlaceholder({ label = "Photo coming soon" }: { label?: string }) {
  return (
    <div className="halftone flex h-full w-full flex-col items-center justify-center gap-1 bg-panel">
      <span className="font-display text-xl tracking-wide text-ash/30">OLD LIGHT</span>
      <span className="font-mono2 text-[9px] uppercase tracking-[0.2em] text-ash/70">{label}</span>
    </div>
  );
}

function ProductCard({ p, onOpen }: { p: Product; onOpen: (p: Product) => void }) {
  return (
    <button
      onClick={() => onOpen(p)}
      className="group flex flex-col border border-line bg-void text-left transition-colors hover:border-[color:var(--gold)]"
    >
      <div className="aspect-[4/5] border-b border-line">
        <PhotoPlaceholder />
      </div>
      <div className="flex flex-1 flex-col gap-2 p-3">
        <div>
          <p className="font-mono2 text-[10px] uppercase tracking-[0.18em] text-ash">{p.brand}</p>
          <h3 className="mt-0.5 text-sm font-semibold leading-snug text-chalk">{p.name}</h3>
        </div>
        <div className="mt-auto flex items-center justify-between gap-2 pt-1">
          <MoonPhase score={p.score} condition={p.condition} />
          <span className="font-mono2 text-[10px] text-ash">{p.size || "—"}</span>
        </div>
        <p className="font-mono2 text-sm text-gold">{money(p.price)}</p>
      </div>
    </button>
  );
}

function Detail({ p, onClose }: { p: Product; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/80 p-4 sm:p-8"
      onClick={onClose}
    >
      <div
        className="my-auto w-full max-w-3xl border border-line bg-void"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-line px-4 py-2">
          <span className="font-mono2 text-[10px] uppercase tracking-[0.2em] text-ash">
            SKU {p.sku}
          </span>
          <button
            onClick={onClose}
            className="font-mono2 text-xs uppercase tracking-widest text-ash hover:text-gold"
          >
            Close ✕
          </button>
        </div>
        <div className="grid gap-6 p-4 sm:p-6 md:grid-cols-2">
          <div className="aspect-[4/5] border border-line">
            <PhotoPlaceholder />
          </div>
          <div className="flex flex-col gap-3">
            <div>
              <p className="font-mono2 text-[10px] uppercase tracking-[0.2em] text-ash">{p.brand}</p>
              <h2 className="font-display text-2xl leading-tight tracking-wide sm:text-3xl">
                {p.name}
              </h2>
            </div>
            <p className="font-mono2 text-2xl text-gold">{money(p.price)}</p>
            <div className="flex flex-wrap items-center gap-3">
              <MoonPhase score={p.score} condition={p.condition} />
              {p.size && (
                <span className="font-mono2 text-[10px] uppercase tracking-[0.18em] text-ash">
                  Size {p.size}
                </span>
              )}
              {p.color && (
                <span className="font-mono2 text-[10px] uppercase tracking-[0.18em] text-ash">
                  {p.color}
                </span>
              )}
            </div>
            {p.desc && <p className="text-sm leading-relaxed text-chalk/90">{p.desc}</p>}
            <p className="font-mono2 text-[10px] uppercase tracking-[0.18em] text-ash">
              One of one — so everything we know about it is on this page, flaws included.
            </p>
            <div className="mt-2 border border-line p-3">
              <p className="font-mono2 text-[10px] uppercase tracking-[0.2em] text-ember">
                Not yet listed
              </p>
              <p className="mt-1 text-xs leading-relaxed text-ash">
                Inventory status: <span className="text-chalk">{p.status || "Unlisted"}</span>
                {p.location && <> · Storage {p.location}</>}
                {!p.size && <> · needs measurements before it can go out</>}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [gender, setGender] = useState<string>("All");
  const [sort, setSort] = useState<string>("price-asc");
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState<Product | null>(null);

  const shown = useMemo(() => {
    let list = PRODUCTS.filter((p) => p.available);
    if (gender !== "All") list = list.filter((p) => p.gender === gender);
    if (query.trim()) {
      const q = query.toLowerCase();
      list = list.filter((p) =>
        [p.name, p.brand, p.type, p.color, p.sku].some((f) => (f || "").toLowerCase().includes(q))
      );
    }
    const sorted = [...list];
    if (sort === "price-asc") sorted.sort((a, b) => a.price - b.price);
    if (sort === "price-desc") sorted.sort((a, b) => b.price - a.price);
    if (sort === "condition") sorted.sort((a, b) => b.score - a.score);
    return sorted;
  }, [gender, sort, query]);

  const stats = useMemo(() => {
    const avail = PRODUCTS.filter((p) => p.available);
    return {
      total: PRODUCTS.length,
      value: avail.reduce((n, p) => n + p.price, 0),
      noSize: avail.filter((p) => !p.size).length,
      listed: PRODUCTS.filter((p) => /listed/i.test(p.status) && !/unlisted/i.test(p.status)).length,
    };
  }, []);

  return (
    <div className="min-h-screen bg-void">
      <header className="sticky top-0 z-40 bg-void">
        <Marquee />
        <div className="flex items-center justify-between border-b border-line px-4 py-3 sm:px-6">
          <span className="font-display text-2xl tracking-wide">
            OLD <span className="text-gold">LIGHT</span>
          </span>
          <span className="hidden font-mono2 text-[10px] uppercase tracking-[0.2em] text-ash sm:block">
            Secondhand, sold under old light
          </span>
        </div>
      </header>

      {/* Hero — post-audit copy. Scarcity appears once, as the reason for
          disclosure, never as a countdown. */}
      <section className="bg-noise border-b border-line px-4 py-16 sm:px-6 sm:py-24">
        <div className="mx-auto max-w-3xl">
          <p className="font-mono2 text-[10px] uppercase tracking-[0.3em] text-gold">
            Pre-owned. Graded by the moon. Checked by hand.
          </p>
          <h1 className="mt-4 font-display text-4xl leading-[1.05] tracking-wide sm:text-6xl">
            Every piece here already
            <br />
            <span className="text-gold">caught the light once.</span>
          </h1>
          <p className="mt-6 max-w-xl text-base leading-relaxed text-ash">
            Real menswear and womenswear, thrifted and checked by hand, priced at what it's
            actually worth — not what a resale app says it's worth. There's only one of each,
            which is exactly why we'd rather you buy it knowing everything than buy it fast.
          </p>
        </div>
      </section>

      {/* Catalog */}
      <section className="px-4 py-12 sm:px-6">
        <div className="mx-auto max-w-6xl">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h2 className="font-display text-3xl tracking-wide">THE CATALOG</h2>
              <p className="mt-1 text-sm text-ash">
                {shown.length} of {stats.total} real inventory items — no timer, no reason to rush.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search brand, item, SKU…"
                className="border border-line bg-transparent px-3 py-2 font-mono2 text-xs text-chalk placeholder:text-ash focus:border-[color:var(--gold)] focus:outline-none"
              />
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="border border-line bg-void px-3 py-2 font-mono2 text-xs uppercase tracking-widest text-chalk focus:border-[color:var(--gold)] focus:outline-none"
              >
                {["All", "Men", "Women", "Unisex"].map((g) => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value)}
                className="border border-line bg-void px-3 py-2 font-mono2 text-xs uppercase tracking-widest text-chalk focus:border-[color:var(--gold)] focus:outline-none"
              >
                <option value="price-asc">Price ↑</option>
                <option value="price-desc">Price ↓</option>
                <option value="condition">Condition</option>
              </select>
            </div>
          </div>

          <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {shown.map((p) => (
              <ProductCard key={p.sku} p={p} onOpen={setOpen} />
            ))}
          </div>
          {shown.length === 0 && (
            <p className="mt-12 text-center font-mono2 text-xs uppercase tracking-widest text-ash">
              Nothing matches that. Try a broader search.
            </p>
          )}
        </div>
      </section>

      {/* Care as process, not adjectives */}
      <section className="border-t border-line px-4 py-16 sm:px-6">
        <div className="mx-auto max-w-6xl">
          <h2 className="font-display text-3xl tracking-wide">HOW EVERY PIECE GETS HERE</h2>
          <p className="mt-2 max-w-2xl text-sm text-ash">
            Secondhand only works if someone actually looked at the thing first. Here's what that
            looks like on our end, every time.
          </p>
          <div className="mt-8 grid gap-px border border-line bg-[color:var(--line)] sm:grid-cols-2 lg:grid-cols-4">
            {CARE_STEPS.map((s) => (
              <div key={s.step} className="flex flex-col gap-2 bg-void p-5">
                <span className="font-mono2 text-[10px] tracking-[0.2em] text-gold">{s.step}</span>
                <h3 className="font-display text-xl tracking-wide">{s.title}</h3>
                <p className="text-sm leading-relaxed text-ash">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Grading */}
      <section className="border-t border-line px-4 py-16 sm:px-6">
        <div className="mx-auto max-w-3xl">
          <h2 className="font-display text-3xl tracking-wide">CONDITION, AS PHASES</h2>
          <p className="mt-2 text-sm text-ash">
            A grading scale that means something twice — how much of the moon you can see, and how
            much of a piece's first life is still visible on it.
          </p>
          <div className="mt-6 flex flex-col divide-y border-y" style={{ borderColor: "var(--line)" }}>
            {PHASES.map((p) => (
              <div key={p.score} className="flex items-center gap-4 py-3">
                <MoonPhase score={p.score} />
                <p className="text-sm text-ash">{p.body}</p>
              </div>
            ))}
          </div>
          <p className="mt-5 text-sm leading-relaxed text-chalk/90">
            We grade before we price, and when it's a close call we round down rather than up. If
            we get a grade wrong, that's ours to make right — not yours to live with.
          </p>
        </div>
      </section>

      {/* The honest status panel. This is a preview of a shop that isn't
          open yet, and saying so is cheaper than being found out. */}
      <section className="border-t border-line bg-panel px-4 py-12 sm:px-6">
        <div className="mx-auto max-w-3xl">
          <p className="font-mono2 text-[10px] uppercase tracking-[0.2em] text-gold">
            Where this actually stands
          </p>
          <h2 className="mt-2 font-display text-2xl tracking-wide">
            This is a preview, not an open shop.
          </h2>
          <div className="mt-5 grid gap-px border bg-[color:var(--line)] sm:grid-cols-4" style={{ borderColor: "var(--line)" }}>
            {[
              { n: String(stats.total), l: "real items" },
              { n: money(stats.value), l: "catalog value" },
              { n: "0", l: "photos matched" },
              { n: String(stats.listed), l: "live elsewhere" },
            ].map((s) => (
              <div key={s.l} className="bg-panel p-4">
                <p className="font-mono2 text-xl text-gold">{s.n}</p>
                <p className="font-mono2 text-[10px] uppercase tracking-[0.18em] text-ash">{s.l}</p>
              </div>
            ))}
          </div>
          <ul className="mt-5 flex flex-col gap-2 text-sm text-ash">
            <li>
              — Every product above is a real row from the live inventory database. The prices,
              grades and descriptions are the real ones.
            </li>
            <li>
              — <span className="text-chalk">Every tile shows a placeholder</span> because no photo
              has been matched to a SKU yet. 69 edited photos are in the repo waiting; nothing in a
              phone filename says which garment it is, so that match is a human call.
            </li>
            <li>
              — <span className="text-chalk">{stats.noSize} items still need measurements</span>{" "}
              before they can be listed anywhere.
            </li>
            <li>
              — Checkout isn't wired in this preview. The real storefront runs Stripe and re-prices
              every cart item server-side.
            </li>
          </ul>
        </div>
      </section>

      <footer className="border-t border-line px-4 py-10 text-center sm:px-6">
        <p className="font-display text-xl tracking-wide">
          OLD <span className="text-gold">LIGHT</span>
        </p>
        <p className="mx-auto mt-2 max-w-md font-mono2 text-[10px] leading-relaxed text-ash">
          Secondhand, sold under old light. Men's &amp; women's clothing checked by hand, graded by
          the moon, and priced like it already lived a life.
        </p>
      </footer>

      {open && <Detail p={open} onClose={() => setOpen(null)} />}
    </div>
  );
}
