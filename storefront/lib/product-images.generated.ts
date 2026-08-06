/**
 * AUTO-GENERATED — do not edit by hand.
 *
 * Regenerate after adding or removing photos:
 *   npx tsx lib/build-image-manifest.ts
 *
 * Maps a SKU to the public URLs of its photos, so the storefront can show
 * real inventory photos without needing an `Images` column written into the
 * Google Sheet (there's no write access to that sheet — see CLAUDE.md).
 */

export const PRODUCT_IMAGES: Record<string, string[]> = {};
