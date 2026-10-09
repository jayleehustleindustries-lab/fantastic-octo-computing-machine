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

Copy `.env.example` to `.env` only when connecting real services. Without `AIRTABLE_API_TOKEN` and `AIRTABLE_BASE_ID`, the application and payment-report buttons remain safely disabled; with them, each applicant becomes one record in the Airtable "Lead Pipeline" table, updated phase by phase, and each payment report becomes a "Needs review" record in "Payment Reports". Without `ANTHROPIC_API_KEY`, the "Ask Jay" chat shows "coming soon" and the browser-only plan builder appears instead; with it, Ask Jay (Claude Opus 5.5) answers questions, writes sample plans, and, when a visitor agrees, saves them to Lead Pipeline (Source "jayleefit.com Ask Jay chat") and hands them to the application with name and email filled in. Each visitor is capped at 30 messages and 3 lead saves an hour; conversations are kept only in the visitor's browser tab.

`GET /api/health` returns `{ ok, applicationIntake, paymentReporting, aiChat }` and is the Railway healthcheck.

## Deployment

Railway project `jayleefit` deploys from `jayleehustleindustries-lab/fantastic-octo-computing-machine`:

- `staging` branch → service `jayleefit-staging` (try changes here first)
- `jayleefit-launch` branch → service `jayleefit-web` (production, jayleefit.com)

GitHub Actions runs check, test and build on every push to either branch.

## Release gate

Before production deployment:

1. Set `AIRTABLE_API_TOKEN` and `AIRTABLE_BASE_ID` so applications reach Lead Pipeline and payment reports reach Payment Reports.
2. Set `ANTHROPIC_API_KEY` to switch on the Ask Jay assistant.
3. Set real package prices or intentionally keep `Contact for Pricing`.
4. Run check, tests, and build.
5. Verify desktop and mobile layouts, all four images, qualification submission, payment reporting, and the AI state in the deployed environment.

Payment reports are manual-review records. The website does not claim or perform automatic PayPal verification.
