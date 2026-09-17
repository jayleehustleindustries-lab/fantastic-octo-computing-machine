"""Poshmark closet scraper -- RUN THIS ON YOUR OWN MACHINE, NOT IN A CLOUD SESSION.

Why local-only: this opens a real browser, you log into Poshmark yourself
interactively, and the script never sees or stores your password. Running
scraping like this at scale from a shared/cloud IP is also more likely to
trip Poshmark's bot detection on your actual selling account -- doing it
from your own browser session on your own machine is the safer path.

This is a stub: it opens your closet URL and prints the listing DOM
structure so you can confirm selectors before trusting the CSV output.
Poshmark's markup changes over time -- verify the selectors below still
match before relying on this for all 367 items.

Usage:
    pip install playwright
    playwright install chromium
    python poshmark_scraper.py --closet-url https://poshmark.com/closet/yourusername --output ../etl/inventory_seed.csv
"""
import argparse
import csv
import time

from playwright.sync_api import sync_playwright


def scrape_closet(closet_url: str) -> list[dict]:
    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(closet_url)

        print("Log into Poshmark in the opened window if prompted.")
        print("Press Enter here once your closet listings are visible...")
        input()

        # Scroll to trigger lazy-loaded listings.
        prev_height = 0
        while True:
            page.mouse.wheel(0, 3000)
            time.sleep(1.5)
            height = page.evaluate("document.body.scrollHeight")
            if height == prev_height:
                break
            prev_height = height

        # NOTE: verify these selectors against the live page before trusting
        # output at scale -- Poshmark's class names are not guaranteed stable.
        tiles = page.query_selector_all("[data-et-name='listing_tile']")
        print(f"Found {len(tiles)} listing tiles. Inspect a few manually before trusting all of them.")

        for tile in tiles:
            title_el = tile.query_selector("[data-test='tile-title']")
            price_el = tile.query_selector("[data-test='tile-price']")
            img_el = tile.query_selector("img")
            link_el = tile.query_selector("a")

            rows.append(
                {
                    "title": title_el.inner_text().strip() if title_el else "",
                    "price": price_el.inner_text().strip().lstrip("$") if price_el else "",
                    "image_url_1": img_el.get_attribute("src") if img_el else "",
                    "poshmark_id": (link_el.get_attribute("href") or "").split("/")[-1] if link_el else "",
                }
            )

        browser.close()
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--closet-url", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    rows = scrape_closet(args.closet_url)

    fieldnames = ["sku", "poshmark_id", "title", "description", "brand", "category",
                  "price", "compare_at_price", "condition", "size", "quantity",
                  "image_url_1", "image_url_2", "image_url_3"]

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, row in enumerate(rows, start=1):
            row.setdefault("sku", f"POSH-{i:04d}")
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    print(f"Wrote {len(rows)} rows to {args.output}. Review before running sheets_to_supabase.py.")


if __name__ == "__main__":
    main()
