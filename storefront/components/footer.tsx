import Link from "next/link";
import CrossPromoBanner from "./cross-promo-banner";

export default function Footer() {
  return (
    <footer className="border-t border-line">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-12 sm:grid-cols-3 sm:px-6">
        <div>
          <p className="font-display text-xl font-semibold tracking-wide text-chalk">
            OLD <span className="text-gold">LIGHT</span>
          </p>
          {/* "Authenticated" was removed deliberately — it names a specific
              counterfeit-verification service we don't perform. See the
              unearned-claims section of BRAND-VOICE.md. */}
          <p className="mt-2 max-w-xs font-mono text-xs text-ash">
            Secondhand, sold under old light. Men&apos;s &amp; women&apos;s clothing
            checked by hand, graded by the moon, and priced like it already lived
            a life.
          </p>
        </div>

        <div className="font-mono text-xs uppercase tracking-widest">
          <p className="mb-3 text-ash">Shop</p>
          <ul className="flex flex-col gap-2">
            <li><Link href="/shop?category=Men" className="hover:text-gold">Men</Link></li>
            <li><Link href="/shop?category=Women" className="hover:text-gold">Women</Link></li>
            <li><Link href="/shop?sale=1" className="hover:text-gold">Sale</Link></li>
            <li><Link href="/about" className="hover:text-gold">About</Link></li>
          </ul>
        </div>

        <div className="font-mono text-xs uppercase tracking-widest">
          <p className="mb-3 text-ash">Get the drops first</p>
          <form className="flex gap-2">
            <input
              type="email"
              placeholder="email@domain.com"
              className="w-full border border-line bg-transparent px-3 py-2 text-chalk placeholder:text-ash focus:border-gold focus:outline-none"
            />
            <button
              type="submit"
              className="shrink-0 bg-gold px-3 py-2 font-bold text-void"
            >
              Join
            </button>
          </form>
        </div>
      </div>

      <CrossPromoBanner />

      <div className="flex flex-col items-center gap-2 px-4 py-4 text-center font-mono text-[10px] uppercase tracking-widest text-ash sm:px-6">
        <div className="flex gap-4">
          <Link href="/shipping-returns" className="hover:text-gold">Shipping &amp; Returns</Link>
          <Link href="/privacy" className="hover:text-gold">Privacy</Link>
          <Link href="/terms" className="hover:text-gold">Terms</Link>
        </div>
        <p>© {new Date().getFullYear()} Old Light. Every piece pre-owned, graded &amp; checked by hand.</p>
      </div>
    </footer>
  );
}
