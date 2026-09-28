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

Copy `.env.example` to `.env` only when connecting real services. Without `AIRTABLE_API_TOKEN` and `AIRTABLE_BASE_ID`, the application buttons remain safely disabled; with them, each applicant becomes one record in the Airtable "Lead Pipeline" table, updated phase by phase. Without `DATABASE_URL`, the payment-report form remains disabled. Without both Forge values, the live AI generator remains disabled while the on-page rapid diagnostic still works.

## Release gate

Before production deployment:

1. Set `AIRTABLE_API_TOKEN` and `AIRTABLE_BASE_ID` so applications reach Lead Pipeline. (A MySQL database is only needed if payment reports should be accepted online.)
2. Configure the Forge AI values only if the AI blueprint generator should be live.
3. Set real package prices or intentionally keep `Contact for Pricing`.
4. Run check, tests, and build.
5. Verify desktop and mobile layouts, all four images, qualification submission, payment reporting, and the AI state in the deployed environment.

Payment reports are manual-review records. The website does not claim or perform automatic PayPal verification.
