# eBay crosslisting — real Sell API integration

Unlike Facebook Marketplace, eBay has a genuine, documented public API
individual sellers can use for real listing automation. This module
builds real listings, not copy-paste prep — everything here defaults to
eBay's **Sandbox** environment and dry-run mode until you deliberately
turn both off.

## Before this can run at all

I can't do this part — it's identity/business-linked and has to be you,
directly on eBay's site:

1. Go to [developer.ebay.com](https://developer.ebay.com) and register
   — this is a separate login from your normal eBay seller account.
   eBay reviews new registrations (historically ~1 business day).
2. Create an application to get an **App ID (Client ID)** and
   **Cert ID (Client Secret)**.
3. Complete eBay's OAuth consent flow for your own seller account to
   grant listing-write access (the `sell.inventory` scope). This is a
   one-time browser flow on eBay's site that ends with a **refresh
   token** — a long-lived credential (eBay's refresh tokens last ~18
   months) that this code exchanges for short-lived access tokens on
   each run.

Once you have those three values, set them as environment variables
(never commit these):

```
EBAY_APP_ID=...
EBAY_CERT_ID=...
EBAY_REFRESH_TOKEN=...
EBAY_ENV=sandbox        # switch to "production" only after a sandbox check
```

## Running it

```
# Dry run — prints category/condition resolution + what would be created, publishes nothing
npx tsx lib/ebay-sync/sync.ts --csv=path/to/local.csv

# Real listings, one item at a time, prints confirmation after each publish
npx tsx lib/ebay-sync/sync.ts --csv=path/to/local.csv --publish
```

Always run a dry run against `EBAY_ENV=sandbox` first and spot-check a
few items' resolved category/condition before ever setting
`EBAY_ENV=production` and passing `--publish`.

## What this doesn't solve

Same limitation as the Facebook exporters — no write access to the EHC
Inventory Log sheet. After a real publish, the script prints exactly
which SKU to mark; you still add "eBay" to that row's `Listing
Platforms` column by hand so future runs skip it (via `alreadyOnEbay()`
in `ebay.ts`, same pattern as the Facebook side's `alreadyOnFacebook()`).

## Why category and condition aren't hardcoded

eBay's category tree has thousands of IDs, and its condition enum is
category-specific (apparel uses different values than general
merchandise). Guessing either risked silently mis-listing a real item,
so `client.ts` resolves both live from eBay's own Taxonomy API
(`getCategorySuggestions`) and Metadata API
(`getItemConditionPolicies`) instead of a hand-maintained mapping table.
The condition match in `sync.ts`'s `pickCondition()` is a best-effort
text match against whatever eBay actually returns for that category —
worth a human glance in dry-run output before trusting it, since
there's no universal ordering across categories to fall back on.
