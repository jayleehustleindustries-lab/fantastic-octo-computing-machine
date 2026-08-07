# Old Light — custom resale storefront

A fully custom-designed (not a Shopify theme) storefront for reselling
pre-owned men's and women's apparel. Celestial/night-sky aesthetic: near-black
+ warm gold, an elegant serif for names, a moon-phase condition grading
system, and one-off inventory framed around care rather than urgency — see
`BRAND-VOICE.md` for why, and for the rules any new copy has to pass.

Brand: **Old Light** — *"Secondhand, sold under old light."* The core idea:
starlight you see tonight already left its source years ago, arriving
"used" but still lit — the same trick a good secondhand find pulls off.

## Stack

- Next.js (App Router) + TypeScript + Tailwind CSS v4
- Inventory read from a **Google Sheet** (no API key needed — CSV export
  endpoint), with a local sample catalog as fallback
- **Stripe Checkout** for real payments (server re-prices every item at
  checkout time, so the client cart can never be tampered with)
- No database — the sheet is the single source of truth, same pattern as the
  Airtable-based JayLeeFit client data layer elsewhere in this repo

## Getting started

```bash
cd storefront
npm install
cp .env.example .env.local   # then fill in the values below
npm run dev
```

Without any env vars set, the site runs against the built-in sample catalog
in `lib/sample-products.ts` — good enough to see the full design and flow
immediately.

## Connecting your Google Sheet

1. In your existing inventory spreadsheet, make (or rename) a tab with these
   column headers in row 1 — order doesn't matter, extra columns are ignored:

   | Column | Required | Notes |
   |---|---|---|
   | `Name` | yes | Product title |
   | `Brand` | | e.g. `Carhartt` |
   | `Category` | | `Men` / `Women` / `Unisex` (anything starting with M/W maps automatically) |
   | `Type` | | e.g. `Jacket`, `Denim`, `Sneakers` |
   | `Size` | | e.g. `L`, `W28`, `US 9` |
   | `Condition` | | e.g. `9/10 — Like New` |
   | `Original Price` | | retail price, plain number |
   | `Price` | yes | your resale price, plain number |
   | `Description` | | shown on the product page |
   | `Images` | | one or more photo URLs, separated by `\|` if more than one |
   | `Tags` | | e.g. `STEAL\|RARE\|LAST ONE`, also `\|`-separated |
   | `In Stock` | | `Y`/`N` — flip to `N` once something sells |
   | `SKU` | | optional; auto-generated if left blank |
   | `Slug` | | optional; auto-generated from the name if left blank |
   | `Timestamp` / `Date Added` | | when the row was logged — used to compute `daysInInventory` (age tracking, not shown on the site UI yet) |

   **Already running an "EHC Inventory Log"-style sheet?** The mapping also
   recognizes that layout directly, no renaming needed: `Permanent SKU`,
   `Item Name`/`SEO Listing Title` (title wins when present), `Department`
   (used as gender/category, with `Category` then read as garment type —
   the reverse of the layout above), `Realistic Sold Value` (used as price,
   `$`-formatted values parse fine), `SEO Listing Description`, `Style Tag
   1/2/3` (used as tags when there's no `Tags` column). There's no `In
   Stock` column in that layout — availability is inferred from
   `Inventory Status`/`Condition` instead (anything not explicitly
   donated/liquidated/passed-on/removed counts as available). That layout's
   own `Timestamp` column (when the row was logged) is read directly for
   `daysInInventory` — no extra setup needed. Verified against a real
   71-row export — see `lib/verify-ehc-mapping.ts`.

   That sheet has no usable photo column, so items render the "Photo coming
   soon" placeholder until photos are added — see **Product photos** below
   for the way around that.

2. Share the sheet: **Share → Anyone with the link → Viewer**.
3. Copy the ID out of the sheet's URL (`.../d/THIS-PART/edit`) into
   `GOOGLE_SHEET_ID`, and set `GOOGLE_SHEET_NAME` to the tab name.

The storefront re-fetches the sheet on a 60-second cache, so editing the
sheet is the entire "adding inventory" workflow — no redeploys needed.

> **Not automated yet:** marking an item sold after checkout is manual today
> (flip `In Stock` to `N`). Automating that write requires a Google service
> account with *edit* access to the sheet — the read-only CSV export used
> here can't write. The Stripe webhook (`app/api/checkout/webhook/route.ts`)
> already logs which SKUs were purchased, so wiring up the write-back later
> is mostly plumbing, not a redesign.

## Shareable preview

`preview/old-light-preview.html` is the whole storefront as one
self-contained file — no server, no build, no network. Open it in a
browser or send it to someone who needs to see the shop before it's
deployed. All 78 products in it are real inventory rows; the brand
tokens and the moon-phase thresholds are copied from this codebase so
the two can't drift. See `preview/README.md` for what's deliberately
not real in it, and how to regenerate after data or copy changes.

## Product photos

An item's photos come from the sheet's `Images` column when it has one.
When it doesn't, the storefront falls back to photos committed to this
repo, one folder per SKU:

```
public/products/A1-MD-0001/1.jpg   ->  /products/A1-MD-0001/1.jpg
public/products/A1-MD-0001/2.jpg   ->  /products/A1-MD-0001/2.jpg
```

After adding or removing photos, regenerate the lookup:

```bash
npx tsx lib/build-image-manifest.ts
```

That rewrites `lib/product-images.generated.ts` (checked in, never edited
by hand). A generated manifest is used rather than reading the directory
at runtime because `lib/products.ts` is imported by a client component
(`components/cart-drawer.tsx`), so it can't touch `fs`.

Folders are named by SKU rather than files being named `<SKU>-1.jpg`
because EHC SKUs contain hyphens *and* end in digits (`A1-MD-0001`),
which makes that filename convention impossible to split reliably.

**Why photos live in the repo at all:** the real EHC sheet's `White Photo
Links` column is filled on 4 of 78 rows, and 3 of those hold misaligned
text instead of links — and there's no write access to repair it from
code (see `CLAUDE.md`). Committing photos sidesteps the sheet entirely,
and once deployed these are public URLs a marketplace or crosslister can
point at too.

## Connecting Stripe

1. Create/use a Stripe account, grab the **secret key** from the dashboard
   → `STRIPE_SECRET_KEY`.
2. Grab the **publishable key** → `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
   (not used by the current Checkout-redirect flow, but wired in for any
   future embedded/Elements-based checkout).
3. For local webhook testing: `stripe listen --forward-to
   localhost:3000/api/checkout/webhook` and put the printed signing secret
   in `STRIPE_WEBHOOK_SECRET`. In production, add the same endpoint URL in
   the Stripe dashboard's Webhooks section and use its signing secret.

Checkout is real money once live keys are in place — test with Stripe test
keys (`sk_test_...`) first.

## Data API — Centralized Inventory Sync

The storefront now has built-in data sync endpoints that connect to EHC Inventory Log (Google Sheets) and eBay:

### Endpoints

**GET /api/data/inventory** — Fetch current inventory from Google Sheets
```bash
curl http://localhost:3000/api/data/inventory
curl http://localhost:3000/api/data/inventory?status=In%20Stock
curl http://localhost:3000/api/data/inventory?gender=Women
```

**GET /api/data/sync** — Get sync state and logs
```bash
curl http://localhost:3000/api/data/sync
```

**POST /api/data/sync** — Trigger manual sync from Google Sheets
```bash
curl -X POST http://localhost:3000/api/data/sync
```

**GET /api/data/export** — Export inventory for external tools (Vendoo, etc.)
```bash
curl http://localhost:3000/api/data/export?format=json
# Supports: ?format=json (default), ?format=csv (coming soon)
```

### Sync Dashboard

Monitor all data transfers in real-time:
```
http://localhost:3000/dashboard
```

Shows:
- Current sync status (Idle / Syncing)
- Last sync times
- Recent sync logs with records processed, errors, duration
- Manual trigger button for on-demand syncs

### Data Flow Architecture

```
EHC Inventory Log (Google Sheets)
    ↓
Data API (Storefront)
    ├→ Product Catalog (displayed to customers)
    │
    └→ /api/data/export → Vendoo, Facebook Marketplace, etc.
         (your API keys control external syncs)
```

**Key point:** Storefront is your single source of truth. All marketplace syncs (eBay, Facebook, etc.) pull from Storefront via `/api/data/export`, using your own Vendoo account or API integrations. No direct marketplace API calls needed.

### Configuration

Data API environment variables (add to `.env.local`):

```
# Google Sheets Integration (required)
EHC_SHEET_ID=1-UcTy4Cr_NPK622SPRXob7LfpHFEw5874mv9y5E90Ys
GOOGLE_SHEETS_API_KEY=your_google_api_key_here

# Google Drive Image Sync (Optional, future)
GOOGLE_DRIVE_FOLDER_ID=your_ehc_import_folder_id_here

# Blob Storage (Optional, future)
CLOUDINARY_CLOUD_NAME=your_cloud_name
```

All sync state is logged to `public/logs/sync-state.json` (retained: last 100 syncs).

### Syncing to External Marketplaces

Instead of direct API integrations, use one of these approaches:

**Option 1: Vendoo (Recommended)**
- Vendoo app pulls from `/api/data/export?format=json`
- Manages syncs to eBay, Facebook Marketplace, Poshmark
- You control your Vendoo API key, not ours

**Option 2: Custom Export + Your Tools**
- Export inventory JSON from `/api/data/export`
- Feed into your own integration (automation, scripts, etc.)
- Full control over data transformation

**Option 3: Future CSV Export**
- Coming soon: `/api/data/export?format=csv`
- For bulk upload tools or manual marketplace updates

## Cross-marketing with JayLeeFit (coaching)

A footer strip and an About-page block link out to the JayLeeFit coaching
brand. Controlled entirely by env vars — on by default, set
`NEXT_PUBLIC_SHOW_CROSS_PROMO=false` to hide it entirely:

```
NEXT_PUBLIC_SHOW_CROSS_PROMO=true
NEXT_PUBLIC_JAYLEEFIT_URL=https://your-jayleefit-site.com
NEXT_PUBLIC_JAYLEEFIT_LABEL=JayLeeFit Coaching
```

## Project structure

```
app/
  page.tsx                  home
  shop/page.tsx             catalog + filters (category, size, sort, sale)
  shop/[slug]/page.tsx      product detail
  about/page.tsx            brand story
  checkout/success|cancel   post-Stripe redirect pages
  api/checkout/route.ts     creates the Stripe Checkout Session (server-priced)
  api/checkout/webhook/     verifies + logs completed orders
components/                 Navbar, Footer, ProductCard, CartDrawer, etc.
lib/
  products.ts               Google Sheet fetch + CSV parse + fallback
  sample-products.ts        local fallback catalog
  cart-context.tsx           localStorage-backed cart (client)
  stripe.ts                  server Stripe client
```

## Deploying

Any Next.js host works (Vercel is the path of least resistance for a
custom domain + env vars + zero-config builds). Point your own URL's DNS at
the deployment, set the env vars above in the host's dashboard, and update
`NEXT_PUBLIC_SITE_URL` to the final domain so Stripe redirects land
correctly.
