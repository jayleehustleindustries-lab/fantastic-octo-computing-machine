import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { upsertApplication } from "./db";
import { mergePhaseNotes } from "./airtable";

type Call = { url: string; rawUrl: string; method: string; body: any };
let calls: Call[];

function mockAirtable(existing: { id: string; fields: Record<string, unknown> } | null) {
  calls = [];
  vi.stubGlobal("fetch", vi.fn(async (url: string, init: RequestInit = {}) => {
    const method = init.method ?? "GET";
    const body = init.body ? JSON.parse(String(init.body)) : undefined;
    calls.push({ url: decodeURIComponent(url), rawUrl: url, method, body });
    const records = method === "GET"
      ? (existing ? [existing] : [])
      : [{ id: body.records[0].id ?? "recNEW", fields: body.records[0].fields }];
    return new Response(JSON.stringify({ records }), { status: 200 });
  }));
}

beforeEach(() => {
  vi.stubEnv("AIRTABLE_API_TOKEN", "pat_test");
  vi.stubEnv("AIRTABLE_BASE_ID", "appTEST");
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

const phase1 = { email: "op@test.com", fullName: "Test Operator", phone: "", location: "Hot Springs, AR" };

describe("upsertApplication → Airtable Lead Pipeline", () => {
  it("creates a new lead on phase 1", async () => {
    mockAirtable(null);
    await upsertApplication("op@test.com", { fullName: "Test Operator", phase1Json: JSON.stringify(phase1) });

    expect(calls.map(c => c.method)).toEqual(["GET", "POST"]);
    expect(calls[0].url).toContain("Lead Pipeline");
    const fields = calls[1].body.records[0].fields;
    expect(fields).toMatchObject({
      "Lead Name": "Test Operator",
      Email: "op@test.com",
      Source: "jayleefit.com MAO application",
      "Funnel Stage": "Application — phase 1 of 4",
    });
    expect(fields["Created Date"]).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(fields.Notes).toContain("Location / timezone: Hot Springs, AR");
    expect(fields.Notes).not.toContain("op@test.com");
    expect(fields.Notes).not.toContain("Phone");
  });

  it("updates the same lead on later phases, keeping the coach's own notes", async () => {
    mockAirtable({
      id: "recEXISTING",
      fields: { Notes: "Called 9/28 — strong fit\n\n── Phase 1 — Identity ──\nFull name: Test Operator" },
    });
    await upsertApplication("op@test.com", {
      phase2Json: JSON.stringify({ email: "op@test.com", goal: "Drop 15 lbs", trainingFrequency: "3x", trainingHistory: "2 yrs" }),
    });

    expect(calls.map(c => c.method)).toEqual(["GET", "PATCH"]);
    const record = calls[1].body.records[0];
    expect(record.id).toBe("recEXISTING");
    expect(record.fields["Funnel Stage"]).toBe("Application — phase 2 of 4");
    expect(record.fields.Notes.indexOf("Called 9/28")).toBe(0);
    expect(record.fields.Notes.indexOf("Phase 1")).toBeLessThan(record.fields.Notes.indexOf("Phase 2"));
    expect(record.fields).not.toHaveProperty("Source");
  });

  it("marks the lead complete after phase 4", async () => {
    mockAirtable({ id: "recX", fields: { Notes: "" } });
    await upsertApplication("op@test.com", {
      phase4Json: JSON.stringify({ email: "op@test.com", whyNow: "Ready", startWindow: "IMMEDIATELY", investmentAck: true, reviewAgreement: true }),
      completedAt: new Date(),
    });
    const fields = calls[1].body.records[0].fields;
    expect(fields["Funnel Stage"]).toBe("Application complete");
    expect(fields.Notes).toContain("Investment acknowledged: Yes");
  });

  it("escapes apostrophes in the email lookup", async () => {
    mockAirtable(null);
    await upsertApplication("o'neil@test.com", { phase1Json: JSON.stringify({ ...phase1, email: "o'neil@test.com" }) });
    const formula = new URL(calls[0].rawUrl).searchParams.get("filterByFormula");
    expect(formula).toBe("LOWER({Email}) = 'o\\'neil@test.com'");
  });

  it("surfaces Airtable errors instead of silently dropping the application", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ error: { message: "Invalid permissions" } }), { status: 403 })));
    await expect(upsertApplication("op@test.com", { phase1Json: JSON.stringify(phase1) })).rejects.toThrow("Airtable 403: Invalid permissions");
  });
});

describe("mergePhaseNotes", () => {
  it("replaces a resubmitted phase instead of duplicating it", () => {
    const first = mergePhaseNotes("", 1, "── Phase 1 — Identity ──\nFull name: A");
    const again = mergePhaseNotes(first.notes, 1, "── Phase 1 — Identity ──\nFull name: B");
    expect(again.notes).toBe("── Phase 1 — Identity ──\nFull name: B");
    expect(again.furthest).toBe(1);
  });
});
