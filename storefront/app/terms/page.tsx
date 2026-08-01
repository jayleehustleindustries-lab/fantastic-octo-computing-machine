export const metadata = {
  title: "Terms of Service — Old Light",
};

export default function TermsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <p className="font-mono text-xs uppercase tracking-widest text-gold">Policies</p>
      <h1 className="mt-2 font-display text-4xl font-semibold tracking-wide sm:text-5xl">
        TERMS OF SERVICE
      </h1>

      <div className="mt-8 flex flex-col gap-8 font-sans text-sm leading-relaxed text-chalk/90">
        <section>
          <h2 className="font-display text-xl font-semibold tracking-wide text-chalk">Pre-owned condition</h2>
          <p className="mt-2">
            Everything sold here is secondhand. Listed condition (Full
            Illumination, Waxing, Half-Light, Old Light) reflects our honest
            grading at the time of listing, not new-item condition. Normal
            signs of prior wear consistent with that grade aren&apos;t defects.
          </p>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold tracking-wide text-chalk">One-off inventory</h2>
          <p className="mt-2">
            Every item is a single unit. Prices and availability shown at the
            time you add something to your cart aren&apos;t locked in until
            checkout completes — on rare occasions an item may sell out
            between browsing and payment; if that happens you won&apos;t be
            charged for it, and we&apos;ll let you know.
          </p>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold tracking-wide text-chalk">Payments</h2>
          <p className="mt-2">
            All prices are in USD. Payment is processed securely by Stripe.
            By completing checkout you authorize the charge for your order
            total, including shipping.
          </p>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold tracking-wide text-chalk">Limitation of liability</h2>
          <p className="mt-2">
            We&apos;re a small, hands-on resale operation, not a large retailer.
            Our liability for any order is limited to the amount you paid for
            it. See our{" "}
            <a href="/shipping-returns" className="text-gold hover:underline">
              Shipping &amp; Returns
            </a>{" "}
            page for how we make things right if something arrives wrong.
          </p>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold tracking-wide text-chalk">Changes</h2>
          <p className="mt-2">
            We may update these terms as the shop grows. The version posted
            here is always the current one.
          </p>
        </section>
      </div>
    </div>
  );
}
