import { eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import { InsertUser, users, applications, aiPlans } from "../drizzle/schema";
import { ENV } from './_core/env';
import { createLead, createPaymentReport as createAirtablePaymentReport, findLeadByEmail, formatPhase, funnelStageFor, mergePhaseNotes, updateLead } from "./airtable";

let _db: ReturnType<typeof drizzle> | null = null;

// Lazily create the drizzle instance so local tooling can run without a DB.
export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

// ── Users ────────────────────────────────────────────────────────────────────

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    } else if (user.openId === ENV.ownerOpenId) {
      values.role = 'admin';
      updateSet.role = 'admin';
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch (error) {
    console.error("[Database] Failed to upsert user:", error);
    throw error;
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

// ── Applications ────────────────────────────────────────────────────────────

export async function upsertApplication(email: string, patch: Partial<{
  fullName: string;
  phase1Json: string;
  phase2Json: string;
  phase3Json: string;
  phase4Json: string;
  completedAt: Date;
}>) {
  const phase = ([1, 2, 3, 4] as const).find(n => patch[`phase${n}Json`] !== undefined);
  if (!phase) throw new Error("Application patch has no phase answers");

  const block = formatPhase(phase, JSON.parse(patch[`phase${phase}Json`]!));
  const existing = await findLeadByEmail(email);
  const { notes, furthest } = mergePhaseNotes(String(existing?.fields.Notes ?? ""), phase, block);

  const fields: Record<string, unknown> = {
    Notes: notes,
    "Funnel Stage": funnelStageFor(furthest),
  };
  if (patch.fullName) fields["Lead Name"] = patch.fullName;

  if (existing) return updateLead(existing.id, fields);
  return createLead({
    ...fields,
    Email: email,
    Source: "jayleefit.com MAO application",
    "Created Date": new Date().toISOString().slice(0, 10),
  });
}

export async function getApplicationByEmail(email: string) {
  const db = await getDb();
  if (!db) return null;
  const rows = await db.select().from(applications).where(eq(applications.email, email)).limit(1);
  return rows[0] ?? null;
}

// ── AI Plans ────────────────────────────────────────────────────────────────

export async function createAiPlan(data: {
  name?: string;
  goals: string;
  fitnessLevel: string;
  availability: string;
  focusArea?: string;
  limitations?: string;
  planOutput?: string;
}) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] AI plan was generated but not persisted: database not available");
    return undefined;
  }
  await db.insert(aiPlans).values(data);
  const all = await db.select().from(aiPlans);
  return all[all.length - 1];
}

// ── Payment Reports ──────────────────────────────────────────────────────────

export async function createPaymentReport(data: {
  name: string;
  email: string;
  method?: string;
  amount: string;
  orderId: string;
  transactionId: string;
  note?: string;
}) {
  return createAirtablePaymentReport(data);
}

// TODO: add feature queries here as your schema grows.
