/**
 * Crosslists available EHC inventory to eBay via the real Sell API.
 *
 * Dry-run by default — prints what each item would resolve to
 * (category, condition options) and what would be created, without
 * calling the publish endpoint. Only publishes for real with an
 * explicit --publish flag, one item at a time, printing a confirmation
 * after each one actually goes live.
 *
 * Run with:
 *   npx tsx lib/ebay-sync/sync.ts --csv=path/to/local.csv           (dry run)
 *   npx tsx lib/ebay-sync/sync.ts --csv=path/to/local.csv --publish (real listings)
 *
 * Defaults to EBAY_ENV=sandbox — set EBAY_ENV=production only once a
 * sandbox dry run has been checked and looks right.
 */
import { readFileSync } from "fs";
import { csvToObjects } from "../csv";
import { isAvailable } from "../products";
import { alreadyOnEbay, rowToEbayDraft, type EbayListingDraft } from "./ebay";
import {
  createOffer,
  createOrReplaceInventoryItem,
  getCategorySuggestions,
  getItemConditionPolicies,
  publishOffer,
  EBAY_ENV,
} from "./client";

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

/** Picks the closest condition to the item's own 1-10 score from eBay's real, category-specific options. */
function pickCondition(
  score: number,
  options: { conditionId: string; conditionDescription: string }[]
): { conditionId: string; conditionDescription: string } | null {
  if (options.length === 0) return null;
  // No universal ordering across categories, so this is a best-effort text
  // match, not a numeric one — flagged in dry-run output for a human check.
  const wantsHigh = score >= 8;
  const preferred = options.find((o) =>
    wantsHigh
      ? /excellent|very good|like new/i.test(o.conditionDescription)
      : /good|acceptable|fair/i.test(o.conditionDescription)
  );
  return preferred ?? options[0];
}

async function processItem(draft: EbayListingDraft, publish: boolean): Promise<void> {
  const category = await getCategorySuggestions(draft.categorySearchQuery);
  if (!category) {
    console.log(`  SKIP ${draft.sku} — no eBay category match for "${draft.categorySearchQuery}"`);
    return;
  }

  const conditions = await getItemConditionPolicies(category.categoryId);
  const condition = pickCondition(draft.conditionScore, conditions);
  if (!condition) {
    console.log(`  SKIP ${draft.sku} — no condition options returned for category ${category.categoryId}`);
    return;
  }

  console.log(
    `  ${draft.sku} — "${draft.title}" — $${draft.price} — category ${category.categoryId} (${category.categoryName}) — condition ${condition.conditionId} (${condition.conditionDescription})`
  );

  if (!publish) return;

  await createOrReplaceInventoryItem(draft.sku, {
    product: {
      title: draft.title,
      description: draft.description,
      imageUrls: draft.images,
    },
    condition: condition.conditionId,
    conditionDescription: draft.description,
    availability: {
      shipToLocationAvailability: { quantity: draft.quantity },
    },
  });

  const offer = await createOffer({
    sku: draft.sku,
    marketplaceId: "EBAY_US",
    format: "FIXED_PRICE",
    availableQuantity: draft.quantity,
    categoryId: category.categoryId,
    pricingSummary: { price: { value: draft.price.toFixed(2), currency: "USD" } },
    listingDescription: draft.description,
  });

  const published = await publishOffer(offer.offerId);
  console.log(`  PUBLISHED ${draft.sku} — eBay listing ID ${published.listingId} (${EBAY_ENV})`);
  console.log(`  ↳ Mark "eBay" in this row's Listing Platforms column in the sheet.`);
}

async function main() {
  const args = process.argv.slice(2);
  const publish = args.includes("--publish");
  const csvArg = args.find((a) => a.startsWith("--csv="));
  const localCsvPath = csvArg ? csvArg.slice("--csv=".length) : null;

  const csv = await loadCsv(localCsvPath);
  const rows = csvToObjects(csv);

  const candidates = rows.filter(
    (row) =>
      isAvailable(row["Inventory Status"] || "", row["Condition"] || "") && !alreadyOnEbay(row)
  );
  const drafts = candidates
    .map(rowToEbayDraft)
    .filter((d): d is EbayListingDraft => d !== null);

  console.log(
    `${drafts.length} item(s) eligible for eBay (not already listed there), environment: ${EBAY_ENV}.`
  );
  console.log(publish ? "PUBLISH MODE — real listings will be created.\n" : "DRY RUN — nothing will be published.\n");

  for (const draft of drafts) {
    await processItem(draft, publish);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
