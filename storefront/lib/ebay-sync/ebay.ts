/**
 * Maps a real EHC Inventory Log row into the shape eBay's Sell Inventory
 * API needs (an InventoryItem + an Offer) — everything that's knowable
 * from the sheet alone, without calling eBay.
 *
 * Deliberately does NOT hardcode an eBay category ID or condition enum
 * here. eBay's category tree has thousands of IDs, and its condition
 * enum is category-specific (apparel uses different values than general
 * merchandise, e.g. PRE_OWNED_GOOD vs USED_EXCELLENT) — guessing either
 * risks silently mis-listing a real item. client.ts resolves both live
 * via eBay's own Taxonomy API (getCategorySuggestions) and Metadata API
 * (getItemConditionPolicies) instead.
 */

export type EbayListingDraft = {
  sku: string;
  title: string;
  description: string;
  price: number;
  quantity: number;
  conditionScore: number;
  images: string[];
  categorySearchQuery: string;
};

function truncateTitle(title: string, max = 80): string {
  if (title.length <= max) return title;
  return title.slice(0, max - 1).trimEnd() + "…";
}

function toConditionScore(condition: string, explicit?: string): number {
  if (explicit) {
    const n = parseInt(explicit, 10);
    if (!Number.isNaN(n)) return n;
  }
  const match = condition.match(/(\d{1,2})\s*\/\s*10/);
  return match ? parseInt(match[1], 10) : 7;
}

function toNumber(value: string): number {
  const n = parseFloat(value.replace(/[^0-9.-]/g, ""));
  return Number.isNaN(n) ? 0 : n;
}

/** True once the sheet's own Listing Platforms column already says eBay. */
export function alreadyOnEbay(row: Record<string, string>): boolean {
  return (row["Listing Platforms"] || "").toLowerCase().includes("ebay");
}

export function rowToEbayDraft(row: Record<string, string>): EbayListingDraft | null {
  const name = row["SEO Listing Title"] || row["Item Name"] || "";
  if (!name) return null;

  const sku = row["Permanent SKU"] || row["SKU"] || "";
  const condition = row["Condition"] || "7/10 — Great";
  const brand = row["Brand"] || "";
  const size = row["Size"] || "";
  const department = row["Department"] || row["Category"] || "";
  const category = row["Category"] || "";
  const description = row["SEO Listing Description"] || row["Description"] || "";

  const fullDescription = [
    description,
    "",
    `Brand: ${brand || "Unbranded"}${size ? ` · Size: ${size}` : ""} · Condition: ${condition}`,
  ]
    .filter(Boolean)
    .join("\n");

  return {
    sku,
    title: truncateTitle(name),
    description: fullDescription,
    price: toNumber(row["Realistic Sold Value"] || row["Price"] || "0"),
    quantity: 1,
    conditionScore: toConditionScore(condition, row["Condition Score"]),
    images: [],
    // Fed to eBay's own Taxonomy API to resolve a real category ID —
    // not a hand-maintained guess.
    categorySearchQuery: [department, category].filter(Boolean).join(" "),
  };
}
