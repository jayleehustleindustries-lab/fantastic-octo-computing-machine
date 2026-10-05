# JayLee Fit — MAO Methodology

The source for the JayLee Fit application-first coaching website. It includes the MAO methodology, qualification flow, training preview, AI blueprint interface, Coach Jay profile, campaign gallery, and manual payment-report intake.

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

Copy `.env.example` to `.env` only when connecting real services. Without `AIRTABLE_API_TOKEN` and `AIRTABLE_BASE_ID`, the application and payment-report buttons remain safely disabled; with them, each applicant becomes one record in the Airtable "Lead Pipeline" table, updated phase by phase, and each payment report becomes a "Needs review" record in "Payment Reports". Without `ANTHROPIC_API_KEY`, the live AI generator remains disabled while the on-page rapid diagnostic still works; with it, each visitor can generate up to 5 sample plans an hour.

`GET /api/health` returns `{ ok, applicationIntake, paymentReporting, aiBlueprints }` and is the Railway healthcheck.

## Deployment

Railway project `jayleefit` deploys from `jayleehustleindustries-lab/fantastic-octo-computing-machine`:

- `staging` branch → service `jayleefit-staging` (try changes here first)
- `jayleefit-launch` branch → service `jayleefit-web` (production, jayleefit.com)

GitHub Actions runs check, test and build on every push to either branch.

## Release gate

Before production deployment:

1. Set `AIRTABLE_API_TOKEN` and `AIRTABLE_BASE_ID` so applications reach Lead Pipeline and payment reports reach Payment Reports.
2. Set `ANTHROPIC_API_KEY` only if the AI blueprint generator should be live.
3. Set real package prices or intentionally keep `Contact for Pricing`.
4. Run check, tests, and build.
5. Verify desktop and mobile layouts, all four images, qualification submission, payment reporting, and the AI state in the deployed environment.

Payment reports are manual-review records. The website does not claim or perform automatic PayPal verification.
