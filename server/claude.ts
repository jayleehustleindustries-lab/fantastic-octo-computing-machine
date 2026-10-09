import Anthropic from "@anthropic-ai/sdk";

/**
 * Claude API access, shared by Ask Jay (free, Haiku) and Remap builds (paid,
 * Opus). Switched on when ANTHROPIC_API_KEY is set; without it the site shows
 * the browser-only plan builder instead of the chat.
 */

export function claudeConfigured(): boolean {
  return Boolean(process.env.ANTHROPIC_API_KEY);
}

let client: Anthropic | null = null;
export function getClaude(): Anthropic {
  client ??= new Anthropic();
  return client;
}

// ── Per-visitor limits ──────────────────────────────────────────────────────
// The assistant is public, so cap how often one visitor can use it. This lives
// in memory: it resets on redeploy and is per-replica, which is enough for a
// single small instance.

const WINDOW_MS = 60 * 60 * 1000;
const hits = new Map<string, number[]>();

/** Records one use of `bucket` by `key`; false once `max` uses fall inside the last hour. */
export function takeSlot(bucket: string, key: string, max: number, now = Date.now()): boolean {
  const id = `${bucket}:${key}`;
  const recent = (hits.get(id) ?? []).filter(t => now - t < WINDOW_MS);
  if (recent.length >= max) {
    hits.set(id, recent);
    return false;
  }
  recent.push(now);
  hits.set(id, recent);
  if (hits.size > 10_000) {
    for (const [k, times] of Array.from(hits.entries())) {
      if (times.every(t => now - t >= WINDOW_MS)) hits.delete(k);
    }
  }
  return true;
}

export function resetLimits() {
  hits.clear();
}
