/**
 * Assigns a photo from photo-inbox/ to a SKU, then regenerates the manifest.
 *
 * The inbox holds already-edited photos pulled out of Drive that aren't
 * matched to inventory rows yet — nothing in a phone filename says which
 * item it is, so that match is a human call. This makes acting on that
 * call one command instead of a mkdir, a mv, and a remembered rebuild.
 *
 *   npx tsx lib/assign-photo.ts IMG_2109-Photoroom.jpg A1-MD-0003
 *
 * Appends as the next free index in public/products/<SKU>/, so running it
 * repeatedly for the same SKU builds up that item's photo set in order.
 * Pass --copy to leave the inbox file in place instead of moving it.
 */
import { existsSync, mkdirSync, readdirSync, renameSync, copyFileSync } from "fs";
import { join, extname, basename } from "path";
import { execFileSync } from "child_process";

const INBOX = join(process.cwd(), "photo-inbox");
const PRODUCTS = join(process.cwd(), "public", "products");

function fail(message: string): never {
  console.error(`error: ${message}`);
  process.exit(1);
}

const args = process.argv.slice(2);
const copyOnly = args.includes("--copy");
const [fileArg, skuArg] = args.filter((a) => !a.startsWith("--"));

if (!fileArg || !skuArg) {
  fail("usage: npx tsx lib/assign-photo.ts <file-in-photo-inbox> <SKU> [--copy]");
}

const sku = skuArg.trim().toUpperCase();
const source = join(INBOX, basename(fileArg));
if (!existsSync(source)) fail(`no such file in photo-inbox/: ${basename(fileArg)}`);

const skuDir = join(PRODUCTS, sku);
mkdirSync(skuDir, { recursive: true });

// Next free index, so repeated calls append rather than overwrite.
const used = readdirSync(skuDir)
  .map((f) => parseInt(basename(f, extname(f)), 10))
  .filter((n) => !Number.isNaN(n));
const nextIndex = used.length > 0 ? Math.max(...used) + 1 : 1;

const target = join(skuDir, `${nextIndex}${extname(source).toLowerCase()}`);
if (copyOnly) copyFileSync(source, target);
else renameSync(source, target);

console.log(
  `${copyOnly ? "Copied" : "Moved"} ${basename(source)} -> public/products/${sku}/${basename(target)}`
);

execFileSync("npx", ["tsx", join("lib", "build-image-manifest.ts")], { stdio: "inherit" });
