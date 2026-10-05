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
