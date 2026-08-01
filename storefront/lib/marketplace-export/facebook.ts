/**
 * Maps a real EHC Inventory Log row into Facebook Marketplace's actual
 * listing fields (title, price, category, condition, description) —
 * ready to copy-paste into FB's own posting form. There is no Facebook
 * Marketplace API for individual sellers, and automating posts there
 * violates Facebook's ToS, so this stays a copy-paste aid, not an
 * auto-poster. Reuses the exact column names and availability logic
 * already proven against the real 71-row sheet in ../products.ts —
 * doesn't reinvent that mapping.
 */

export type FacebookListing = {
  sku: string;
  title: string;
  price: number;
  category: string;
  condition: "New" | "Used - Like New" | "Used - Good" | "Used - Fair";
  description: string;
  photoNote: string;
};

/** "$12.00" -> 12, same helper as products.ts. */
function toNumber(value: string): number {
  const n = parseFloat(value.replace(/[^0-9.-]/g, ""));
  return Number.isNaN(n) ? 0 : n;
}

/** Facebook truncates long titles in its own UI; keep ours under a safe limit. */
function truncateTitle(title: string, max = 100): string {
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

/**
 * Facebook Marketplace's condition field is a fixed 4-option list — not
 * the free-text 1-10 grading this sheet uses. Mapped conservatively (a
 * borderline score rounds down in honesty, not up in salesmanship).
 */
function toFacebookCondition(score: number): FacebookListing["condition"] {
  if (score >= 9) return "Used - Like New";
  if (score >= 7) return "Used - Good";
  return "Used - Fair";
}

/**
 * Facebook's own category tree doesn't map 1:1 to this sheet's
 * Department/Category columns — this is a best-fit starting guess, not
 * authoritative. Flagged in the output so it gets a human check per item.
 */
function guessFacebookCategory(department: string): string {
  const d = department.trim().toLowerCase();
  if (d.startsWith("m")) return "Men's clothing (double-check FB's exact category)";
  if (d.startsWith("w")) return "Women's clothing (double-check FB's exact category)";
  return "Clothing & accessories (double-check FB's exact category)";
}

export function rowToFacebookListing(row: Record<string, string>): FacebookListing | null {
  const name = row["SEO Listing Title"] || row["Item Name"] || "";
  if (!name) return null;

  const sku = row["Permanent SKU"] || row["SKU"] || "";
  const condition = row["Condition"] || "7/10 — Great";
  const score = toConditionScore(condition, row["Condition Score"]);
  const price = toNumber(row["Realistic Sold Value"] || row["Price"] || "0");
  const brand = row["Brand"] || "";
  const size = row["Size"] || "";
  const department = row["Department"] || row["Category"] || "";
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
    price,
    category: guessFacebookCategory(department),
    condition: toFacebookCondition(score),
    description: fullDescription,
    photoNote: "Attach photos manually — Facebook Marketplace has no URL-based photo import.",
  };
}
