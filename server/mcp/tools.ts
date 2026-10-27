import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { APPLICATION_STEPS, COACH, REMAP, SERVICES, TIERS } from "@shared/maoContent";
import { ACTIVITY_LEVELS, GOALS, PROGRAM_WEEKS, inchesToCm, lbToKg, remapNumbers } from "@shared/remap";
import {
  airtableConfigured,
  clientContext,
  findLeadByEmail,
  findRemapOrderByToken,
  formulaString,
  getRecord,
  listRecords,
  updateRecord,
  updateRemapOrder,
  type AirtableRecord,
} from "../airtable";
import { ensureGeneration, remapPriceCents } from "../remap";
import { siteCapabilities } from "../routers";
import { siteUrl } from "./auth";

/**
 * The tools Claude gets through the website connector: public coaching info,
 * read access to the business records in Airtable, and a few safe actions.
 * Nothing here deletes anything.
 */

const CHARACTER_LIMIT = 25_000;
const PROGRAM_CHARACTER_LIMIT = 80_000;

type Data = Record<string, unknown>;

function ok(data: Data, limit = CHARACTER_LIMIT): CallToolResult {
  let text = JSON.stringify(data, null, 2);
  if (text.length > limit) text = `${text.slice(0, limit)}\n… (truncated; narrow the request or use a smaller limit)`;
  return { content: [{ type: "text", text }], structuredContent: data };
}

const fail = (message: string): CallToolResult => ({ content: [{ type: "text", text: message }], isError: true });

/** Runs a tool that needs Airtable, turning errors into messages Claude can act on. */
async function withAirtable(run: () => Promise<CallToolResult>): Promise<CallToolResult> {
  if (!airtableConfigured()) {
    return fail("Airtable isn't connected on this server yet. Add AIRTABLE_API_TOKEN in Railway → jayleefit-web → Variables.");
  }
  try {
    return await run();
  } catch (error) {
    return fail(`Error: ${error instanceof Error ? error.message : String(error)}`);
  }
}

const READ_ONLY = { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false } as const;
const PUBLIC_READ = { ...READ_ONLY } as const;

const limitArg = z.number().int().min(1).max(100).default(20).describe("How many records to return (1–100).");
const cursorArg = z.string().max(200).optional().describe("The next_cursor from a previous call, to get the next page.");
const emailArg = z.string().trim().email().max(200);
const recordIdArg = z.string().regex(/^rec[A-Za-z0-9]{14}$/, "Airtable record ids look like recXXXXXXXXXXXXXX");

const text = (value: unknown) => (value === undefined || value === null ? undefined : String(value));
const clip = (value: unknown, max: number) => {
  const s = text(value);
  return s && s.length > max ? `${s.slice(0, max)}…` : s;
};
const parseJson = (value: unknown) => {
  try {
    return value ? JSON.parse(String(value)) : null;
  } catch {
    return null;
  }
};
const page = (offset: string | undefined) => ({ has_more: Boolean(offset), next_cursor: offset ?? null });

function leadSummary(r: AirtableRecord, notesLength = 300) {
  const f = r.fields;
  return {
    id: r.id,
    name: text(f["Lead Name"]),
    email: text(f.Email),
    stage: text(f["Funnel Stage"]),
    source: text(f.Source),
    created: text(f["Created Date"]),
    next_action: text(f["Next Action"]),
    notes: clip(f.Notes, notesLength),
  };
}

function orderSummary(r: AirtableRecord) {
  const f = r.fields;
  const site = siteUrl();
  return {
    id: r.id,
    name: text(f.Name),
    email: text(f.Email),
    status: text(f.Status),
    amount: f.Amount ?? null,
    source: text(f.Source),
    experience: text(f.Experience),
    goal: text(f.Goal),
    weeks: f.Weeks ?? null,
    target_calories: f["Target Calories"] ?? null,
    created: text(f["Created Date"]),
    paid_at: text(f["Paid At"]),
    generated_at: text(f["Generated At"]),
    error: text(f.Error),
    program_url: site && f.Token ? new URL(`/remap/p/${f.Token}`, site).href : null,
  };
}

function paymentSummary(r: AirtableRecord) {
  const f = r.fields;
  return {
    id: r.id,
    name: text(f.Name),
    email: text(f.Email),
    method: text(f.Method),
    amount: text(f.Amount),
    order_id: text(f["Order ID"]),
    transaction_id: text(f["Transaction ID"]),
    reported: text(f["Reported Date"]),
    status: text(f.Status),
    note: text(f.Note),
  };
}

async function findLead(lead: string): Promise<AirtableRecord | null> {
  return lead.startsWith("rec") ? getRecord("leads", lead) : findLeadByEmail(lead);
}

async function findOrder(order: string): Promise<AirtableRecord | null> {
  if (/^rec[A-Za-z0-9]{14}$/.test(order)) return getRecord("remap", order);
  if (order.includes("@")) {
    const { records } = await listRecords("remap", {
      formula: `LOWER({Email}) = ${formulaString(order.toLowerCase())}`,
      sortField: "Created Date",
      pageSize: 1,
    });
    return records[0] ?? null;
  }
  return findRemapOrderByToken(order);
}

const today = () => new Date().toISOString().slice(0, 10);
const appendNote = (existing: unknown, note: string) => [text(existing)?.trim(), `── Note (${today()}) ──\n${note.trim()}`].filter(Boolean).join("\n\n");

export function createMcpServer(): McpServer {
  const server = new McpServer({ name: "jayleefit-mcp-server", version: "1.0.0" });

  // ── Public coaching info ─────────────────────────────────────────────────

  server.registerTool(
    "jayleefit_site_info",
    {
      title: "JayLee Hustle offers and coach info",
      description:
        "What JayLee Hustle sells and how it works: the Remap self-guided program (with its current price), the three coaching tiers (Foundation, Recomp, Legacy; coaching prices are only shared after an application is qualified), services, Coach Jay's bio, and the application steps. Use this before describing an offer.",
      inputSchema: {},
      annotations: PUBLIC_READ,
    },
    async () => {
      const cents = remapPriceCents();
      const site = siteUrl();
      return ok({
        site: site?.href ?? null,
        remap: { ...REMAP, price_usd: cents === null ? null : cents / 100, url: site ? new URL("/remap", site).href : null },
        coaching_tiers: TIERS.map(({ priceKey: _priceKey, ...tier }) => tier),
        services: SERVICES,
        coach: COACH,
        application_steps: APPLICATION_STEPS,
      });
    },
  );

  server.registerTool(
    "jayleefit_calculate_numbers",
    {
      title: "Calculate BMR, TDEE and macros",
      description: `Runs the same calculator Remap uses: Mifflin-St Jeor BMR, times an activity factor for TDEE, a goal-based calorie target with safety floors, and protein/fat/carb grams. Use it instead of doing the math yourself.

Activity: sedentary (1.2), light (1.375), moderate (1.55), very (1.725), athlete (1.9).
Goal: fat-loss (×0.8), recomp (×0.9), muscle-gain (×1.1), performance (×1.0).
Give height and weight in the chosen units: imperial = inches and pounds, metric = cm and kg.`,
      inputSchema: {
        units: z.enum(["imperial", "metric"]).default("imperial"),
        sex: z.enum(["male", "female", "unspecified"]),
        age: z.number().int().min(16).max(90),
        height: z.number().positive().describe("Inches (imperial, e.g. 71 for 5'11\") or cm (metric)."),
        weight: z.number().positive().describe("Pounds (imperial) or kg (metric)."),
        goal_weight: z.number().positive().optional().describe("Optional, same units as weight. Used for protein when BMI is 30 or more."),
        activity: z.enum(["sedentary", "light", "moderate", "very", "athlete"]),
        goal: z.enum(["fat-loss", "recomp", "muscle-gain", "performance"]),
        experience: z.enum(["beginner", "intermediate", "advanced"]).optional().describe("Optional: also return Remap's program length range."),
      },
      annotations: PUBLIC_READ,
    },
    async ({ units, sex, age, height, weight, goal_weight, activity, goal, experience }) => {
      const imperial = units === "imperial";
      const heightCm = imperial ? inchesToCm(height) : height;
      const weightKg = imperial ? lbToKg(weight) : weight;
      if (heightCm < 120 || heightCm > 230) return fail("Height looks off. Imperial height is in inches (5'11\" = 71).");
      if (weightKg < 35 || weightKg > 300) return fail("Weight looks off. Imperial weight is in pounds, metric in kg.");
      const numbers = remapNumbers({
        sex,
        age,
        heightCm,
        weightKg,
        goalWeightKg: goal_weight ? (imperial ? lbToKg(goal_weight) : goal_weight) : undefined,
        activity,
        goal,
      });
      return ok({
        ...numbers,
        activity_label: ACTIVITY_LEVELS[activity].label,
        goal_label: GOALS[goal].label,
        program_weeks: experience ? PROGRAM_WEEKS[experience] : undefined,
      });
    },
  );

  // ── Business records (read) ──────────────────────────────────────────────

  server.registerTool(
    "jayleefit_site_status",
    {
      title: "Website status",
      description: "Which parts of the website are switched on: applications, payment reports, the Ask Jay chat, Remap checkout, and this connector. Use it to explain why something isn't working.",
      inputSchema: {},
      annotations: READ_ONLY,
    },
    async () => ok({ site: siteUrl()?.href ?? null, ...siteCapabilities() }),
  );

  server.registerTool(
    "jayleefit_list_leads",
    {
      title: "List leads",
      description: `Lists leads from the Lead Pipeline (applications, Ask Jay chats, Remap buyers), newest first. Notes are shortened; use jayleefit_get_lead for the full record.

Common stages: "Chat lead", "Chat — ready to apply", "Chat — Remap interest", "Application – step N of 4", "Application complete", "Remap purchased".`,
      inputSchema: {
        stage: z.string().trim().max(80).optional().describe("Only leads whose Funnel Stage contains this text, e.g. \"Application\"."),
        source: z.string().trim().max(80).optional().describe("Only leads whose Source contains this text, e.g. \"Instagram\"."),
        since: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe("Only leads created on or after this date (YYYY-MM-DD)."),
        limit: limitArg,
        cursor: cursorArg,
      },
      annotations: READ_ONLY,
    },
    ({ stage, source, since, limit, cursor }) =>
      withAirtable(async () => {
        const filters = [
          stage && `FIND(LOWER(${formulaString(stage)}), LOWER({Funnel Stage}))`,
          source && `FIND(LOWER(${formulaString(source)}), LOWER({Source}))`,
          since && `NOT(IS_BEFORE({Created Date}, ${formulaString(since)}))`,
        ].filter(Boolean);
        const { records, offset } = await listRecords("leads", {
          formula: filters.length ? `AND(${filters.join(", ")})` : undefined,
          sortField: "Created Date",
          pageSize: limit,
          offset: cursor,
        });
        return ok({ count: records.length, leads: records.map(r => leadSummary(r)), ...page(offset) });
      }),
  );

  server.registerTool(
    "jayleefit_get_lead",
    {
      title: "Get a lead",
      description: "One Lead Pipeline record by email or record id, with full Notes (the Ask Jay chat summary and every application phase's answers).",
      inputSchema: { lead: z.string().trim().min(3).max(200).describe("Email address or Airtable record id (recXXXXXXXXXXXXXX).") },
      annotations: READ_ONLY,
    },
    ({ lead }) =>
      withAirtable(async () => {
        const record = await findLead(lead);
        if (!record) return fail(`No lead found for "${lead}". Try jayleefit_list_leads to search.`);
        const f = record.fields;
        return ok({
          ...leadSummary(record, 20_000),
          qualification: text(f.Qualification),
          outcome: text(f.Outcome),
          discovery_call: text(f["Discovery Call Date"]),
          mrr_won: f["MRR Won"] ?? null,
          state: text(f.State),
          client_ids: f.Clients ?? [],
        });
      }),
  );

  server.registerTool(
    "jayleefit_list_remap_orders",
    {
      title: "List Remap orders",
      description: "Lists Remap purchases, newest first, with status (Awaiting payment, Paid, Generating, Ready, Failed), amount, source and the client's program link.",
      inputSchema: {
        status: z.enum(["Awaiting payment", "Paid", "Generating", "Ready", "Failed"]).optional(),
        limit: limitArg,
        cursor: cursorArg,
      },
      annotations: READ_ONLY,
    },
    ({ status, limit, cursor }) =>
      withAirtable(async () => {
        const { records, offset } = await listRecords("remap", {
          formula: status ? `{Status} = ${formulaString(status)}` : undefined,
          sortField: "Created Date",
          pageSize: limit,
          offset: cursor,
          fields: ["Name", "Email", "Status", "Token", "Amount", "Source", "Experience", "Goal", "Weeks", "Target Calories", "Created Date", "Paid At", "Generated At", "Error"],
        });
        return ok({ count: records.length, orders: records.map(orderSummary), ...page(offset) });
      }),
  );

  server.registerTool(
    "jayleefit_get_remap_order",
    {
      title: "Get a Remap order",
      description: "One Remap order with the client's intake answers, computed numbers (BMR, TDEE, calories, macros) and, if built, the full program. Look it up by record id, program-link token, or email (latest order).",
      inputSchema: {
        order: z.string().trim().min(3).max(200).describe("Record id, token from the program link, or the buyer's email."),
        include_program: z.boolean().default(true).describe("Set false to skip the program, which is long."),
      },
      annotations: READ_ONLY,
    },
    ({ order, include_program }) =>
      withAirtable(async () => {
        const record = await findOrder(order);
        if (!record) return fail(`No Remap order found for "${order}".`);
        return ok(
          {
            ...orderSummary(record),
            intake: parseJson(record.fields.Intake),
            numbers: parseJson(record.fields.Numbers),
            model: text(record.fields.Model),
            program: include_program ? parseJson(record.fields.Program) : undefined,
          },
          PROGRAM_CHARACTER_LIMIT,
        );
      }),
  );

  server.registerTool(
    "jayleefit_list_payment_reports",
    {
      title: "List payment reports",
      description: "Payments clients self-reported on the site, newest first. None are verified automatically; check each against PayPal, then use jayleefit_set_payment_status.",
      inputSchema: {
        status: z.enum(["Needs review", "Verified", "Rejected"]).optional(),
        limit: limitArg,
        cursor: cursorArg,
      },
      annotations: READ_ONLY,
    },
    ({ status, limit, cursor }) =>
      withAirtable(async () => {
        const { records, offset } = await listRecords("payments", {
          formula: status ? `{Status} = ${formulaString(status)}` : undefined,
          sortField: "Reported Date",
          pageSize: limit,
          offset: cursor,
        });
        return ok({ count: records.length, reports: records.map(paymentSummary), ...page(offset) });
      }),
  );

  server.registerTool(
    "jayleefit_find_client",
    {
      title: "Find a client",
      description: "Everything on file for one person by email: their Clients record (goals, status, start date), their lead, recent progress entries, and nutrition plans (macro targets).",
      inputSchema: { email: emailArg },
      annotations: READ_ONLY,
    },
    ({ email }) =>
      withAirtable(async () => {
        const { lead, client, progress } = await clientContext(email);
        if (!lead && !client) return fail(`Nothing on file for ${email}.`);
        const planIds = ((client?.fields["Nutrition Plans"] as string[] | undefined) ?? []).slice(-5);
        const plans = (await Promise.all(planIds.map(id => getRecord("nutrition", id)))).filter(Boolean) as AirtableRecord[];
        const { "Profile Photo": _photo, ...clientFields } = client?.fields ?? {};
        return ok({
          client: client ? { id: client.id, ...clientFields } : null,
          lead: lead ? leadSummary(lead, 20_000) : null,
          recent_progress: progress.map(p => {
            const { "Progress Photos": _photos, ...fields } = p.fields;
            return { id: p.id, ...fields };
          }),
          nutrition_plans: plans.map(p => ({ id: p.id, ...p.fields })),
        });
      }),
  );

  // ── Actions ──────────────────────────────────────────────────────────────

  server.registerTool(
    "jayleefit_update_lead_stage",
    {
      title: "Update a lead's stage",
      description: "Sets a lead's Funnel Stage (free text, e.g. \"Discovery call booked\" or \"Won — Recomp\"), and can add a dated note to their Notes. Setting the same stage twice changes nothing.",
      inputSchema: {
        lead: z.string().trim().min(3).max(200).describe("Email address or record id."),
        stage: z.string().trim().min(1).max(80),
        note: z.string().trim().max(2000).optional().describe("Optional note to append to the lead's Notes."),
        next_action: z.string().trim().max(500).optional().describe("Optional: replaces the lead's Next Action."),
      },
      annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: true, openWorldHint: false },
    },
    ({ lead, stage, note, next_action }) =>
      withAirtable(async () => {
        const record = await findLead(lead);
        if (!record) return fail(`No lead found for "${lead}".`);
        const fields: Data = { "Funnel Stage": stage };
        if (note) fields.Notes = appendNote(record.fields.Notes, note);
        if (next_action !== undefined) fields["Next Action"] = next_action;
        const updated = await updateRecord("leads", record.id, fields);
        return ok({ updated: true, previous_stage: text(record.fields["Funnel Stage"]) ?? null, lead: leadSummary(updated) });
      }),
  );

  server.registerTool(
    "jayleefit_set_payment_status",
    {
      title: "Set a payment report's status",
      description: "Marks a self-reported payment Verified or Rejected (or back to Needs review) after checking it against PayPal, with an optional note.",
      inputSchema: {
        report_id: recordIdArg.describe("Record id from jayleefit_list_payment_reports."),
        status: z.enum(["Verified", "Rejected", "Needs review"]),
        note: z.string().trim().max(1000).optional(),
      },
      annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: true, openWorldHint: false },
    },
    ({ report_id, status, note }) =>
      withAirtable(async () => {
        const record = await getRecord("payments", report_id);
        if (!record) return fail(`No payment report ${report_id}.`);
        const fields: Data = { Status: status };
        if (note) fields.Note = appendNote(record.fields.Note, note);
        const updated = await updateRecord("payments", record.id, fields);
        return ok({ updated: true, previous_status: text(record.fields.Status) ?? null, report: paymentSummary(updated) });
      }),
  );

  server.registerTool(
    "jayleefit_retry_remap",
    {
      title: "Rebuild a failed Remap",
      description: "Starts the program build again for a paid Remap order that Failed (or stalled for 10+ minutes). It uses Claude Opus credit, and only works for orders that were paid. The client's program page updates by itself when the build finishes, usually in 1–3 minutes.",
      inputSchema: { order: z.string().trim().min(3).max(200).describe("Record id, program-link token, or buyer's email (latest order).") },
      annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: true },
    },
    ({ order }) =>
      withAirtable(async () => {
        const record = await findOrder(order);
        if (!record) return fail(`No Remap order found for "${order}".`);
        const status = text(record.fields.Status);
        if (status === "Awaiting payment") return fail("This order was never paid, so it can't be built.");
        if (status === "Ready") return fail("This program is already built. Nothing to retry.");
        const started = Date.parse(text(record.fields["Generation Started"]) ?? "");
        if (status === "Generating" && Number.isFinite(started) && Date.now() - started < 10 * 60 * 1000) {
          return fail("This program is being built right now. Check back in a few minutes.");
        }
        const toBuild = status === "Failed" ? await updateRemapOrder(record.id, { Status: "Paid", Error: "" }) : record;
        ensureGeneration(toBuild);
        return ok({ started: true, previous_status: status, order: orderSummary(toBuild) });
      }),
  );

  return server;
}
