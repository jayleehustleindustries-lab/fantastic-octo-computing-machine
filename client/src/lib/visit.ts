import { cleanRef } from "@shared/source";

/**
 * Per-visit details kept in sessionStorage: where the visitor came from
 * (`?ref=ig` on a social DM link) and anything Ask Jay hands to the Remap form.
 */

const REF_KEY = "jlfRef";
const REMAP_PREFILL_KEY = "remapPrefill";

function read(key: string): string | null {
  try { return sessionStorage.getItem(key); } catch { return null; }
}
function write(key: string, value: string) {
  try { sessionStorage.setItem(key, value); } catch {}
}

/** Call once on page load; keeps the first ref seen this visit. */
export function captureRef() {
  const ref = cleanRef(new URLSearchParams(window.location.search).get("ref"));
  if (ref && !read(REF_KEY)) write(REF_KEY, ref);
}

export const visitRef = (): string | undefined => read(REF_KEY) ?? undefined;

export type RemapPrefill = { name?: string; email?: string; goalNote?: string };

export function setRemapPrefill(prefill: RemapPrefill) {
  write(REMAP_PREFILL_KEY, JSON.stringify(prefill));
}

export function takeRemapPrefill(): RemapPrefill | null {
  const raw = read(REMAP_PREFILL_KEY);
  if (!raw) return null;
  try { sessionStorage.removeItem(REMAP_PREFILL_KEY); } catch {}
  try { return JSON.parse(raw); } catch { return null; }
}
