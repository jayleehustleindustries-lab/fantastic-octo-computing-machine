/**
 * Writes one combined Markdown document of Facebook Marketplace-ready
 * listing copy — one block per available item, ready to copy-paste into
 * FB's own posting form. Reads the real EHC Inventory Log either by
 * fetching the live Sheet CSV export directly, or from a local CSV file
 * (e.g. exported via the Google Drive connector, for sandboxes whose
 * network policy blocks docs.google.com directly).
 *
 * Run with: npx tsx lib/marketplace-export/generate.ts [output-path] [--csv=path/to/local.csv]
 */
import { readFileSync, writeFileSync } from "fs";
import { csvToObjects } from "../csv";
import { isAvailable } from "../products";
import { alreadyOnFacebook, rowToFacebookListing, type FacebookListing } from "./facebook";

const SHEET_ID =
  process.env.GOOGLE_SHEET_ID || "1-UcTy4Cr_NPK622SPRXob7LfpHFEw5874mv9y5E90Ys";
const SHEET_NAME = process.env.GOOGLE_SHEET_NAME || "Inventory";

function renderListing(listing: FacebookListing): string {
  return [
    `## ${listing.title}`,
    "",
    `- **SKU:** ${listing.sku}`,
    `- **Price:** $${listing.price}`,
    `- **Category:** ${listing.category}`,
    `- **Condition:** ${listing.condition}`,
    "",
    "**Description (paste as-is):**",
    "",
    "```",
    listing.description,
    "```",
    "",
    `_${listing.photoNote}_`,
    "",
    "---",
  ].join("\n");
}

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

  const available = rows.filter(
    (row) =>
      isAvailable(row["Inventory Status"] || "", row["Condition"] || "") &&
      !alreadyOnFacebook(row)
  );
  const listings = available
    .map(rowToFacebookListing)
    .filter((l): l is FacebookListing => l !== null);

  const doc = [
    "# Facebook Marketplace listing copy — EHC Inventory",
    "",
    `Generated ${new Date().toISOString().slice(0, 10)} from the live EHC Inventory Log.`,
    `${listings.length} listing(s) below, ready to copy-paste one at a time into` +
      " Facebook Marketplace's own posting form. Photos still need manual upload —" +
      " there's no URL-based photo import on Facebook. Items already marked Facebook" +
      " in the sheet's Listing Platforms column are left off this list.",
    "",
    "---",
    "",
    ...listings.map(renderListing),
  ].join("\n");

  const outPath =
    process.argv.slice(2).find((a) => !a.startsWith("--")) || "facebook-marketplace-listings.md";
  writeFileSync(outPath, doc, "utf-8");
  console.log(`${listings.length} listings written to ${outPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
