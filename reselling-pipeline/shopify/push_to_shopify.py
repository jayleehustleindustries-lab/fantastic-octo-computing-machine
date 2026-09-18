"""Push 'ready' rows from Supabase to Shopify as DRAFT products.

Never auto-publishes. A draft product is invisible on the storefront until
a human publishes it in Shopify admin -- that's the review checkpoint.

Bulletproofing:
  - Before creating a product, checks Shopify for an existing product with
    the same SKU. If a previous run crashed after creating the Shopify
    product but before writing shopify_product_id back to Supabase, this
    run reconciles instead of creating a duplicate.
  - Every Shopify API call retries with exponential backoff on transient
    failures (rate limits, timeouts).
  - A row that still fails after retries is marked status='error' with the
    reason in error_message, and left alone -- it will NOT be silently
    retried forever on every run. Pass --retry-errors to explicitly requeue
    error rows.
  - needs_review=true rows are never pushed, full stop, regardless of status.

Usage:
    python push_to_shopify.py [--limit N] [--retry-errors]

Requires SUPABASE_URL, SUPABASE_SERVICE_KEY, SHOPIFY_STORE,
SHOPIFY_ACCESS_TOKEN in the environment.
"""
import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from supabase import create_client

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.retry import RetryExhausted, with_retries  # noqa: E402

API_VERSION = "2024-10"
TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}


class TransientShopifyError(Exception):
    pass


def graphql(store: str, token: str, query: str, variables: dict) -> dict:
    def call():
        url = f"https://{store}/admin/api/{API_VERSION}/graphql.json"
        headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": token}
        resp = requests.post(url, headers=headers, json={"query": query, "variables": variables}, timeout=30)
        if resp.status_code in TRANSIENT_STATUS_CODES:
            raise TransientShopifyError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        resp.raise_for_status()
        body = resp.json()
        if body.get("errors"):
            raise RuntimeError(body["errors"])
        return body["data"]

    return with_retries(call, retry_on=(TransientShopifyError, requests.exceptions.RequestException), label="shopify graphql call")


FIND_BY_SKU = """
query FindBySku($query: String!) {
  productVariants(first: 1, query: $query) {
    nodes { id product { id } }
  }
}
"""

CREATE_PRODUCT = """
mutation CreateProduct($input: ProductInput!) {
  productCreate(input: $input) {
    product { id }
    userErrors { field message }
  }
}
"""

UPDATE_VARIANT = """
mutation UpdateVariant($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
  productVariantsBulkUpdate(productId: $productId, variants: $variants) {
    productVariants { id price sku }
    userErrors { field message }
  }
}
"""

VARIANTS_FOR_PRODUCT = """
query($id: ID!) { product(id: $id) { variants(first: 1) { nodes { id } } } }
"""


def find_existing_product(store: str, token: str, sku: str) -> str | None:
    data = graphql(store, token, FIND_BY_SKU, {"query": f"sku:{sku}"})
    nodes = data["productVariants"]["nodes"]
    return nodes[0]["product"]["id"] if nodes else None


def upsert_variant(store: str, token: str, product_id: str, row: dict) -> None:
    variant_data = graphql(store, token, VARIANTS_FOR_PRODUCT, {"id": product_id})
    variant_id = variant_data["product"]["variants"]["nodes"][0]["id"]

    variant_input = {
        "id": variant_id,
        "price": str(row["price"]),
        "inventoryItem": {"sku": row["sku"]},
    }
    if row.get("compare_at_price"):
        variant_input["compareAtPrice"] = str(row["compare_at_price"])

    update_data = graphql(store, token, UPDATE_VARIANT, {"productId": product_id, "variants": [variant_input]})
    errors = update_data["productVariantsBulkUpdate"]["userErrors"]
    if errors:
        raise RuntimeError(errors)


def push_product(store: str, token: str, row: dict, images: list[dict]) -> str:
    existing_id = find_existing_product(store, token, row["sku"])
    if existing_id:
        print(f"  found existing Shopify product for {row['sku']} ({existing_id}); reconciling instead of duplicating")
        upsert_variant(store, token, existing_id, row)
        return existing_id

    create_input = {
        "title": row["title"],
        "descriptionHtml": f"<p>{row.get('description') or ''}</p>",
        "vendor": row.get("brand") or "",
        "productType": row.get("category") or "",
        "status": "DRAFT",
        "images": [{"src": img["url"]} for img in images if img.get("url")],
    }
    data = graphql(store, token, CREATE_PRODUCT, {"input": create_input})
    errors = data["productCreate"]["userErrors"]
    if errors:
        raise RuntimeError(errors)
    product_id = data["productCreate"]["product"]["id"]

    upsert_variant(store, token, product_id, row)
    return product_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--retry-errors", action="store_true",
                         help="Also requeue rows currently marked status='error'")
    args = parser.parse_args()

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
    shopify_store = os.environ.get("SHOPIFY_STORE")
    shopify_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")

    missing = [
        name
        for name, val in [
            ("SUPABASE_URL", supabase_url),
            ("SUPABASE_SERVICE_KEY", supabase_key),
            ("SHOPIFY_STORE", shopify_store),
            ("SHOPIFY_ACCESS_TOKEN", shopify_token),
        ]
        if not val
    ]
    if missing:
        sys.exit(f"Missing required env vars: {', '.join(missing)}")

    client = create_client(supabase_url, supabase_key)

    statuses = ["ready"] + (["error"] if args.retry_errors else [])
    query = (
        client.table("products")
        .select("*")
        .in_("status", statuses)
        .eq("needs_review", False)
    )
    if args.limit:
        query = query.limit(args.limit)
    rows = query.execute().data

    if not rows:
        print("No eligible rows (status in {ready" + (", error" if args.retry_errors else "") + "}, needs_review=false). Nothing to push.")
        return

    pushed, failed = 0, 0
    for row in rows:
        images = client.table("product_images").select("*").eq("sku", row["sku"]).order("position").execute().data
        try:
            product_id = push_product(shopify_store, shopify_token, row, images)
        except (RetryExhausted, RuntimeError) as exc:
            failed += 1
            print(f"FAILED {row['sku']}: {exc}")
            client.table("products").update(
                {"status": "error", "error_message": str(exc)[:500]}
            ).eq("sku", row["sku"]).execute()
            continue

        client.table("products").update(
            {
                "shopify_product_id": product_id,
                "status": "pushed",
                "error_message": None,
                "synced_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("sku", row["sku"]).execute()

        pushed += 1
        print(f"Pushed {row['sku']} -> {product_id} (DRAFT, review before publishing)")

    print(f"Done: {pushed} pushed, {failed} failed (marked status='error', re-run with --retry-errors after investigating).")


if __name__ == "__main__":
    main()
