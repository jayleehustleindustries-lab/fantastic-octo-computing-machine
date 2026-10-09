# JayLee Fit — MAO Methodology

The source for the JayLee Fit application-first coaching website. It includes the MAO offer, packages, Coach Jay profile, the four-phase application, the "Ask Jay" AI assistant, and manual payment-report intake for existing clients.

## Local setup

Requirements: Node.js 20+ and pnpm 10.4.1.

```bash
pnpm install --frozen-lockfile
pnpm check
pnpm test -- --pool=threads --poolOptions.threads.singleThread=true --maxConcurrency=1
pnpm build
PORT=4174 NODE_ENV=production node dist/index.js
```

Open `http://127.0.0.1:4174/`.

Copy `.env.example` to `.env` only when connecting real services. Without `AIRTABLE_API_TOKEN` and `AIRTABLE_BASE_ID`, the application and payment-report buttons remain safely disabled; with them, each applicant becomes one record in the Airtable "Lead Pipeline" table, updated phase by phase, and each payment report becomes a "Needs review" record in "Payment Reports". Without `ANTHROPIC_API_KEY`, the "Ask Jay" chat shows "coming soon" and the browser-only plan builder appears instead.

### Free tier: Ask Jay (Claude Haiku 5.5)

Ask Jay answers questions, writes a short free starter week, and, when a visitor agrees, saves them to Lead Pipeline and hands them to the right next step: the Remap form or the coaching application, with name and email filled in. Each visitor is capped at 30 messages and 3 lead saves an hour; conversations are kept only in the visitor's browser tab.

Social DM automations should link to the site with a `ref`, e.g. `https://jayleefit.com/?ref=ig` (also `tt`, `fb`, `yt`, `dm`). The ref is kept for the visit and recorded on every lead and order, e.g. Source "Instagram DM → jayleefit.com Ask Jay chat".

### Paid tier: Remap (Claude Opus 5.5)

`/remap` is the one product sold without an application. The visitor fills in an intake and sees their BMR (Mifflin-St Jeor) and daily burn (BMR × activity multiplier) live; the calorie target, macros and program unlock after payment. The numbers are computed in `shared/remap.ts`, never by the model:

- Calorie target: TDEE × 0.80 (fat loss), 0.90 (recomp), 1.10 (muscle gain) or 1.0 (performance), never below BMR or 1,200/1,500 kcal.
- Protein 0.9 g/lb (goal weight when BMI ≥ 30); fat at least 0.3 g/lb and 25% of calories; carbs the rest.
- Program length: beginner 8–12 weeks, intermediate 6–8, advanced 4–6.

Checkout is a Stripe Checkout Session. When Stripe confirms payment (webhook, or the program page checking the session), Claude Opus 5.5 builds the program from the intake, the fixed numbers, and what Airtable already knows about the buyer (Lead Pipeline notes, Clients goals, recent Progress Tracking). The result is validated (length range, phases covering every week, one entry per training day) and retried once if needed. The buyer's private page, `/remap/p/<token>`, shows it and saves as a PDF. Opus never runs for an unpaid order.

Each order is a row in the Airtable "Remap Orders" table. A delivered Remap also creates or updates the buyer's Clients record, adds a Nutrition Plan with the gram targets, and moves the lead to "Remap purchased". Expect roughly $0.30–0.60 of Claude usage per program.

`GET /api/health` returns `{ ok, applicationIntake, paymentReporting, aiChat, remapCheckout }` and is the Railway healthcheck.

## Deployment

Railway project `jayleefit` deploys from `jayleehustleindustries-lab/fantastic-octo-computing-machine`:

- `staging` branch → service `jayleefit-staging` (try changes here first)
- `jayleefit-launch` branch → service `jayleefit-web` (production, jayleefit.com)

GitHub Actions runs check, test and build on every push to either branch.

## Release gate

Before production deployment:

1. Set `AIRTABLE_API_TOKEN` and `AIRTABLE_BASE_ID` so applications reach Lead Pipeline and payment reports reach Payment Reports.
2. Set `ANTHROPIC_API_KEY` to switch on the Ask Jay assistant.
3. For Remap: set `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` and `REMAP_PRICE_CENTS`, and add the `/api/stripe/webhook` endpoint in Stripe. Run one purchase end to end with test keys on staging first.
4. Set real package prices or intentionally keep `Contact for Pricing`.
5. Run check, tests, and build.
6. Verify desktop and mobile layouts, all four images, qualification submission, payment reporting, and the AI state in the deployed environment.

Payment reports are manual-review records. The website does not claim or perform automatic PayPal verification.
