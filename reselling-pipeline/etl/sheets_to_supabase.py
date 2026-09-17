"""Stage & clean: upsert a CSV (scraper output, Vendoo export, or hand-filled
csv_template.csv) into the Supabase 'products' / 'product_images' tables.

This is the "one true source" step. Nothing downstream (Shopify push) reads
the CSV directly -- everything reads from Supabase after this has run.

Usage:
    python sheets_to_supabase.py --csv etl/inventory_seed.csv

Requires SUPABASE_URL and SUPABASE_SERVICE_KEY in the environment (see
shopify/.env.example -- same env file is shared across scripts in this repo).
"""
import argparse
import csv
import os
import sys

from supabase import create_client


def load_rows(csv_path: str) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def upsert_row(client, row: dict) -> None:
    sku = row["sku"].strip()
    if not sku:
        return

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
            "status": "ready",
        }
    ).execute()

    image_cols = [c for c in row if c.startswith("image_url_")]
    for position, col in enumerate(sorted(image_cols)):
        url = row.get(col, "").strip()
        if not url:
            continue
        client.table("product_images").upsert(
            {"sku": sku, "url": url, "position": position},
            on_conflict="sku,position",
        ).execute()


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

    for row in rows:
        upsert_row(client, row)

    print(f"Upserted {len(rows)} rows from {args.csv} into Supabase.")


if __name__ == "__main__":
    main()
