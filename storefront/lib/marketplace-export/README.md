# Facebook Marketplace listing-copy export

Generates ready-to-copy-paste Facebook Marketplace listing content
(title/price/category/condition/description) from the real EHC Inventory
Log. There's no Facebook Marketplace API for individual sellers, and
automating posts there violates their ToS — this doesn't post anything,
it just makes manual posting fast.

## Refresh on demand, not on a schedule

Resale inventory doesn't change fast enough to justify a proactive
schedule, and a cron/Routine setup adds a moving part (staleness, silent
failures) for something only needed right before a posting session. Just
ask for a fresh export when you're about to post — it's a one-minute
regeneration from the live sheet, not a background job.

## The refresh procedure

1. **Download the live sheet via the Google Drive connector** — not a
   direct fetch to `docs.google.com`. This sandbox's network policy
   blocks that host directly; `download_file_content` with the EHC
   Inventory Log's Sheet ID (the same one `../products.ts` defaults to)
   and `exportMimeType: text/csv` is the working path.
2. **Decode the result** — the Drive connector returns the CSV content
   base64-encoded; decode it to a local `.csv` file.
3. **Run the generator:**
   ```
   npx tsx lib/marketplace-export/generate.ts <output.md> --csv=<local.csv>
   ```
4. **Deliver the resulting Markdown file** — one block per available
   item, ready to paste into Facebook's own posting form. Photos still
   need manual upload; there's no URL-based photo import on Facebook.

If sandbox network policy ever allows `docs.google.com` directly, step 1
can be skipped — `generate.ts` also fetches the live Sheet CSV export
directly when no `--csv=` flag is given.
