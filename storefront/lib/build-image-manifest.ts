/**
 * Scans public/products/ and regenerates lib/product-images.generated.ts.
 *
 * Layout is one folder per SKU, which keeps SKU parsing unambiguous — EHC
 * SKUs contain hyphens *and* end in digits (`A1-MD-0001`), so any
 * `<SKU>-<n>.jpg` filename convention would be impossible to split
 * reliably. A folder name is the SKU, full stop:
 *
 *   public/products/A1-MD-0001/1.jpg   ->  /products/A1-MD-0001/1.jpg
 *   public/products/A1-MD-0001/2.jpg   ->  /products/A1-MD-0001/2.jpg
 *
 * Run with:
 *   npx tsx lib/build-image-manifest.ts
 */
import { readdirSync, statSync, writeFileSync, existsSync } from "fs";
import { join, extname, relative } from "path";

const PRODUCTS_DIR = join(process.cwd(), "public", "products");
const OUTPUT_FILE = join(process.cwd(), "lib", "product-images.generated.ts");

const IMAGE_EXTENSIONS = new Set([".jpg", ".jpeg", ".png", ".webp", ".avif"]);

/** "2.jpg" before "10.jpg" — plain string sort would put 10 first. */
function naturalCompare(a: string, b: string): number {
  return a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" });
}

function collect(): Record<string, string[]> {
  const manifest: Record<string, string[]> = {};
  if (!existsSync(PRODUCTS_DIR)) return manifest;

  for (const sku of readdirSync(PRODUCTS_DIR).sort(naturalCompare)) {
    const skuDir = join(PRODUCTS_DIR, sku);
    if (!statSync(skuDir).isDirectory()) continue;

    const images = readdirSync(skuDir)
      .filter((file) => IMAGE_EXTENSIONS.has(extname(file).toLowerCase()))
      .sort(naturalCompare)
      .map((file) => `/${relative(join(process.cwd(), "public"), join(skuDir, file))}`);

    if (images.length > 0) manifest[sku.toUpperCase()] = images;
  }

  return manifest;
}

function render(manifest: Record<string, string[]>): string {
  const entries = Object.entries(manifest)
    .map(([sku, images]) => {
      const list = images.map((i) => `    ${JSON.stringify(i)},`).join("\n");
      return `  ${JSON.stringify(sku)}: [\n${list}\n  ],`;
    })
    .join("\n");

  return `/**
 * AUTO-GENERATED — do not edit by hand.
 *
 * Regenerate after adding or removing photos:
 *   npx tsx lib/build-image-manifest.ts
 *
 * Maps a SKU to the public URLs of its photos, so the storefront can show
 * real inventory photos without needing an \`Images\` column written into the
 * Google Sheet (there's no write access to that sheet — see CLAUDE.md).
 */

export const PRODUCT_IMAGES: Record<string, string[]> = {${
    entries ? `\n${entries}\n` : ""
  }};
`;
}

const manifest = collect();
writeFileSync(OUTPUT_FILE, render(manifest), "utf-8");

const skuCount = Object.keys(manifest).length;
const imageCount = Object.values(manifest).reduce((n, list) => n + list.length, 0);
console.log(
  `Wrote ${relative(process.cwd(), OUTPUT_FILE)} — ${skuCount} SKU(s), ${imageCount} image(s).`
);
