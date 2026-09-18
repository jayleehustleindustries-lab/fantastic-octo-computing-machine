# Imports log

Snapshots of real inventory data pulled in and imported to Supabase, kept for audit/reproducibility. Not meant to be re-run automatically — each one was a manual, reviewed import.

## ehc_inventory_2026-09-18.csv

Source: Google Drive spreadsheet "EHC_inventory_database" (file id
`17JeIyMsos60gqsppplILJYnQVV1276V5KxODcDo-PuI`), the block matching the
described 31-column schema (Timestamp, Permanent SKU, Item Number, Storage
Location, ... Optimized Description).

**Known problems with this export, read before trusting it further:**

1. The Drive export flattens all spreadsheet tabs into one markdown document
   with no tab-name labels. 18 distinct table blocks were found; this CSV is
   one of them, matched by column-header pattern, not by a real tab name.
2. A second block (~71 rows, same SKU range `A1-MD-0001` onward) has
   materially different data for the same SKUs — different `Inventory
   Status`, different prices, ~138 field-level differences from this one.
   Which is authoritative was NOT resolved. Confirm against the live sheet
   before treating either as ground truth for anything beyond staging.
3. Two rows (`A4-MD-0051`, `A4-MD-0058`) have `Men's Tops` sitting in the
   `White Photo Links` column — a column-shift/data-entry bug in the source
   sheet, not a real URL. Their SKUs are otherwise valid.
4. Photo coverage: 0 of 78 rows have a usable photo URL in either photo-link
   column at import time. Real photo files exist in the
   `EHC-Inventory-Ready-To-List` Drive folder, but are named by camera/export
   ID (e.g. `IMG_6574-Photoroom-Photoroom.jpg`), not by SKU — nothing maps
   them to a row automatically.

**Import result:** all 78 rows loaded into the `products` table with
`source='ehc_sheet'`, `needs_review=true` on every row (per problem #4 — no
row had a real photo to hand-verify against), `status='sold'` for the one row
whose `Inventory Status` was `Sold`, `status='staged'` for the rest. None are
`status='ready'`, so none are eligible for `shopify/push_to_shopify.py` until
someone clears `needs_review` after confirming photos and details per row.
