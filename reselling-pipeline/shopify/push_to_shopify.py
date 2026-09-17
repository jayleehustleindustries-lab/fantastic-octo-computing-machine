"""Push 'ready' rows from Supabase to Shopify as DRAFT products.

Never auto-publishes. A draft product is invisible on the storefront until
a human publishes it in Shopify admin -- that's the review checkpoint.

Usage:
    python push_to_shopify.py [--limit N]

Requires SUPABASE_URL, SUPABASE_SERVICE_KEY, SHOPIFY_STORE,
SHOPIFY_ACCESS_TOKEN in the environment.
"""
import argparse
import os
import sys
from datetime import datetime, timezone

import requests
from supabase import create_client

API_VERSION = "2024-10"


def graphql(store: str, token: str, query: str, variables: dict) -> dict:
    url = f"https://{store}/admin/api/{API_VERSION}/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": token}
    resp = requests.post(url, headers=headers, json={"query": query, "variables": variables}, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    if body.get("errors"):
        raise RuntimeError(body["errors"])
    return body["data"]


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


def push_product(store: str, token: str, row: dict, images: list[dict]) -> str:
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

    variants_query = """
    query($id: ID!) { product(id: $id) { variants(first: 1) { nodes { id } } } }
    """
    variant_data = graphql(store, token, variants_query, {"id": product_id})
    variant_id = variant_data["product"]["variants"]["nodes"][0]["id"]

    variant_input = {
        "id": variant_id,
        "price": str(row["price"]),
        "inventoryItem": {"sku": row["sku"]},
    }
    if row.get("compare_at_price"):
        variant_input["compareAtPrice"] = str(row["compare_at_price"])

    update_data = graphql(store, token, UPDATE_VARIANT, {"productId": product_id, "variants": [variant_input]})
    update_errors = update_data["productVariantsBulkUpdate"]["userErrors"]
    if update_errors:
        raise RuntimeError(update_errors)

    return product_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
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

    query = client.table("products").select("*").eq("status", "ready")
    if args.limit:
        query = query.limit(args.limit)
    rows = query.execute().data

    if not rows:
        print("No rows with status='ready'. Nothing to push.")
        return

    for row in rows:
        images = client.table("product_images").select("*").eq("sku", row["sku"]).order("position").execute().data
        try:
            product_id = push_product(shopify_store, shopify_token, row, images)
        except Exception as exc:  # noqa: BLE001 -- surface and continue with next row
            print(f"FAILED {row['sku']}: {exc}")
            continue

        client.table("products").update(
            {
                "shopify_product_id": product_id,
                "status": "pushed",
                "synced_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("sku", row["sku"]).execute()

        print(f"Pushed {row['sku']} -> {product_id} (DRAFT, review before publishing)")


if __name__ == "__main__":
    main()
