"""Stage & clean: upsert a CSV (scraper output, Vendoo export, or hand-filled
csv_template.csv) into the Supabase 'products' / 'product_images' tables.

This is the "one true source" step. Nothing downstream (Shopify push) reads
the CSV directly -- everything reads from Supabase after this has run.

Bulletproofing:
  - Every row is validated before it touches the database. A row that fails
    validation is written to <csv>_rejected.csv with a reason column instead
    of crashing the run or being silently skipped.
  - A row that's parseable but incomplete (e.g. no image) is still inserted,
    marked needs_review=true, and excluded from the Shopify push until a
    human clears it.
  - Duplicate SKUs within the same CSV are caught before they hit Supabase.
  - Supabase writes retry with exponential backoff on transient errors.

Usage:
    python sheets_to_supabase.py --csv etl/inventory_seed.csv

Requires SUPABASE_URL and SUPABASE_SERVICE_KEY in the environment (see
shopify/.env.example -- same env file is shared across scripts in this repo).
"""
import argparse
import csv
import os
import sys
from pathlib import Path

from supabase import create_client

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.retry import RetryExhausted, with_retries  # noqa: E402

REQUIRED_FIELDS = ["sku", "title", "price"]


def load_rows(csv_path: str) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validate_row(row: dict, seen_skus: set[str]) -> tuple[bool, list[str], list[str]]:
    """Returns (is_valid, hard_errors, soft_warnings).
    Hard errors -> row rejected outright, never reaches Supabase.
    Soft warnings -> row inserted but flagged needs_review=true.
    """
    errors: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_FIELDS:
        if not (row.get(field) or "").strip():
            errors.append(f"missing required field '{field}'")

    sku = (row.get("sku") or "").strip()
    if sku and sku in seen_skus:
        errors.append(f"duplicate sku '{sku}' within this CSV")

    price_raw = (row.get("price") or "").strip()
    if price_raw:
        try:
            price = float(price_raw)
            if price <= 0:
                errors.append(f"price must be positive, got '{price_raw}'")
        except ValueError:
            errors.append(f"price '{price_raw}' is not a number")

    compare_raw = (row.get("compare_at_price") or "").strip()
    if compare_raw:
        try:
            float(compare_raw)
        except ValueError:
            errors.append(f"compare_at_price '{compare_raw}' is not a number")

    image_cols = [c for c in row if c.startswith("image_url_")]
    if not any((row.get(c) or "").strip() for c in image_cols):
        warnings.append("no image URLs provided")

    if not (row.get("condition") or "").strip():
        warnings.append("no condition provided")

    return (len(errors) == 0, errors, warnings)


def upsert_row(client, row: dict, needs_review: bool, notes: str) -> None:
    sku = row["sku"].strip()

    def do_upsert():
        client.table("products").upsert(
            {
                "sku": sku,
                "poshmark_id": row.get("poshmark_id") or None,
                "title": row["title"].strip(),
                "description": row.get("description") or None,
                "brand": row.get("brand") or None,
                "category": row.get("category") or None,
                "price": float(row["price"]),
                "compare_at_price": float(row["compare_at_price"]) if row.get("compare_at_price") else None,
                "condition": row.get("condition") or None,
                "size": row.get("size") or None,
                "quantity": int(row.get("quantity") or 1),
                "status": "staged" if needs_review else "ready",
                "needs_review": needs_review,
                "notes": notes or None,
            }
        ).execute()

    with_retries(do_upsert, label=f"upsert product {sku}")

    image_cols = [c for c in row if c.startswith("image_url_")]
    for position, col in enumerate(sorted(image_cols)):
        url = row.get(col, "").strip()
        if not url:
            continue

        def do_image_upsert(url=url, position=position):
            client.table("product_images").upsert(
                {"sku": sku, "url": url, "position": position},
                on_conflict="sku,position",
            ).execute()

        with_retries(do_image_upsert, label=f"upsert image {sku}#{position}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, help="Path to inventory CSV")
    args = parser.parse_args()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        sys.exit("Set SUPABASE_URL and SUPABASE_SERVICE_KEY in the environment first.")

    client = create_client(url, key)
    rows = load_rows(args.csv)

    seen_skus: set[str] = set()
    accepted = 0
    flagged = 0
    rejected: list[dict] = []

    for row in rows:
        is_valid, errors, warnings = validate_row(row, seen_skus)

        if not is_valid:
            rejected.append({**row, "reason": "; ".join(errors)})
            continue

        sku = row["sku"].strip()
        seen_skus.add(sku)

        needs_review = len(warnings) > 0
        notes = "; ".join(warnings) if warnings else ""

        try:
            upsert_row(client, row, needs_review, notes)
        except RetryExhausted as exc:
            rejected.append({**row, "reason": f"supabase write failed: {exc}"})
            continue

        accepted += 1
        if needs_review:
            flagged += 1

    if rejected:
        rejected_path = str(Path(args.csv).with_name(Path(args.csv).stem + "_rejected.csv"))
        fieldnames = sorted({k for r in rejected for k in r})
        with open(rejected_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rejected)
        print(f"{len(rejected)} rows rejected -> {rejected_path} (fix and re-run, they were not skipped silently)")

    print(f"Upserted {accepted} rows from {args.csv} into Supabase "
          f"({flagged} flagged needs_review, excluded from Shopify push until cleared).")


if __name__ == "__main__":
    main()
