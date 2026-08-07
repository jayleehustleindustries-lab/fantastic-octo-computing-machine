/**
 * Writes a Vendoo-shaped CSV of available EHC inventory, plus a summary
 * of what isn't listable yet and why.
 *
 * Reads the real EHC Inventory Log either from the live Sheet CSV export
 * or from a local CSV (the sandbox's network policy blocks Google hosts,
 * so a local export is the usual path here).
 *
 * Run with:
 *   npx tsx lib/marketplace-export/generate-vendoo.ts [out.csv] [--csv=local.csv] [--base-url=https://yourdomain.com]
 *
 * --base-url turns the repo-relative photo paths (/products/<SKU>/1.jpg)
 * into absolute URLs, which is what any importer will need. Leave it off
 * while the site isn't deployed yet.
 */
import { readFileSync, writeFileSync } from "fs";
import { csvToObjects } from "../csv";
import { isAvailable } from "../products";
import {
  alreadyOnVendoo,
  rowToVendooListing,
  toCsvRow,
  VENDOO_COLUMNS,
  type VendooListing,
} from "./vendoo";

const SHEET_ID =
  process.env.GOOGLE_SHEET_ID || "1-UcTy4Cr_NPK622SPRXob7LfpHFEw5874mv9y5E90Ys";
const SHEET_NAME = process.env.GOOGLE_SHEET_NAME || "Inventory";

async function loadCsv(localCsvPath: string | null): Promise<string> {
  if (localCsvPath) return readFileSync(localCsvPath, "utf-8");
  const url = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:csv&sheet=${encodeURIComponent(
    SHEET_NAME
  )}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch sheet: ${res.status} ${res.statusText}`);
  return res.text();
}

/** Reasons an item can't go out yet — reported rather than silently dropped. */
function blockers(listing: VendooListing): string[] {
  const problems: string[] = [];
  if (listing.photos.length === 0) problems.push("no photo assigned");
  if (!listing.price) problems.push("no price");
  if (!listing.size) problems.push("no size");
  if (!listing.description) problems.push("no description");
  return problems;
}

async function main() {
  const args = process.argv.slice(2);
  const csvArg = args.find((a) => a.startsWith("--csv="));
  const baseArg = args.find((a) => a.startsWith("--base-url="));
  const outPath = args.find((a) => !a.startsWith("--")) || "vendoo-import.csv";
  const baseUrl = baseArg ? baseArg.slice("--base-url=".length) : "";

  const rows = csvToObjects(await loadCsv(csvArg ? csvArg.slice("--csv=".length) : null));

  const candidates = rows.filter(
    (row) =>
      isAvailable(row["Inventory Status"] || "", row["Condition"] || "") && !alreadyOnVendoo(row)
  );

  const listings = candidates
    .map(rowToVendooListing)
    .filter((l): l is VendooListing => l !== null);

  const ready = listings.filter((l) => blockers(l).length === 0);
  const notReady = listings.filter((l) => blockers(l).length > 0);

  writeFileSync(
    outPath,
    [VENDOO_COLUMNS.join(","), ...ready.map((l) => toCsvRow(l, baseUrl))].join("\n") + "\n",
    "utf-8"
  );

  console.log(`${rows.length} row(s) in sheet.`);
  console.log(`${candidates.length} available and not already on Vendoo.`);
  console.log(`${ready.length} fully ready -> ${outPath}`);
  if (!baseUrl) {
    console.log("  (photo paths are site-relative — pass --base-url once deployed)");
  }

  if (notReady.length > 0) {
    console.log(`\n${notReady.length} not ready yet:`);
    const byReason = new Map<string, number>();
    for (const l of notReady) {
      for (const reason of blockers(l)) {
        byReason.set(reason, (byReason.get(reason) ?? 0) + 1);
      }
    }
    for (const [reason, count] of [...byReason].sort((a, b) => b[1] - a[1])) {
      console.log(`  ${String(count).padStart(3)}  ${reason}`);
    }
    console.log("\nFirst 10 blocked SKUs:");
    for (const l of notReady.slice(0, 10)) {
      console.log(`  ${l.sku.padEnd(12)} ${blockers(l).join(", ")}`);
    }
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
