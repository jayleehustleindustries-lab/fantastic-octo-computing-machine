import { z } from "zod";
import { TRPCError } from "@trpc/server";
import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, router } from "./_core/trpc";
import { airtableConfigured, upsertChatLead } from "./airtable";
import { askJay, chatInput } from "./chat";
import { claudeConfigured, takeSlot } from "./claude";
import {
  upsertApplication,
  getApplicationByEmail,
  createPaymentReport,
} from "./db";

// Pricing config — served only after phase-4 completion
const PRICING = {
  FOUNDATION_PRICE: process.env.FOUNDATION_PRICE ?? "Contact for Pricing",
  RECOMP_PRICE: process.env.RECOMP_PRICE ?? "Contact for Pricing",
  LEGACY_PRICE: process.env.LEGACY_PRICE ?? "Contact for Pricing",
};

// Public-use caps per visitor (IP) per hour.
const CHAT_MESSAGES_PER_HOUR = 30;
const LEADS_PER_HOUR = 3;

/** What the site can do in this deployment. Also served at /api/health. */
export function siteCapabilities() {
  return {
    applicationIntake: airtableConfigured(),
    paymentReporting: airtableConfigured(),
    aiChat: claudeConfigured(),
  };
}

export const appRouter = router({
  site: router({
    capabilities: publicProcedure.query(() => siteCapabilities()),
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

  // ── Ask Jay assistant ──────────────────────────────────────────────────
  chat: router({
    send: publicProcedure
      .input(chatInput)
      .mutation(async ({ input, ctx }) => {
        const visitor = ctx.req.ip || "unknown";
        if (!claudeConfigured()) {
          throw new TRPCError({ code: "PRECONDITION_FAILED", message: "Ask Jay isn't switched on yet. You can still apply below." });
        }
        if (!takeSlot("chat", visitor, CHAT_MESSAGES_PER_HOUR)) {
          throw new TRPCError({
            code: "TOO_MANY_REQUESTS",
            message: "That's a lot of questions for one hour. Take a breather, or apply and Coach Jay will answer you directly.",
          });
        }
        return askJay(input.messages, async lead => {
          if (!airtableConfigured()) throw new Error("Lead storage isn't connected yet.");
          if (!takeSlot("lead", visitor, LEADS_PER_HOUR)) throw new Error("Too many saves from this visitor this hour.");
          await upsertChatLead(lead);
        });
      }),
  }),

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
