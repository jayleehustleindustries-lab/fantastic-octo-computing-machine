# Reselling Automation Pipeline

Poshmark → Supabase (single source of truth) → Shopify, for Jaylee Hustle Industries.

This lives inside `fantastic-octo-computing-machine` on branch
`claude/poshmark-shopify-pipeline-yltj2g` because the GitHub App installed on
this account can only push to repos it's already been granted, not create new
ones (a 403 on repo creation confirmed this). Move it to its own repo whenever
you're ready: create the repo yourself on github.com, then either `git push`
this directory's history to it, or grant the app `Administration: write` and
ask Claude to create it directly.

## Status: scaffold + proven end-to-end path, not a running automation

What's real right now:
- Supabase project `jaylee-reselling-pipeline` (ref `plbsnlmhzcwebbafqvuj`,
  org `lroxqfemfsdqolerkqeg`) exists with the schema in `schema/`.
- Two real rows (from your Poshmark screenshot: the Keurig and the Athleta
  top) are inserted into `products` / `product_images`.
- One of them (`MD-KEURIG-01`) was pushed to your live Shopify store
  (`pbgrym-hd.myshopify.com`) as a **DRAFT** product with a real SKU and
  price attached — proving the Supabase → Shopify leg actually works.
  It is not published. Nothing is visible to customers. Review it in
  Shopify admin and publish, edit, or delete it yourself.

What's NOT real yet, on purpose:
- The Poshmark scraper (`scraper/poshmark_scraper.py`) is unrun. It needs
  your logged-in Poshmark session, which nobody should hand to a cloud
  session. Run it on your own machine, or hand `GROKBOT_HANDOFF.md` to
  another agent that can drive a browser with your session (see below).
- Product images are placeholder URLs (`example.com/...`) in the two seed
  rows — no real image URLs were available from a screenshot, only text.
  Don't push more products to Shopify until real image URLs (from Drive or
  wherever you land the photos) replace them, or you'll get broken images
  on live listings.
- Nothing runs on a schedule. This is manual-trigger scripts until you've
  reviewed the shape of the data and decided it's right.

## Self-correction built into the pipeline

Two failure modes matter most for a 367-item batch: a bad row poisoning the
whole run, and a network/rate-limit hiccup causing a duplicate or a silent
drop. Both are handled:

- **`etl/sheets_to_supabase.py` validates every row before it touches
  Supabase.** Missing required fields, non-numeric prices, or duplicate SKUs
  within the same CSV send that row to `<csv>_rejected.csv` with a reason —
  the rest of the batch still runs. A row that's valid but incomplete (no
  image, no condition) is inserted with `needs_review = true` and excluded
  from the Shopify push until you clear it — it's never silently dropped.
- **`shopify/push_to_shopify.py` is idempotent.** Before creating a product
  it checks Shopify for an existing one with that SKU — if a previous run
  crashed after creating the product but before recording
  `shopify_product_id` in Supabase, this run reconciles that product instead
  of creating a duplicate. Every Shopify API call retries with exponential
  backoff on rate limits/timeouts (`lib/retry.py`). A row that still fails
  after retries is marked `status = 'error'` with the reason in
  `error_message` — it won't retry-loop forever, but `--retry-errors`
  requeues it once you've investigated.

## Pipeline stages

1. **Ingest** — three ways to get the CSV, pick one:
   - `scraper/poshmark_scraper.py` — Playwright script, run **locally**:
     `python scraper/poshmark_scraper.py --closet-url <your closet> --output etl/inventory_seed.csv`.
     You log in interactively in the opened browser window; the script never
     stores or transmits your credentials.
   - `GROKBOT_HANDOFF.md` — a self-contained spec you can hand to Grok (or
     any other agent that can drive a browser under your logged-in session)
     to do the scraping for you. It defines the exact CSV schema this
     pipeline expects, so the output drops straight into step 2 with no
     reformatting.
   - Vendoo export — if you already cross-list through Vendoo, its export is
     cleaner and doesn't touch Poshmark's bot detection at all. Reshape it
     to match `etl/csv_template.csv`'s columns and skip the scraper entirely.

2. **Stage & clean** (`etl/sheets_to_supabase.py`) — reads a CSV (from the
   scraper, Vendoo, or hand-entry using `etl/csv_template.csv`), dedupes by
   SKU, and upserts into the `products` / `product_images` tables in
   Supabase. This is the "one true source" step — every later stage reads
   from Supabase, never from the CSV directly.

3. **Canonical store** — Supabase project `jaylee-reselling-pipeline`.
   `products.sku` is the join key; `product_images.sku` links images back
   to their row, ordered by `position`, with an optional `drive_file_id` if
   you're pulling images from a Google Drive folder by file ID rather than
   a public URL.

4. **Push to Shopify** (`shopify/push_to_shopify.py`) — reads `status =
   'ready'` rows from Supabase, creates them in Shopify **as DRAFT**
   (never auto-published), attaches price/SKU/images, then writes
   `shopify_product_id` + `synced_at` back to the Supabase row so nothing
   gets pushed twice. Publishing a draft to your live storefront is a
   manual step you take in Shopify admin — that's the human-in-the-loop
   checkpoint.

## Setup

```
cp shopify/.env.example shopify/.env
# fill in SUPABASE_URL, SUPABASE_SERVICE_KEY, SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN
pip install -r requirements.txt
```

Supabase connection details for this project:
- URL: `https://plbsnlmhzcwebbafqvuj.supabase.co`
- Use the **service role key** for the ETL/push scripts (server-side only,
  never commit it) — get it from Supabase dashboard → Project Settings →
  API. The publishable/anon key is fine for read-only tooling only.

## Explicitly out of scope for this pass

- The `Media-state-engine` repo and the unrelated video/TTS content
  currently sitting on this repo's `main` branch — different project,
  untouched here.
- A standalone storefront on Vercel — you confirmed Shopify is the
  actual storefront; Supabase is staging only. If that changes, this
  pipeline's output (clean Supabase rows) is exactly what a Vercel
  frontend would read from anyway.
- Auto-publishing anything, on any schedule, without you reviewing it
  first.
