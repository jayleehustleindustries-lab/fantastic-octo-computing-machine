/**
 * Maps a real EHC Inventory Log row into a Vendoo-shaped listing.
 *
 * Vendoo is a crosslister: it drives Poshmark/Mercari/eBay/Depop through
 * a browser extension rather than an API, which is why it works where
 * API automation is either prohibited (Poshmark, Mercari, Facebook) or
 * gated behind a developer approval (eBay). It's the piece that replaces
 * the automation that can't be built — see the plan and root CLAUDE.md.
 *
 * Third mapper in this family, deliberately the same shape as
 * `rowToFacebookListing()` (./facebook.ts) and `rowToEbayDraft()`
 * (../ebay-sync/ebay.ts), reusing the same column fallbacks that were
 * verified against the real 71-row export.
 *
 * IMPORTANT — the column headers in VENDOO_COLUMNS below are NOT
 * confirmed against Vendoo's real import template. Nobody has checked
 * whether Vendoo takes a CSV bulk import at all, or requires per-item
 * entry. The extraction (which row means what) is the hard part and is
 * verified; renaming headers to match their template later is a
 * one-constant edit. Do not treat this file as proof Vendoo accepts it.
 */
import { imagesForSku } from "../products";

export type VendooListing = {
  sku: string;
  title: string;
  description: string;
  price: number;
  costOfGoods: number;
  brand: string;
  size: string;
  color: string;
  department: string;
  category: string;
  condition: string;
  conditionScore: number;
  photos: string[];
  storageLocation: string;
};

/** Vendoo's title cap is unconfirmed; 80 matches eBay's and is the safer bound. */
function truncateTitle(title: string, max = 80): string {
  if (title.length <= max) return title;
  return title.slice(0, max - 1).trimEnd() + "…";
}

function toNumber(value: string): number {
  const n = parseFloat(value.replace(/[^0-9.-]/g, ""));
  return Number.isNaN(n) ? 0 : n;
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
 * Rounds down on a borderline score rather than up — the same rule the
 * Facebook mapper uses, and the one BRAND-VOICE.md names as a promise:
 * "close calls round down, never up."
 */
export function toVendooCondition(score: number): string {
  if (score >= 10) return "New";
  if (score >= 9) return "Like New";
  if (score >= 7) return "Good";
  if (score >= 5) return "Fair";
  return "Poor";
}

/** True once the sheet's own Listing Platforms column already says Vendoo. */
export function alreadyOnVendoo(row: Record<string, string>): boolean {
  return (row["Listing Platforms"] || "").toLowerCase().includes("vendoo");
}

export function rowToVendooListing(row: Record<string, string>): VendooListing | null {
  const name =
    row["SEO Listing Title"] || row["Optimized SEO Title"] || row["Item Name"] || "";
  if (!name) return null;

  const sku = row["Permanent SKU"] || row["SKU"] || "";
  const condition = row["Condition"] || "7/10 — Great";
  const conditionScore = toConditionScore(condition, row["Condition Score"]);

  return {
    sku,
    title: truncateTitle(name),
    description:
      row["Optimized Description"] || row["SEO Listing Description"] || row["Description"] || "",
    price: toNumber(
      row["Recommended List Price"] || row["Realistic Sold Value"] || row["Price"] || "0"
    ),
    costOfGoods: toNumber(row["Cost of Goods"] || "0"),
    brand: row["Brand"] || "",
    size: row["Size"] || "",
    color: row["Color"] || "",
    department: row["Department"] || "",
    category: row["Category"] || row["Type"] || "",
    condition: toVendooCondition(conditionScore),
    conditionScore,
    // Photos come from what's actually been assigned in the repo, not from
    // the sheet — the sheet's White Photo Links column is filled on 4 of 78
    // rows and 3 of those hold misaligned text instead of links.
    photos: imagesForSku(sku),
    storageLocation: row["Storage Location"] || "",
  };
}

/** Header names are provisional — see the file header. */
export const VENDOO_COLUMNS = [
  "SKU",
  "Title",
  "Description",
  "Price",
  "Cost",
  "Brand",
  "Size",
  "Color",
  "Department",
  "Category",
  "Condition",
  "Photos",
  "Storage Location",
] as const;

function escapeCsv(value: string): string {
  return /[",\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value;
}

export function toCsvRow(listing: VendooListing, photoBaseUrl: string): string {
  const photos = listing.photos
    .map((p) => (photoBaseUrl ? `${photoBaseUrl.replace(/\/$/, "")}${p}` : p))
    .join(" | ");

  return [
    listing.sku,
    listing.title,
    listing.description,
    listing.price ? listing.price.toFixed(2) : "",
    listing.costOfGoods ? listing.costOfGoods.toFixed(2) : "",
    listing.brand,
    listing.size,
    listing.color,
    listing.department,
    listing.category,
    listing.condition,
    photos,
    listing.storageLocation,
  ]
    .map((v) => escapeCsv(String(v ?? "")))
    .join(",");
}
