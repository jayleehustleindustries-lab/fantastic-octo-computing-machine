import { beforeEach, describe, expect, it, vi } from "vitest";
import { claudeConfigured, resetLimits, takeSlot } from "./claude";

beforeEach(() => {
  resetLimits();
  vi.unstubAllEnvs();
});

describe("claudeConfigured", () => {
  it("follows ANTHROPIC_API_KEY", () => {
    vi.stubEnv("ANTHROPIC_API_KEY", "");
    expect(claudeConfigured()).toBe(false);
    vi.stubEnv("ANTHROPIC_API_KEY", "sk-test");
    expect(claudeConfigured()).toBe(true);
  });
});

describe("takeSlot", () => {
  it("allows max uses per visitor per hour, per bucket", () => {
    const start = 1_000_000;
    for (let i = 0; i < 5; i++) expect(takeSlot("chat", "1.2.3.4", 5, start + i)).toBe(true);
    expect(takeSlot("chat", "1.2.3.4", 5, start + 10)).toBe(false);
    expect(takeSlot("lead", "1.2.3.4", 5, start + 10)).toBe(true);
    expect(takeSlot("chat", "5.6.7.8", 5, start + 10)).toBe(true);
    expect(takeSlot("chat", "1.2.3.4", 5, start + 60 * 60 * 1000 + 1)).toBe(true);
  });
});
