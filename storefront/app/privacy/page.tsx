export const metadata = {
  title: "Privacy Policy — Old Light",
};

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <p className="font-mono text-xs uppercase tracking-widest text-gold">Policies</p>
      <h1 className="mt-2 font-display text-4xl font-semibold tracking-wide sm:text-5xl">
        PRIVACY POLICY
      </h1>

      <div className="mt-8 flex flex-col gap-8 font-sans text-sm leading-relaxed text-chalk/90">
        <section>
          <h2 className="font-display text-xl font-semibold tracking-wide text-chalk">What we collect</h2>
          <p className="mt-2">
            When you check out, payment, name, email, and shipping address are
            collected directly by Stripe, our payment processor — we don&apos;t
            see or store your card details ourselves. If you sign up for
            drop notifications in the footer, we keep your email for that
            purpose only.
          </p>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold tracking-wide text-chalk">How it&apos;s used</h2>
          <p className="mt-2">
            Order information is used to fulfill and ship your purchase, and
            to follow up if there&apos;s a problem with it. We do not sell,
            rent, or share your information with anyone outside the services
            that make the store run (Stripe for payments, our hosting and
            analytics providers for keeping the site online).
          </p>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold tracking-wide text-chalk">Cookies &amp; analytics</h2>
          <p className="mt-2">
            The site uses basic hosting-level analytics to understand traffic
            and keep pages fast. It doesn&apos;t track you across other sites
            or sell that data to advertisers.
          </p>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold tracking-wide text-chalk">Your options</h2>
          <p className="mt-2">
            Email us any time to ask what we have on file, to correct it, or
            to have it deleted (aside from records Stripe or tax law require
            us to keep for completed orders).
          </p>
        </section>
      </div>
    </div>
  );
}
