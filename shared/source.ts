/**
 * Where a visitor came from. Social DM automations link to the site with
 * `?ref=ig` (or tt, fb, yt…); the page keeps it for the visit and every lead
 * and order records it, so Airtable shows which channel produced the sale.
 */

const CHANNELS: Record<string, string> = {
  ig: "Instagram DM",
  instagram: "Instagram DM",
  tt: "TikTok DM",
  tiktok: "TikTok DM",
  fb: "Facebook DM",
  facebook: "Facebook DM",
  yt: "YouTube",
  youtube: "YouTube",
  dm: "Social DM",
};

/** Normalizes a raw `ref` value; anything unusual is reduced to safe characters. */
export function cleanRef(ref: string | null | undefined): string | undefined {
  const cleaned = (ref ?? "").toLowerCase().replace(/[^a-z0-9_-]/g, "").slice(0, 24);
  return cleaned || undefined;
}

/** "jayleefit.com Ask Jay chat" → "Instagram DM → jayleefit.com Ask Jay chat" when a ref is known. */
export function sourceLabel(ref: string | null | undefined, base: string): string {
  const key = cleanRef(ref);
  if (!key) return base;
  return `${CHANNELS[key] ?? `ref:${key}`} → ${base}`;
}
