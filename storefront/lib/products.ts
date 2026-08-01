import { csvToObjects } from "./csv";
import { sampleProducts } from "./sample-products";
import type { Category, Product } from "./types";

/**
 * Inventory source of truth is a Google Sheet (matches the existing
 * spreadsheet-first workflow this shop already runs on). No API key needed —
 * share the sheet as "Anyone with the link can view" and it's readable via
 * the gviz CSV export endpoint. See storefront/README.md for the exact
 * column headers expected.
 */
const SHEET_ID = process.env.GOOGLE_SHEET_ID || "1-UcTy4Cr_NPK622SPRXob7LfpHFEw5874mv9y5E90Ys";
const SHEET_NAME = process.env.GOOGLE_SHEET_NAME || "Inventory";

function slugify(input: string): string {
  return input
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function toBool(value: string): boolean {
  const v = value.trim().toLowerCase();
  return v === "y" || v === "yes" || v === "true" || v === "1" || v === "in stock";
}

/** "$12.00" -> 12. parseFloat alone chokes on the leading currency symbol. */
function toNumber(value: string): number {
  const n = parseFloat(value.replace(/[^0-9.-]/g, ""));
  return Number.isNaN(n) ? 0 : n;
}

function toCategory(value: string): Category {
  const v = value.trim().toLowerCase();
  if (v.startsWith("m")) return "Men";
  if (v.startsWith("w")) return "Women";
  return "Unisex";
}

/**
 * The EHC Inventory Log doesn't have an "In Stock" column — availability has
 * to be read off Inventory Status / Condition instead. Anything not
 * explicitly gone (donated, liquidated, passed on, pulled from inventory)
 * counts as available, since most rows are simply "not graded/listed yet."
 */
function isAvailable(inventoryStatus: string, condition: string): boolean {
  const text = `${inventoryStatus} ${condition}`.toLowerCase();
  const gone = ["donated", "liquidated", "passed / not purchased", "removed from inventory", "not for sale", "sold"];
  return !gone.some((phrase) => text.includes(phrase));
}

function toConditionScore(condition: string, explicit?: string): number {
  if (explicit) {
    const n = parseInt(explicit, 10);
    if (!Number.isNaN(n)) return n;
  }
  const match = condition.match(/(\d{1,2})\s*\/\s*10/);
  return match ? parseInt(match[1], 10) : 7;
}

function splitMulti(value: string): string[] {
  return value
    .split(/[|;]/)
    .map((v) => v.trim())
    .filter(Boolean);
}

/** "2026-06-22" (the sheet's Timestamp column, when the row was logged) -> days since then. */
function toDaysInInventory(value: string): number | null {
  if (!value.trim()) return null;
  const logged = new Date(value.trim());
  if (Number.isNaN(logged.getTime())) return null;
  const msPerDay = 1000 * 60 * 60 * 24;
  const days = Math.floor((Date.now() - logged.getTime()) / msPerDay);
  return days >= 0 ? days : null;
}

export function rowsToProducts(rows: Record<string, string>[]): Product[] {
  return rows
    .map((row): Product | null => {
      const name =
        row["SEO Listing Title"] || row["Name"] || row["Item Name"] || row["Item"] || "";
      if (!name) return null;

      const sku = row["SKU"] || row["Permanent SKU"] || slugify(name).slice(0, 12).toUpperCase();
      const condition = row["Condition"] || "7/10 — Great";
      const originalPrice = toNumber(row["Original Price"] || row["Retail Price"] || "0");
      const price = toNumber(
        row["Price"] || row["Resale Price"] || row["Realistic Sold Value"] || "0"
      );

      // EHC's sheet splits gender/department (Department) from garment type
      // (Category) the opposite way this project's own documented spec does
      // (Category = gender, Type = garment). Department present means we're
      // reading the real sheet; fall back to the documented layout otherwise.
      const hasDepartment = Boolean(row["Department"]);
      const categorySource = hasDepartment ? row["Department"] : row["Category"] || "Unisex";
      const typeSource = hasDepartment ? row["Category"] || row["Type"] || "" : row["Type"] || "";

      const tags = row["Tags"]
        ? splitMulti(row["Tags"])
        : [row["Style Tag 1"], row["Style Tag 2"], row["Style Tag 3"]].filter(Boolean);

      return {
        sku,
        slug: row["Slug"] ? slugify(row["Slug"]) : slugify(`${name}-${sku}`),
        name,
        brand: row["Brand"] || "",
        category: toCategory(categorySource),
        type: typeSource,
        size: row["Size"] || "",
        condition,
        conditionScore: toConditionScore(condition, row["Condition Score"]),
        originalPrice,
        price,
        description: row["SEO Listing Description"] || row["Description"] || "",
        images: splitMulti(row["Images"] || row["Image"] || ""),
        tags,
        inStock: row["In Stock"]
          ? toBool(row["In Stock"])
          : isAvailable(row["Inventory Status"] || "", condition),
        daysInInventory: toDaysInInventory(row["Timestamp"] || row["Date Added"] || ""),
      };
    })
    .filter((p): p is Product => p !== null);
}

async function fetchFromGoogleSheet(): Promise<Product[] | null> {
  if (!SHEET_ID) return null;

  const url = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:csv&sheet=${encodeURIComponent(
    SHEET_NAME
  )}`;

  try {
    const res = await fetch(url, { next: { revalidate: 60 } });
    if (!res.ok) return null;
    const csv = await res.text();
    const products = rowsToProducts(csvToObjects(csv));
    return products.length > 0 ? products : null;
  } catch {
    return null;
  }
}

export async function getProducts(): Promise<Product[]> {
  const sheetProducts = await fetchFromGoogleSheet();
  return sheetProducts ?? sampleProducts;
}

export async function getProductBySlug(slug: string): Promise<Product | undefined> {
  const products = await getProducts();
  return products.find((p) => p.slug === slug);
}

export function discountPercent(product: Pick<Product, "originalPrice" | "price">): number {
  if (!product.originalPrice) return 0;
  return Math.round((1 - product.price / product.originalPrice) * 100);
}

export function formatPrice(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export type ConditionPhase = "full" | "gibbous" | "half" | "crescent";

const PHASE_THRESHOLDS: { max: number; phase: ConditionPhase; label: string }[] = [
  { max: 4, phase: "crescent", label: "Old Light" },
  { max: 6, phase: "half", label: "Half-Light" },
  { max: 8, phase: "gibbous", label: "Waxing" },
  { max: Infinity, phase: "full", label: "Full Illumination" },
];

/** Condition score (1-10) -> moon phase, shared by the UI and the asset pipeline. */
export function phaseForScore(score: number) {
  return PHASE_THRESHOLDS.find((p) => score <= p.max) ?? PHASE_THRESHOLDS[PHASE_THRESHOLDS.length - 1];
}
