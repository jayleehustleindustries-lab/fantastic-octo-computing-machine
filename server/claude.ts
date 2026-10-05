import Anthropic from "@anthropic-ai/sdk";

/**
 * The sample-blueprint generator runs on the Claude API. It replaces the
 * Manus Forge endpoint, which only exists inside Manus. The button is enabled
 * when ANTHROPIC_API_KEY is set.
 */

export const BLUEPRINT_MODEL = process.env.ANTHROPIC_MODEL || "claude-opus-5-5";

export function claudeConfigured(): boolean {
  return Boolean(process.env.ANTHROPIC_API_KEY);
}

let client: Anthropic | null = null;
function getClient(): Anthropic {
  client ??= new Anthropic();
  return client;
}

export async function generateBlueprint(system: string, userMessage: string): Promise<string> {
  if (!claudeConfigured()) throw new Error("The AI blueprint generator is not configured.");

  const response = await getClient().beta.messages.create({
    model: BLUEPRINT_MODEL,
    // Thinking shares this budget, so leave room beyond the ~600-word plan.
    max_tokens: 8000,
    output_config: { effort: "low" },
    // On a safety decline, the API reruns the request on a fallback model.
    betas: ["server-side-fallback-2026-07-01"],
    fallbacks: "default",
    system,
    messages: [{ role: "user", content: userMessage }],
  });

  if (response.stop_reason === "refusal") {
    throw new Error("The generator couldn't write a plan for that request. Try rephrasing your goals.");
  }

  const text = response.content
    .flatMap(block => (block.type === "text" ? [block.text] : []))
    .join("")
    .trim();
  if (!text) throw new Error("The generator returned an empty plan. Please try again.");
  return text;
}

// ── Per-visitor limit ───────────────────────────────────────────────────────
// The generator is public, so cap how often one visitor can run it. This lives
// in memory: it resets on redeploy and is per-replica, which is enough for a
// single small instance.

const WINDOW_MS = 60 * 60 * 1000;
const MAX_PER_WINDOW = 5;
const hits = new Map<string, number[]>();

export function takeBlueprintSlot(key: string, now = Date.now()): boolean {
  const recent = (hits.get(key) ?? []).filter(t => now - t < WINDOW_MS);
  if (recent.length >= MAX_PER_WINDOW) {
    hits.set(key, recent);
    return false;
  }
  recent.push(now);
  hits.set(key, recent);
  if (hits.size > 10_000) {
    for (const [k, times] of Array.from(hits.entries())) {
      if (times.every(t => now - t >= WINDOW_MS)) hits.delete(k);
    }
  }
  return true;
}

export function resetBlueprintLimits() {
  hits.clear();
}
