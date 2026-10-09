import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const create = vi.fn();
vi.mock("@anthropic-ai/sdk", () => ({
  default: class {
    beta = { messages: { create } };
  },
}));

import { askJay, SAVE_LEAD_TOOL } from "./chat";
import { ASK_JAY_SYSTEM_PROMPT } from "./chatPrompt";

const text = (t: string) => ({ type: "text", text: t });
const reply = (t: string) => ({ stop_reason: "end_turn", content: [{ type: "thinking", thinking: "", signature: "sig" }, text(t)] });
const saveCall = (input: Record<string, unknown>) => ({
  stop_reason: "tool_use",
  content: [{ type: "thinking", thinking: "", signature: "sig" }, { type: "tool_use", id: "toolu_1", name: "save_lead", input }],
});

const history = [{ role: "user" as const, content: "What's in Recomp?" }];
const goodLead = { name: "Sam", email: "sam@example.com", goal: "Lose fat", summary: "Busy dad.", ready_to_apply: true, next: "remap" };

beforeEach(() => {
  create.mockReset();
  vi.stubEnv("ANTHROPIC_API_KEY", "sk-test");
});

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("askJay", () => {
  it("is off until ANTHROPIC_API_KEY is set", async () => {
    vi.stubEnv("ANTHROPIC_API_KEY", "");
    await expect(askJay(history, vi.fn())).rejects.toThrow(/not switched on/);
    expect(create).not.toHaveBeenCalled();
  });

  it("answers free visitors on Haiku 5.5 with the cached Ask Jay prompt", async () => {
    create.mockResolvedValue(reply("Recomp adds weekly calls."));
    const result = await askJay(history, vi.fn());

    expect(result).toEqual({ reply: "Recomp adds weekly calls.", lead: undefined });
    const params = create.mock.calls[0][0];
    // Haiku has no server-side fallback, so the request carries no fallback beta.
    expect(params.betas).toBeUndefined();
    expect(params.fallbacks).toBeUndefined();
    expect(params).toMatchObject({
      model: "claude-haiku-5-5",
      output_config: { effort: "low" },
      cache_control: { type: "ephemeral" },
      system: ASK_JAY_SYSTEM_PROMPT,
      tools: [SAVE_LEAD_TOOL],
      tool_choice: { type: "auto" },
      messages: [{ role: "user", content: "What's in Recomp?" }],
    });
  });

  it("keeps only the latest 20 turns, starting on a visitor message", async () => {
    create.mockResolvedValue(reply("ok"));
    const long = Array.from({ length: 25 }, (_, i) => ({ role: (i % 2 ? "assistant" : "user") as "user" | "assistant", content: `m${i}` }));
    await askJay(long, vi.fn());
    const sent = create.mock.calls[0][0].messages;
    expect(sent[0]).toEqual({ role: "user", content: "m6" });
    expect(sent.at(-1)).toEqual({ role: "user", content: "m24" });
  });

  it("saves a lead through the tool and reports it to the page", async () => {
    create.mockResolvedValueOnce(saveCall(goodLead)).mockResolvedValueOnce(reply("You're all set."));
    const saveLead = vi.fn().mockResolvedValue(undefined);

    const result = await askJay(history, saveLead);

    expect(saveLead).toHaveBeenCalledWith({ name: "Sam", email: "sam@example.com", goal: "Lose fat", summary: "Busy dad.", readyToApply: true, next: "remap" });
    expect(result).toEqual({ reply: "You're all set.", lead: { name: "Sam", email: "sam@example.com", goal: "Lose fat", next: "remap" } });
    const followUp = create.mock.calls[1][0].messages;
    // The assistant turn goes back unchanged (thinking included), then the tool result.
    expect(followUp[1]).toEqual({ role: "assistant", content: saveCall(goodLead).content });
    expect(followUp[2].content[0]).toMatchObject({ type: "tool_result", tool_use_id: "toolu_1" });
    expect(followUp[2].content[0].is_error).toBeUndefined();
    expect(followUp[2].content[0].content).toContain("Build my Remap");
  });

  it("rejects a malformed email without saving", async () => {
    create.mockResolvedValueOnce(saveCall({ ...goodLead, email: "sam at example" })).mockResolvedValueOnce(reply("Can you check that email?"));
    const saveLead = vi.fn();
    const result = await askJay(history, saveLead);
    expect(saveLead).not.toHaveBeenCalled();
    expect(result.lead).toBeUndefined();
    expect(create.mock.calls[1][0].messages[2].content[0]).toMatchObject({ is_error: true });
  });

  it("keeps storage errors out of the conversation", async () => {
    create.mockResolvedValueOnce(saveCall(goodLead)).mockResolvedValueOnce(reply("Please use the Apply section."));
    const errorLog = vi.spyOn(console, "error").mockImplementation(() => {});
    const result = await askJay(history, vi.fn().mockRejectedValue(new Error("Airtable 401: bad token")));
    const toolResult = create.mock.calls[1][0].messages[2].content[0];
    expect(toolResult.is_error).toBe(true);
    expect(toolResult.content).not.toContain("Airtable");
    expect(result.lead).toBeUndefined();
    errorLog.mockRestore();
  });

  it("turns a refusal into a friendly redirect", async () => {
    create.mockResolvedValue({ stop_reason: "refusal", content: [] });
    const result = await askJay(history, vi.fn());
    expect(result.reply).toMatch(/JayLee Fit coaching/);
  });
});

describe("Ask Jay prompt", () => {
  it("knows the packages but never carries prices", () => {
    expect(ASK_JAY_SYSTEM_PROMPT).toContain("RECOMP");
    expect(ASK_JAY_SYSTEM_PROMPT).toContain("Never quote, estimate, or hint at prices");
    expect(ASK_JAY_SYSTEM_PROMPT).not.toMatch(/\$\s?\d/);
  });

  it("sells Remap without giving away its numbers for free", () => {
    expect(ASK_JAY_SYSTEM_PROMPT).toContain("REMAP: buy now, no application");
    expect(ASK_JAY_SYSTEM_PROMPT).toContain("don't calculate their calories, BMR, or macros");
  });

  it("introduces itself as an AI assistant, not Coach Jay", () => {
    expect(ASK_JAY_SYSTEM_PROMPT).toContain("You are an AI assistant, not Coach Jay himself");
  });
});
