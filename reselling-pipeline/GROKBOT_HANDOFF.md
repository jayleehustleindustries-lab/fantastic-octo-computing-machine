# Task: Extract Poshmark closet inventory into a CSV

## Goal

Produce one CSV file listing every active item in this Poshmark closet:

`https://poshmark.com/closet/<the account's username>`

This is the account owner's own closet — you're helping them export their own
inventory data, not scraping anyone else's listings. The output CSV feeds
directly into an existing pipeline (`sheets_to_supabase.py` → Supabase →
Shopify), so the schema below must be followed exactly. Do not rename
columns, reorder them arbitrarily, or invent data for a field you can't read
from the page — leave it blank instead. A blank gets flagged for human
review downstream; a guessed/wrong value gets silently pushed to a live
Shopify store, which is the failure mode we're avoiding.

## Output schema (CSV header, exact column names)

```
sku,poshmark_id,title,description,brand,category,price,compare_at_price,condition,size,quantity,image_url_1,image_url_2,image_url_3
```

| Column | Required | Format | Notes |
|---|---|---|---|
| `sku` | yes | text | If Poshmark doesn't expose one, generate `POSH-0001`, `POSH-0002`, ... in listing order. Must be unique per row. |
| `poshmark_id` | no | text | The listing's slug/ID from its URL (e.g. the last path segment of the listing link). Used for de-duplication on re-runs. |
| `title` | yes | text | Exactly as shown on the listing. |
| `description` | no | text | Full listing description text. Strip HTML if present. |
| `brand` | no | text | As tagged on the listing. |
| `category` | no | text | As tagged on the listing (e.g. "Women > Tops"). |
| `price` | yes | plain decimal, no `$` | e.g. `45.00`, not `$45` or `45`. |
| `compare_at_price` | no | plain decimal | Original/list price if the listing shows one, else leave blank (don't repeat `price` into this field — leaving it blank is correct when there's no discount). |
| `condition` | no | text | Poshmark's own condition label for the item (e.g. "New", "Good", "Fair"). |
| `size` | no | text | As shown on the listing. |
| `quantity` | no | integer, default `1` | Poshmark listings are usually qty 1 unless it's a bundle/multi-quantity listing. |
| `image_url_1..3` | no | full https URL | Up to 3 photo URLs per listing, in the order they appear. If a listing has more than 3 photos, only the first 3 are needed for now. |

## Rules

1. **One row per active listing.** Skip sold/deleted listings unless asked otherwise.
2. **Never fabricate a value.** If you can't confidently read a field, leave the cell empty. Do not estimate a price, guess a brand, or invent a description.
3. **Escape correctly.** Titles/descriptions may contain commas or quotes — use standard CSV quoting (wrap the field in `"..."`, double any internal `"`).
4. **Don't paginate past what's visible without scrolling/loading more** — if the closet uses infinite scroll, keep scrolling/loading until no new listings appear before stopping.
5. **Report what you couldn't get.** At the end, list any listings you skipped and why (e.g. "listing X failed to load", "listing Y had no readable price").

## Delivery

Save the result as a single file named `inventory_seed.csv`. Send it back to
the user — they will drop it into `reselling-pipeline/etl/inventory_seed.csv`
in their pipeline repo and run:

```
python etl/sheets_to_supabase.py --csv etl/inventory_seed.csv
```

That script independently validates every row (required fields, numeric
price, duplicate SKUs) — rows that fail validation are written to
`inventory_seed_rejected.csv` with a reason instead of silently disappearing,
and rows missing images/condition are inserted but flagged for manual review
before they can reach Shopify. So: if you're unsure about a field, leaving it
blank is safe — the pipeline downstream is built to catch and flag exactly
that, not to fail silently or push bad data live.
