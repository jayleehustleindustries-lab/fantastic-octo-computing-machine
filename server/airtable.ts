/**
 * Applications are stored as leads in the JayLeeFit Client Hub's Lead Pipeline
 * table — the same base the rest of the business runs on — instead of a
 * separate MySQL database. One record per applicant email, filled in as they
 * move through the four phases.
 */

const AIRTABLE_API = "https://api.airtable.com/v0";

export function airtableConfigured(): boolean {
  return Boolean(process.env.AIRTABLE_API_TOKEN && process.env.AIRTABLE_BASE_ID);
}

type AirtableRecord = { id: string; fields: Record<string, unknown> };

const leadsTable = () => process.env.AIRTABLE_LEADS_TABLE || "Lead Pipeline";
const paymentsTable = () => process.env.AIRTABLE_PAYMENTS_TABLE || "Payment Reports";

async function airtable(path: string, init: RequestInit = {}, tableName = leadsTable()): Promise<any> {
  const token = process.env.AIRTABLE_API_TOKEN;
  const baseId = process.env.AIRTABLE_BASE_ID;
  if (!token || !baseId) throw new Error("Airtable is not configured");

  const table = encodeURIComponent(tableName);
  const response = await fetch(`${AIRTABLE_API}/${baseId}/${table}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...init.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(`Airtable ${response.status}: ${body?.error?.message ?? body?.error ?? "request failed"}`);
  }
  return response.json();
}

export async function findLeadByEmail(email: string): Promise<AirtableRecord | null> {
  // Formula strings are single-quoted; escape so an apostrophe in an address can't break out.
  const safe = email.toLowerCase().replace(/\\/g, "\\\\").replace(/'/g, "\\'");
  const params = new URLSearchParams({
    filterByFormula: `LOWER({Email}) = '${safe}'`,
    maxRecords: "1",
  });
  const data = await airtable(`?${params}`);
  return data.records?.[0] ?? null;
}

export async function createLead(fields: Record<string, unknown>): Promise<AirtableRecord> {
  const data = await airtable("", { method: "POST", body: JSON.stringify({ records: [{ fields }] }) });
  return data.records[0];
}

export async function updateLead(id: string, fields: Record<string, unknown>): Promise<AirtableRecord> {
  const data = await airtable("", { method: "PATCH", body: JSON.stringify({ records: [{ id, fields }] }) });
  return data.records[0];
}

// ── Payment reports ─────────────────────────────────────────────────────────

export type PaymentReport = {
  name: string;
  email: string;
  method?: string;
  amount: string;
  orderId: string;
  transactionId: string;
  note?: string;
};

/**
 * Self-reported payments land in their own table for manual review against
 * PayPal. Nothing here verifies the payment; Status starts at "Needs review".
 */
export async function createPaymentReport(report: PaymentReport): Promise<AirtableRecord> {
  const fields: Record<string, unknown> = {
    Name: report.name,
    Email: report.email,
    Method: report.method || "PayPal",
    Amount: report.amount,
    "Order ID": report.orderId,
    "Transaction ID": report.transactionId,
    "Reported Date": new Date().toISOString().slice(0, 10),
    Status: "Needs review",
  };
  if (report.note) fields.Note = report.note;
  const data = await airtable(
    "",
    { method: "POST", body: JSON.stringify({ records: [{ fields }], typecast: true }) },
    paymentsTable(),
  );
  return data.records[0];
}

// ── Turning phase answers into readable Notes ───────────────────────────────

const PHASE_TITLES: Record<number, string> = {
  1: "Phase 1 — Identity",
  2: "Phase 2 — Mission Profile",
  3: "Phase 3 — Logistics & Commitment",
  4: "Phase 4 — Readiness",
};

const LABELS: Record<string, string> = {
  fullName: "Full name",
  phone: "Phone",
  location: "Location / timezone",
  goal: "12-week goal",
  trainingFrequency: "Training frequency",
  trainingHistory: "Training history",
  currentStats: "Current stats",
  hoursPerWeek: "Hours per week",
  equipmentAccess: "Equipment access",
  biggestObstacle: "Biggest obstacle",
  willLog: "Will log daily",
  whyNow: "Why now",
  startWindow: "Start window",
  investmentAck: "Investment acknowledged",
  reviewAgreement: "Agreed to review",
};

const PHASE_MARKER = /^── Phase (\d)/;

export function formatPhase(phase: number, answers: Record<string, unknown>): string {
  const lines = Object.entries(answers)
    .filter(([key, value]) => key !== "email" && value !== undefined && value !== "")
    .map(([key, value]) => {
      const shown = typeof value === "boolean" ? (value ? "Yes" : "No") : String(value);
      return `${LABELS[key] ?? key}: ${shown}`;
    });
  return [`── ${PHASE_TITLES[phase] ?? `Phase ${phase}`} ──`, ...lines].join("\n");
}

/**
 * Merges one phase's block into existing Notes. Re-submitting a phase replaces
 * its block instead of duplicating it; anything else in Notes (e.g. what the
 * coach typed by hand) is kept at the top.
 */
export function mergePhaseNotes(existing: string, phase: number, block: string) {
  const other: string[] = [];
  const phases = new Map<number, string>();
  for (const section of existing.split(/\n\n+/).filter(s => s.trim())) {
    const match = section.match(PHASE_MARKER);
    if (match) phases.set(Number(match[1]), section);
    else other.push(section);
  }
  phases.set(phase, block);

  const ordered = Array.from(phases.entries()).sort(([a], [b]) => a - b);
  const notes = [...other, ...ordered.map(([, text]) => text)].join("\n\n");
  const furthest = ordered[ordered.length - 1][0];
  return { notes, furthest };
}

export function funnelStageFor(furthestPhase: number): string {
  return furthestPhase >= 4 ? "Application complete" : `Application — phase ${furthestPhase} of 4`;
}

// ── Leads from the Ask Jay assistant ────────────────────────────────────────

const CHAT_MARKER = "── Ask Jay chat ──";

export type ChatLead = {
  name: string;
  email: string;
  goal: string;
  summary: string;
  readyToApply: boolean;
  /** Which offer they were heading to when they shared their details. */
  next?: "remap" | "coaching";
  /** Lead Source, e.g. "Instagram DM → jayleefit.com Ask Jay chat". */
  source?: string;
};

/** Notes sections are split on blank lines, so keep each value on one paragraph. */
const oneParagraph = (text: string) => text.replace(/\s*\n\s*\n\s*/g, "\n").trim();

/** Puts the latest chat summary at the top of Notes, replacing any earlier one. */
export function mergeChatNotes(existing: string, lead: ChatLead): string {
  const block = [
    CHAT_MARKER,
    `Goal: ${oneParagraph(lead.goal)}`,
    `Interested in: ${lead.next === "remap" ? "Remap (self-guided program)" : "1:1 coaching"}`,
    `Ready to start: ${lead.readyToApply ? "Yes" : "No"}`,
    `Summary: ${oneParagraph(lead.summary)}`,
  ].join("\n");
  const kept = existing.split(/\n\n+/).filter(section => section.trim() && !section.startsWith(CHAT_MARKER));
  return [block, ...kept].join("\n\n");
}

/**
 * Saves a visitor who asked Ask Jay to pass their details to Coach Jay. Uses the
 * same one-record-per-email Lead Pipeline row as the application, and never
 * moves a lead that has started applying back to a chat stage.
 */
export async function upsertChatLead(lead: ChatLead): Promise<AirtableRecord> {
  const stage = lead.next === "remap" ? "Chat — Remap interest" : lead.readyToApply ? "Chat — ready to apply" : "Chat lead";
  const existing = await findLeadByEmail(lead.email);
  const notes = mergeChatNotes(String(existing?.fields.Notes ?? ""), lead);

  if (existing) {
    const fields: Record<string, unknown> = { Notes: notes };
    const current = String(existing.fields["Funnel Stage"] ?? "");
    if (!current.startsWith("Application") && !current.startsWith("Remap")) fields["Funnel Stage"] = stage;
    if (!existing.fields["Lead Name"]) fields["Lead Name"] = lead.name;
    return updateLead(existing.id, fields);
  }
  return createLead({
    "Lead Name": lead.name,
    Email: lead.email,
    Source: lead.source ?? "jayleefit.com Ask Jay chat",
    "Created Date": new Date().toISOString().slice(0, 10),
    "Funnel Stage": stage,
    Notes: notes,
  });
}

// ── Remap orders and client records ─────────────────────────────────────────

const remapTable = () => process.env.AIRTABLE_REMAP_TABLE || "Remap Orders";
const clientsTable = () => process.env.AIRTABLE_CLIENTS_TABLE || "Clients";
const nutritionTable = () => process.env.AIRTABLE_NUTRITION_TABLE || "Nutrition Plans";
const progressTable = () => process.env.AIRTABLE_PROGRESS_TABLE || "Progress Tracking";

export type { AirtableRecord };

const formulaString = (value: string) => `'${value.replace(/\\/g, "\\\\").replace(/'/g, "\\'")}'`;

async function findOne(table: string, formula: string): Promise<AirtableRecord | null> {
  const params = new URLSearchParams({ filterByFormula: formula, maxRecords: "1" });
  const data = await airtable(`?${params}`, {}, table);
  return data.records?.[0] ?? null;
}

async function create(table: string, fields: Record<string, unknown>): Promise<AirtableRecord> {
  const data = await airtable("", { method: "POST", body: JSON.stringify({ records: [{ fields }], typecast: true }) }, table);
  return data.records[0];
}

async function update(table: string, id: string, fields: Record<string, unknown>): Promise<AirtableRecord> {
  const data = await airtable("", { method: "PATCH", body: JSON.stringify({ records: [{ id, fields }], typecast: true }) }, table);
  return data.records[0];
}

export const createRemapOrder = (fields: Record<string, unknown>) => create(remapTable(), fields);
export const updateRemapOrder = (id: string, fields: Record<string, unknown>) => update(remapTable(), id, fields);
export const findRemapOrderByToken = (token: string) => findOne(remapTable(), `{Token} = ${formulaString(token)}`);

export const findClientByEmail = (email: string) =>
  findOne(clientsTable(), `LOWER({Email}) = ${formulaString(email.toLowerCase())}`);

/** Background on a buyer that Opus can use: their lead notes, client goals, and recent progress. */
export async function clientContext(email: string): Promise<{ lead: AirtableRecord | null; client: AirtableRecord | null; progress: AirtableRecord[] }> {
  const [lead, client] = await Promise.all([findLeadByEmail(email), findClientByEmail(email)]);
  let progress: AirtableRecord[] = [];
  const ids = (client?.fields["Progress Tracking"] as string[] | undefined) ?? [];
  if (ids.length) {
    const params = new URLSearchParams({
      filterByFormula: `OR(${ids.slice(-20).map(id => `RECORD_ID() = ${formulaString(id)}`).join(", ")})`,
      "sort[0][field]": "Date",
      "sort[0][direction]": "desc",
      maxRecords: "5",
    });
    progress = (await airtable(`?${params}`, {}, progressTable())).records ?? [];
  }
  return { lead, client, progress };
}

export type DeliveredRemap = {
  name: string;
  email: string;
  goalSummary: string;
  source: string;
  startDate: string;
  endDate: string;
  proteinG: number;
  carbsG: number;
  fatG: number;
  targetCalories: number;
  nutritionNotes: string;
};

/**
 * Files a delivered Remap where the coaching side already looks: the client's
 * record, a Nutrition Plan with gram targets (Airtable computes calories and
 * percentages), and the lead's funnel stage.
 */
export async function recordRemapDelivery(r: DeliveredRemap): Promise<void> {
  const existing = await findClientByEmail(r.email);
  const client = existing
    ? existing.fields.Goals ? existing : await update(clientsTable(), existing.id, { Goals: r.goalSummary })
    : await create(clientsTable(), {
        "Client Name": r.name,
        Email: r.email,
        Goals: r.goalSummary,
        "Program Start Date": r.startDate,
        Tags: ["Remap"],
      });

  await create(nutritionTable(), {
    "Meal Plan Name": `Remap — ${r.name} (${r.startDate})`,
    Client: [client.id],
    "Protein (g)": r.proteinG,
    "Carbs (g)": r.carbsG,
    "Fat (g)": r.fatG,
    Macros: `${r.targetCalories} kcal · P ${r.proteinG}g · C ${r.carbsG}g · F ${r.fatG}g`,
    "Nutrition Notes": r.nutritionNotes,
    "Plan Start Date": r.startDate,
    "Plan End Date": r.endDate,
  });

  const lead = await findLeadByEmail(r.email);
  if (lead) {
    await updateLead(lead.id, { "Funnel Stage": "Remap purchased", Clients: Array.from(new Set([...((lead.fields.Clients as string[]) ?? []), client.id])) });
  } else {
    await createLead({
      "Lead Name": r.name,
      Email: r.email,
      Source: r.source,
      "Created Date": r.startDate,
      "Funnel Stage": "Remap purchased",
      Clients: [client.id],
    });
  }
}
