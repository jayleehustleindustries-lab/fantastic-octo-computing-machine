import { z } from "zod";
import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, router } from "./_core/trpc";
import { invokeLLM } from "./_core/llm";
import { ENV } from "./_core/env";
import { airtableConfigured } from "./airtable";
import {
  upsertApplication,
  getApplicationByEmail,
  createAiPlan,
  createPaymentReport,
} from "./db";

// Pricing config — served only after phase-4 completion
const PRICING = {
  FOUNDATION_PRICE: process.env.FOUNDATION_PRICE ?? "Contact for Pricing",
  RECOMP_PRICE: process.env.RECOMP_PRICE ?? "Contact for Pricing",
  LEGACY_PRICE: process.env.LEGACY_PRICE ?? "Contact for Pricing",
};

const MAO_SYSTEM_PROMPT = `You are the MAO Engine, the AI programming assistant for Coach Jay of JayLee Fit (JayLee Hustle Industries). Generate a personalized 7-day training week in the MAO style: direct, disciplined, no fluff, second person ("you"). Structure the output as:
1) OPERATOR READOUT — 2-3 sentence assessment of the user's inputs.
2) RECOMMENDED TRACK — one of FOUNDATION / RECOMP / LEGACY with one-line rationale.
3) THE WEEK — a day-by-day split (MON-SUN) with exercises, sets x reps, rest, and a one-line coach's note per day. Respect stated availability, focus area, and any injuries/limitations (substitute safe alternatives and say why).
4) GUARDRAILS — 3 short rules on nutrition, recovery, and consistency.
End with: "This is a sample blueprint. Your full MAO program is built after qualification. — MAO ENGINE". Keep it under 600 words. Never give medical advice; advise consulting a professional for injuries.`;

export const appRouter = router({
  site: router({
    capabilities: publicProcedure.query(() => ({
      applicationIntake: airtableConfigured(),
      paymentReporting: Boolean(process.env.DATABASE_URL),
      aiBlueprints: Boolean(ENV.forgeApiUrl && ENV.forgeApiKey),
    })),
  }),
  system: systemRouter,
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return { success: true } as const;
    }),
  }),

  // ── Application form (4 phases) ──────────────────────────────────────────
  application: router({
    submitPhase1: publicProcedure
      .input(z.object({
        email: z.string().email(),
        fullName: z.string().min(1),
        phone: z.string().optional(),
        location: z.string().min(1),
      }))
      .mutation(async ({ input }) => {
        const app = await upsertApplication(input.email, {
          fullName: input.fullName,
          phase1Json: JSON.stringify(input),
        });
        return { success: true, id: app?.id };
      }),

    submitPhase2: publicProcedure
      .input(z.object({
        email: z.string().email(),
        goal: z.string().min(1),
        trainingFrequency: z.string().min(1),
        trainingHistory: z.string().min(1),
        currentStats: z.string().optional(),
      }))
      .mutation(async ({ input }) => {
        const app = await upsertApplication(input.email, {
          phase2Json: JSON.stringify(input),
        });
        return { success: true, id: app?.id };
      }),

    submitPhase3: publicProcedure
      .input(z.object({
        email: z.string().email(),
        hoursPerWeek: z.string().min(1),
        equipmentAccess: z.string().min(1),
        biggestObstacle: z.string().min(1),
        willLog: z.string().min(1),
      }))
      .mutation(async ({ input }) => {
        const app = await upsertApplication(input.email, {
          phase3Json: JSON.stringify(input),
        });
        return { success: true, id: app?.id };
      }),

    submitPhase4: publicProcedure
      .input(z.object({
        email: z.string().email(),
        whyNow: z.string().min(1),
        startWindow: z.string().min(1),
        investmentAck: z.boolean(),
        reviewAgreement: z.boolean(),
      }))
      .mutation(async ({ input }) => {
        if (!input.investmentAck || !input.reviewAgreement) {
          throw new Error("Both acknowledgments are required.");
        }
        const app = await upsertApplication(input.email, {
          phase4Json: JSON.stringify(input),
          completedAt: new Date(),
        });
        // Return pricing only after phase 4 completes
        return {
          success: true,
          id: app?.id,
          pricing: PRICING,
        };
      }),
  }),

  // ── AI Engine ────────────────────────────────────────────────────────────
  aiEngine: router({
    generatePlan: publicProcedure
      .input(z.object({
        name: z.string().optional(),
        goals: z.string().min(1),
        fitnessLevel: z.enum(["Beginner", "Intermediate", "Advanced"]),
        availability: z.string().min(1),
        focusArea: z.string().optional(),
        limitations: z.string().optional(),
      }))
      .mutation(async ({ input }) => {
        const userMessage = [
          `Name: ${input.name ?? "Operator"}`,
          `Goals: ${input.goals}`,
          `Fitness Level: ${input.fitnessLevel}`,
          `Availability: ${input.availability}`,
          input.focusArea ? `Focus Area: ${input.focusArea}` : null,
          input.limitations ? `Injuries/Limitations: ${input.limitations}` : null,
        ].filter(Boolean).join("\n");

        const result = await invokeLLM({
          messages: [
            { role: "system", content: MAO_SYSTEM_PROMPT },
            { role: "user", content: userMessage },
          ],
          model: "claude-sonnet-4-5",
          maxTokens: 1200,
        });

        const firstChoice = result.choices?.[0];
        const planOutput = typeof firstChoice?.message?.content === "string"
          ? firstChoice.message.content
          : "Error generating plan. Please try again.";

        // Persist to DB
        await createAiPlan({
          name: input.name,
          goals: input.goals,
          fitnessLevel: input.fitnessLevel,
          availability: input.availability,
          focusArea: input.focusArea,
          limitations: input.limitations,
          planOutput,
        });

        return { success: true, plan: planOutput };
      }),
  }),

  // ── Payment Reports ──────────────────────────────────────────────────────
  payment: router({
    report: publicProcedure
      .input(z.object({
        name: z.string().min(1),
        email: z.string().email(),
        method: z.string().default("PayPal"),
        amount: z.string().min(1),
        orderId: z.string().min(1),
        transactionId: z.string().min(1),
        note: z.string().optional(),
      }))
      .mutation(async ({ input }) => {
        await createPaymentReport(input);
        return { success: true };
      }),
  }),
});

export type AppRouter = typeof appRouter;
