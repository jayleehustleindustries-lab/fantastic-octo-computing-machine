export const metadata = {
  title: "Shipping & Returns — Old Light",
};

export default function ShippingReturnsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <p className="font-mono text-xs uppercase tracking-widest text-gold">Policies</p>
      <h1 className="mt-2 font-display text-4xl font-semibold tracking-wide sm:text-5xl">
        SHIPPING &amp; RETURNS
      </h1>

      <div className="mt-8 flex flex-col gap-8 font-sans text-sm leading-relaxed text-chalk/90">
        <section>
          <h2 className="font-display text-xl font-semibold tracking-wide text-chalk">Shipping</h2>
          <p className="mt-2">
            Orders ship within 1-3 business days of purchase, via USPS or the
            best available carrier for the package. Standard shipping is a
            flat $6.99 within the US and Canada, added at checkout. You&apos;ll
            get a tracking link by email once your order ships.
          </p>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold tracking-wide text-chalk">Returns &amp; exchanges</h2>
          <p className="mt-2">
            Every piece here is one-of-one — once it&apos;s sold, there isn&apos;t a
            second one to send as a replacement or exchange. Because of that,
            all sales are final except for one case:
          </p>
          <p className="mt-2">
            <strong className="text-chalk">Item not as described.</strong> If
            what arrives doesn&apos;t match the condition, size, or details
            listed on the product page, email us within 7 days of delivery
            with photos of the issue. We&apos;ll work out a refund or partial
            refund — whichever&apos;s fair for what actually went wrong.
          </p>
          <p className="mt-2">
            We grade every item honestly before it&apos;s listed, so this
            should be rare — but if we get a grading call wrong, that&apos;s on
            us to make right, not you.
          </p>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold tracking-wide text-chalk">Damaged in transit</h2>
          <p className="mt-2">
            If a package arrives visibly damaged, keep the packaging, photograph
            it, and reach out right away — we&apos;ll sort a replacement or
            refund with the carrier claim on our end, not yours.
          </p>
        </section>
      </div>
    </div>
  );
}
