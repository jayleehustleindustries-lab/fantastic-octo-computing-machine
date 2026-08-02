/**
 * Generates a simple posting-progress checklist (SKU + title + price,
 * checkbox per item) from the real EHC Inventory Log — a companion to
 * generate.ts's full listing copy, for tracking which of the (many)
 * items have actually been posted to Facebook Marketplace yet.
 *
 * Run with: npx tsx lib/marketplace-export/checklist.ts [output-path] [--csv=path/to/local.csv]
 */
import { readFileSync, writeFileSync } from "fs";
import { csvToObjects } from "../csv";
import { isAvailable } from "../products";
import { rowToFacebookListing, type FacebookListing } from "./facebook";

const SHEET_ID =
  process.env.GOOGLE_SHEET_ID || "1-UcTy4Cr_NPK622SPRXob7LfpHFEw5874mv9y5E90Ys";
const SHEET_NAME = process.env.GOOGLE_SHEET_NAME || "Inventory";

async function loadCsv(localCsvPath: string | null): Promise<string> {
  if (localCsvPath) return readFileSync(localCsvPath, "utf-8");

  const url = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:csv&sheet=${encodeURIComponent(
    SHEET_NAME
  )}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch sheet: ${res.status} ${res.statusText}`);
  }
  return res.text();
}

async function main() {
  const csvArg = process.argv.find((a) => a.startsWith("--csv="));
  const localCsvPath = csvArg ? csvArg.slice("--csv=".length) : null;

  const csv = await loadCsv(localCsvPath);
  const rows = csvToObjects(csv);

  const available = rows.filter((row) =>
    isAvailable(row["Inventory Status"] || "", row["Condition"] || "")
  );
  const listings = available
    .map(rowToFacebookListing)
    .filter((l): l is FacebookListing => l !== null);

  const doc = [
    "# Facebook Marketplace posting checklist — EHC Inventory",
    "",
    `Generated ${new Date().toISOString().slice(0, 10)}. Check each item off as you post it.`,
    "",
    ...listings.map((l) => `- [ ] **${l.sku}** — ${l.title} — $${l.price}`),
  ].join("\n");

  const outPath =
    process.argv.slice(2).find((a) => !a.startsWith("--")) ||
    "facebook-marketplace-checklist.md";
  writeFileSync(outPath, doc, "utf-8");
  console.log(`${listings.length} items written to ${outPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
