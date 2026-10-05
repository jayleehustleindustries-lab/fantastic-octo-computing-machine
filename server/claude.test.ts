import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const create = vi.fn();
vi.mock("@anthropic-ai/sdk", () => ({
  default: class {
    beta = { messages: { create } };
  },
}));

import { claudeConfigured, generateBlueprint, resetBlueprintLimits, takeBlueprintSlot } from "./claude";

beforeEach(() => {
  create.mockReset();
  resetBlueprintLimits();
});

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("generateBlueprint", () => {
  it("is off until ANTHROPIC_API_KEY is set", async () => {
    vi.stubEnv("ANTHROPIC_API_KEY", "");
    expect(claudeConfigured()).toBe(false);
    await expect(generateBlueprint("system", "goals")).rejects.toThrow(/not configured/);
    expect(create).not.toHaveBeenCalled();
  });

  it("sends the MAO prompt and returns the plan text", async () => {
    vi.stubEnv("ANTHROPIC_API_KEY", "sk-test");
    create.mockResolvedValue({
      stop_reason: "end_turn",
      content: [
        { type: "thinking", thinking: "" },
        { type: "text", text: "OPERATOR READOUT\nTrain 4x a week." },
      ],
    });

    const plan = await generateBlueprint("You are the MAO Engine", "Goals: build strength");

    expect(plan).toBe("OPERATOR READOUT\nTrain 4x a week.");
    const params = create.mock.calls[0][0];
    expect(params).toMatchObject({
      model: "claude-opus-5-5",
      system: "You are the MAO Engine",
      messages: [{ role: "user", content: "Goals: build strength" }],
      output_config: { effort: "low" },
      fallbacks: "default",
      betas: ["server-side-fallback-2026-07-01"],
    });
  });

  it("turns a refusal into a readable error", async () => {
    vi.stubEnv("ANTHROPIC_API_KEY", "sk-test");
    create.mockResolvedValue({ stop_reason: "refusal", content: [] });
    await expect(generateBlueprint("s", "u")).rejects.toThrow(/couldn't write a plan/);
  });
});

describe("takeBlueprintSlot", () => {
  it("allows 5 plans per visitor per hour", () => {
    const start = 1_000_000;
    for (let i = 0; i < 5; i++) expect(takeBlueprintSlot("1.2.3.4", start + i)).toBe(true);
    expect(takeBlueprintSlot("1.2.3.4", start + 10)).toBe(false);
    expect(takeBlueprintSlot("5.6.7.8", start + 10)).toBe(true);
    expect(takeBlueprintSlot("1.2.3.4", start + 60 * 60 * 1000 + 1)).toBe(true);
  });
});
