import { describe, expect, it, vi, beforeEach } from "vitest";

// ── Mock the DB helpers so tests don't need a real database ─────────────────
vi.mock("./db", () => ({
  upsertApplication: vi.fn().mockResolvedValue({ id: 1 }),
  getApplicationByEmail: vi.fn().mockResolvedValue(null),
  createAiPlan: vi.fn().mockResolvedValue({ id: 1 }),
  createPaymentReport: vi.fn().mockResolvedValue({ id: 1 }),
}));

// ── Mock the Claude call so tests don't make real API calls ──────────────────
vi.mock("./claude", async importOriginal => ({
  ...(await importOriginal<typeof import("./claude")>()),
  generateBlueprint: vi.fn().mockResolvedValue("## OPERATOR READOUT\nTest plan generated."),
}));

import { appRouter } from "./routers";
import type { TrpcContext } from "./_core/context";

function createPublicContext(): TrpcContext {
  return {
    user: null,
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: { clearCookie: vi.fn() } as unknown as TrpcContext["res"],
  };
}

describe("application.submitPhase1", () => {
  it("accepts valid phase 1 input and returns success", async () => {
    const caller = appRouter.createCaller(createPublicContext());
    const result = await caller.application.submitPhase1({
      email: "operator@test.com",
      fullName: "Test Operator",
      location: "Austin, TX",
    });
    expect(result.success).toBe(true);
    expect(result.id).toBe(1);
  });

  it("rejects invalid email", async () => {
    const caller = appRouter.createCaller(createPublicContext());
    await expect(
      caller.application.submitPhase1({
        email: "not-an-email",
        fullName: "Test",
        location: "Austin, TX",
      })
    ).rejects.toThrow();
  });
});

describe("site.capabilities", () => {
  it("reports optional services without exposing secrets", async () => {
    const caller = appRouter.createCaller(createPublicContext());
    const result = await caller.site.capabilities();
    expect(result).toEqual({
      applicationIntake: Boolean(process.env.AIRTABLE_API_TOKEN && process.env.AIRTABLE_BASE_ID),
      paymentReporting: Boolean(process.env.AIRTABLE_API_TOKEN && process.env.AIRTABLE_BASE_ID),
      aiBlueprints: Boolean(process.env.ANTHROPIC_API_KEY),
    });
    expect(Object.values(result).every(v => typeof v === "boolean")).toBe(true);
  });
});

describe("application.submitPhase4", () => {
  it("returns pricing after all acknowledgments are checked", async () => {
    const caller = appRouter.createCaller(createPublicContext());
    const result = await caller.application.submitPhase4({
      email: "operator@test.com",
      whyNow: "Ready to commit",
      startWindow: "IMMEDIATELY",
      investmentAck: true,
      reviewAgreement: true,
    });
    expect(result.success).toBe(true);
    expect(result.pricing).toBeDefined();
    expect(result.pricing).toHaveProperty("FOUNDATION_PRICE");
    expect(result.pricing).toHaveProperty("RECOMP_PRICE");
    expect(result.pricing).toHaveProperty("LEGACY_PRICE");
  });

  it("throws if investmentAck is false", async () => {
    const caller = appRouter.createCaller(createPublicContext());
    await expect(
      caller.application.submitPhase4({
        email: "operator@test.com",
        whyNow: "Ready",
        startWindow: "IMMEDIATELY",
        investmentAck: false,
        reviewAgreement: true,
      })
    ).rejects.toThrow("Both acknowledgments are required.");
  });
});

describe("aiEngine.generatePlan", () => {
  it("calls LLM and returns a plan string", async () => {
    const caller = appRouter.createCaller(createPublicContext());
    const result = await caller.aiEngine.generatePlan({
      goals: "Lose 15 lbs and build strength",
      fitnessLevel: "Intermediate",
      availability: "5 days/week, 60 min sessions",
    });
    expect(result.success).toBe(true);
    expect(typeof result.plan).toBe("string");
    expect(result.plan.length).toBeGreaterThan(0);
  });

  it("rejects if goals is empty", async () => {
    const caller = appRouter.createCaller(createPublicContext());
    await expect(
      caller.aiEngine.generatePlan({
        goals: "",
        fitnessLevel: "Beginner",
        availability: "3 days/week",
      })
    ).rejects.toThrow();
  });
});

describe("payment.report", () => {
  it("accepts a valid payment report", async () => {
    const caller = appRouter.createCaller(createPublicContext());
    const result = await caller.payment.report({
      name: "Test Operator",
      email: "operator@test.com",
      method: "PayPal",
      amount: "500.00",
      orderId: "ORD-001",
      transactionId: "TXN-ABC123",
    });
    expect(result.success).toBe(true);
  });

  it("rejects if required fields are missing", async () => {
    const caller = appRouter.createCaller(createPublicContext());
    await expect(
      caller.payment.report({
        name: "",
        email: "operator@test.com",
        method: "PayPal",
        amount: "500.00",
        orderId: "ORD-001",
        transactionId: "TXN-ABC123",
      })
    ).rejects.toThrow();
  });
});
