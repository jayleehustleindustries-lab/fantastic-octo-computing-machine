/**
 * The Neural HUD's signal rules. Pure functions: records in, ranked queue out.
 * The brain only proposes. Nothing here sends, approves or changes anything.
 *
 *   100  money waiting (payment to verify, paid Remap not delivered)
 *    90  hot lead (application done or ready to apply, no next action), −10/day after 48h, floor 60
 *    85  Linear urgent · 80 overdue · 75 due within 48h · 70 high priority
 *    70  Notion: publish approval needed within 72h · 65 failed · 62 in QA review
 *
 * Everything else is noise: muted and counted with a reason.
 */

export type SignalKind = "money" | "lead" | "client" | "task" | "gate";
export type SourceKey = "airtable" | "linear" | "notion";

export type Candidate = {
  id: string;
  source: SourceKey;
  kind: SignalKind;
  score: number;
  title: string;
  why: string;
  next: string;
  url?: string | null;
  /** When the thing last happened, for the stale rule. ISO date or datetime. */
  at?: string | null;
  /** Set when the record is noise. */
  muted?: string;
};

export type Signal = Omit<Candidate, "muted">;

export type SourceStatus = { source: SourceKey; label: string; connected: boolean; error?: string; count: number };

export type Queue = {
  generated_at: string;
  do_now: Signal[];
  next: Signal[];
  /** Signal that ranked below the top 10. */
  more: number;
  muted: { reason: string; count: number }[];
  muted_total: number;
  sources: SourceStatus[];
};

export const MUTE = {
  stale: "Untouched for 30+ days",
  noAction: "No next action and no deadline",
  notFitness: "Not fitness (EHC, resale, automation offer, sports)",
  handled: "Next action already logged",
  sample: "Sample or demo record",
} as const;

const DAY = 24 * 60 * 60 * 1000;
const HOUR = 60 * 60 * 1000;
const NOT_FITNESS = /\b(ehc|resale|resell|poshmark|ebay|old light|automation offer|ai automation|sports? analytics|wnba|nfl|job command)/i;
const SAMPLE = /\b(sample|demo|test record|lorem)\b/i;

const str = (value: unknown) => (value === undefined || value === null ? "" : String(value).trim());
const ms = (value: unknown) => {
  const t = Date.parse(str(value));
  return Number.isFinite(t) ? t : null;
};

export const isFitness = (...texts: unknown[]) => !texts.some(t => NOT_FITNESS.test(str(t)));
export const isSample = (...texts: unknown[]) => texts.some(t => SAMPLE.test(str(t)));

/** 90 for the first 48 hours, then 10 less for each day after, never below 60. */
export function hotLeadScore(createdMs: number, now: number): number {
  const hours = Math.max(0, (now - createdMs) / HOUR);
  if (hours <= 48) return 90;
  return Math.max(60, 90 - 10 * Math.ceil((hours - 48) / 24));
}

const ago = (t: number, now: number) => {
  const h = Math.max(0, Math.round((now - t) / HOUR));
  return h < 48 ? `${h}h ago` : `${Math.round(h / 24)} days ago`;
};

// ── Airtable ────────────────────────────────────────────────────────────────

type Fields = Record<string, unknown>;

export function fromPayment(id: string, f: Fields, now: number): Candidate {
  const who = str(f.Name) || str(f.Email) || "A client";
  const reported = ms(f["Reported Date"]);
  return {
    id,
    source: "airtable",
    kind: "money",
    score: 100,
    title: `Payment report to verify: ${[str(f.Amount), str(f.Method)].filter(Boolean).join(" via ") || "amount not given"}`,
    why: `${who} says they paid${reported ? ` ${ago(reported, now)}` : ""}. It isn't verified until you check.`,
    next: `Match it in ${str(f.Method) || "your payment app"}, then set the report to Verified.`,
    at: str(f["Reported Date"]) || null,
  };
}

export function fromRemapOrder(id: string, f: Fields, now: number, programUrl?: string | null): Candidate {
  const who = str(f.Name) || str(f.Email) || "A buyer";
  const status = str(f.Status);
  const base = { id, source: "airtable" as const, kind: "money" as const, url: programUrl ?? null, at: str(f["Paid At"]) || str(f["Created Date"]) || null };
  if (status === "Failed") {
    return { ...base, score: 100, title: `Paid Remap failed to generate: ${who}`, why: `They paid and have no program yet.${str(f.Error) ? ` Error: ${str(f.Error).slice(0, 140)}` : ""}`, next: "Retry it (jayleefit_retry_remap) or message them with a time." };
  }
  const paid = ms(f["Paid At"]) ?? ms(f["Generation Started"]);
  const stuck = paid !== null && now - paid > (status === "Generating" ? 30 : 15) * 60 * 1000;
  if ((status === "Paid" || status === "Generating") && stuck) {
    return { ...base, score: 100, title: `Paid Remap stuck at "${status}": ${who}`, why: `Paid ${ago(paid!, now)} and still not delivered.`, next: "Retry it (jayleefit_retry_remap) and check the logs." };
  }
  return { ...base, score: 0, title: `Remap ${status}: ${who}`, why: "Still within normal delivery time.", next: "", muted: MUTE.noAction };
}

const HOT_STAGES = /^(application complete|chat — ready to apply)/i;
const PARTIAL_STAGES = /^(application — phase|application – step|chat — remap interest|chat lead)/i;

export function fromLead(id: string, f: Fields, now: number): Candidate {
  const who = str(f["Lead Name"]) || str(f.Email) || "A lead";
  const stage = str(f["Funnel Stage"]);
  const created = ms(f["Created Date"]);
  const base = { id, source: "airtable" as const, kind: "lead" as const, at: str(f["Created Date"]) || null };
  if (isSample(who, f.Email, f.Notes)) return { ...base, score: 0, title: who, why: "", next: "", muted: MUTE.sample };
  if (str(f["Next Action"])) return { ...base, score: 0, title: who, why: "", next: "", muted: MUTE.handled };
  if (HOT_STAGES.test(stage)) {
    return {
      ...base,
      score: created === null ? 90 : hotLeadScore(created, now),
      title: `${stage.startsWith("Chat") ? "Ready to apply" : "Application complete"}, no reply logged: ${who}`,
      why: `${stage}${created !== null ? `, ${ago(created, now)}` : ""}. Leads go cold fast.`,
      next: stage.startsWith("Chat") ? "Send them the application link." : "Send your call link and log it as the Next Action.",
    };
  }
  if (PARTIAL_STAGES.test(stage)) {
    return { ...base, score: 50, title: `Started but didn't finish: ${who}`, why: `${stage}${created !== null ? `, ${ago(created, now)}` : ""}.`, next: "Send one nudge with the link to finish." };
  }
  return { ...base, score: 0, title: who, why: "", next: "", muted: MUTE.noAction };
}

// ── Linear ──────────────────────────────────────────────────────────────────

export type LinearIssue = {
  identifier: string;
  title: string;
  url?: string;
  /** 0 none, 1 urgent, 2 high, 3 medium, 4 low. */
  priority?: number | null;
  dueDate?: string | null;
  updatedAt?: string | null;
  team?: string | null;
  project?: string | null;
  labels?: string[];
};

export function fromLinearIssue(issue: LinearIssue, now: number, scope: string[] = []): Candidate {
  const base = { id: issue.identifier, source: "linear" as const, kind: "task" as const, url: issue.url ?? null, at: issue.updatedAt ?? null };
  const title = `${issue.identifier}: ${issue.title}`;
  const context = [issue.team, issue.project, ...(issue.labels ?? [])];
  const inScope = scope.length
    ? context.some(c => scope.some(s => str(c).toLowerCase() === s.toLowerCase()))
    : isFitness(issue.title, ...context);
  if (!inScope) return { ...base, score: 0, title, why: "", next: "", muted: MUTE.notFitness };

  const due = issue.dueDate ? Date.parse(`${issue.dueDate}T23:59:59`) : null;
  const overdue = due !== null && due < now;
  const soon = due !== null && !overdue && due - now <= 48 * HOUR;
  const dueText = issue.dueDate ? ` Due ${issue.dueDate}.` : "";
  if (issue.priority === 1) return { ...base, score: 85, title, why: `Marked Urgent.${dueText}`, next: "Do it or cut its scope today." };
  if (overdue) return { ...base, score: 80, title, why: `Overdue.${dueText}`, next: "Finish it or move the date on purpose." };
  if (soon) return { ...base, score: 75, title, why: `Due within 48 hours.${dueText}`, next: "Block time for it today." };
  if (issue.priority === 2) return { ...base, score: 70, title, why: `High priority.${dueText}`, next: "Pick the first concrete step." };
  return { ...base, score: 0, title, why: "", next: "", muted: MUTE.noAction };
}

// ── Notion (JLF Content Scheduler) ──────────────────────────────────────────

export type SchedulerRow = {
  id: string;
  name: string;
  url?: string;
  status?: string;
  brand?: string;
  publishApproval?: string;
  scheduledAt?: string | null;
  nextAction?: string;
  nextOwner?: string;
  lastError?: string;
  editedAt?: string | null;
};

export function fromSchedulerRow(row: SchedulerRow, now: number): Candidate {
  const base = { id: row.id, source: "notion" as const, kind: "gate" as const, url: row.url ?? null, at: row.editedAt ?? null };
  const title = row.name || "Untitled content";
  if (!isFitness(row.brand, row.name)) return { ...base, score: 0, title, why: "", next: "", muted: MUTE.notFitness };
  if (isSample(row.name)) return { ...base, score: 0, title, why: "", next: "", muted: MUTE.sample };

  const when = ms(row.scheduledAt);
  const within72h = when !== null && when >= now - HOUR && when - now <= 72 * HOUR;
  if (row.publishApproval === "NOT_APPROVED" && within72h && /^(ready|scheduled|qa review)$/i.test(row.status ?? "")) {
    return { ...base, score: 70, title: `Publish approval needed: ${title}`, why: `Scheduled ${row.scheduledAt}. Only you can approve publishing.`, next: "Watch it once, then approve or block it." };
  }
  if (/^failed$/i.test(row.status ?? "")) {
    return { ...base, score: 65, title: `Content failed: ${title}`, why: row.lastError ? `Last error: ${row.lastError.slice(0, 140)}` : "Status is Failed.", next: row.nextAction || "Fix the error or put it on Hold." };
  }
  if (/^qa review$/i.test(row.status ?? "")) {
    return { ...base, score: 62, title: `In QA review: ${title}`, why: "Waiting on a human QA pass.", next: row.nextAction || "Review it and set the result." };
  }
  if (/jordan|coach jay|\bjay\b/i.test(row.nextOwner ?? "") && row.nextAction) {
    return { ...base, score: 60, title, why: `Next owner is you.`, next: row.nextAction };
  }
  return { ...base, score: 0, title, why: "", next: "", muted: MUTE.noAction };
}

// ── Ranking ─────────────────────────────────────────────────────────────────

export function rank(candidates: Candidate[], sources: SourceStatus[], now: number): Queue {
  const muted = new Map<string, number>();
  const signal: Signal[] = [];
  for (const c of candidates) {
    const at = ms(c.at);
    const reason = c.muted ?? (c.kind !== "money" && at !== null && now - at > 30 * DAY ? MUTE.stale : undefined);
    if (reason) {
      muted.set(reason, (muted.get(reason) ?? 0) + 1);
      continue;
    }
    const { muted: _ignored, ...s } = c;
    signal.push(s);
  }
  // Highest score first; on a tie the older item goes first, since it has waited longer.
  signal.sort((a, b) => b.score - a.score || (ms(a.at) ?? now) - (ms(b.at) ?? now));
  const counted = Array.from(muted).map(([reason, count]) => ({ reason, count })).sort((a, b) => b.count - a.count);
  return {
    generated_at: new Date(now).toISOString(),
    do_now: signal.slice(0, 3),
    next: signal.slice(3, 10),
    more: Math.max(0, signal.length - 10),
    muted: counted,
    muted_total: counted.reduce((sum, m) => sum + m.count, 0),
    sources,
  };
}
