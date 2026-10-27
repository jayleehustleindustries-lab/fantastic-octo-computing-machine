import { airtableConfigured, listRecords } from "../airtable";
import { siteUrl } from "../mcp/auth";
import {
  fromLead,
  fromLinearIssue,
  fromPayment,
  fromRemapOrder,
  fromSchedulerRow,
  rank,
  type Candidate,
  type LinearIssue,
  type Queue,
  type SchedulerRow,
  type SourceKey,
  type SourceStatus,
} from "./score";

/**
 * Reads every source the site can reach, scores it, and ranks it. Each source
 * is optional: a missing key shows as "not connected" instead of failing the
 * whole queue. Gmail, Calendar and Drive are merged by Claude through its own
 * connectors (see the daily_brief prompt), not here.
 */

const TIMEOUT_MS = 8000;
const NOTION_SCHEDULER_DB = () => process.env.NOTION_SCHEDULER_DB || "e10f14157a424f8da94496f7b016df38";
const linearScope = () => (process.env.LINEAR_FITNESS_SCOPE ?? "").split(",").map(s => s.trim()).filter(Boolean);

type SourceResult = { candidates: Candidate[]; status: SourceStatus };

async function readSource(source: SourceKey, label: string, configured: boolean, setup: string, read: () => Promise<Candidate[]>): Promise<SourceResult> {
  if (!configured) return { candidates: [], status: { source, label, connected: false, error: setup, count: 0 } };
  try {
    const candidates = await read();
    return { candidates, status: { source, label, connected: true, count: candidates.length } };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`[Brain] ${source} read failed:`, message);
    return { candidates: [], status: { source, label, connected: true, error: message.slice(0, 200), count: 0 } };
  }
}

async function readAirtable(now: number): Promise<Candidate[]> {
  const site = siteUrl();
  const [payments, orders, leads] = await Promise.all([
    listRecords("payments", { formula: `{Status} = 'Needs review'`, sortField: "Reported Date", pageSize: 50 }),
    listRecords("remap", { formula: `OR({Status} = 'Failed', {Status} = 'Paid', {Status} = 'Generating')`, sortField: "Created Date", pageSize: 50 }),
    listRecords("leads", { sortField: "Created Date", pageSize: 100 }),
  ]);
  return [
    ...payments.records.map(r => fromPayment(r.id, r.fields, now)),
    ...orders.records.map(r =>
      fromRemapOrder(r.id, r.fields, now, site && r.fields.Token ? new URL(`/remap/p/${r.fields.Token}`, site).href : null),
    ),
    ...leads.records.map(r => fromLead(r.id, r.fields, now)),
  ];
}

const LINEAR_QUERY = `query BrainIssues {
  viewer { assignedIssues(first: 75, filter: { state: { type: { nin: ["completed", "canceled"] } } }) {
    nodes { identifier title url priority dueDate updatedAt team { key name } project { name } labels { nodes { name } } }
  } }
}`;

async function readLinear(now: number): Promise<Candidate[]> {
  const response = await fetch("https://api.linear.app/graphql", {
    method: "POST",
    headers: { Authorization: process.env.LINEAR_API_KEY!, "Content-Type": "application/json" },
    body: JSON.stringify({ query: LINEAR_QUERY }),
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok || body.errors) throw new Error(`Linear ${response.status}: ${body.errors?.[0]?.message ?? "request failed"}`);
  const nodes: any[] = body.data?.viewer?.assignedIssues?.nodes ?? [];
  const scope = linearScope();
  return nodes.map(n =>
    fromLinearIssue(
      {
        identifier: n.identifier,
        title: n.title,
        url: n.url,
        priority: n.priority,
        dueDate: n.dueDate,
        updatedAt: n.updatedAt,
        team: n.team?.key ?? n.team?.name,
        project: n.project?.name,
        labels: (n.labels?.nodes ?? []).map((l: { name: string }) => l.name),
      } satisfies LinearIssue,
      now,
      scope,
    ),
  );
}

const plain = (prop: any): string => {
  if (!prop) return "";
  switch (prop.type) {
    case "title":
    case "rich_text":
      return (prop[prop.type] ?? []).map((t: { plain_text: string }) => t.plain_text).join("");
    case "select":
    case "status":
      return prop[prop.type]?.name ?? "";
    case "date":
      return prop.date?.start ?? "";
    default:
      return "";
  }
};

async function readNotion(now: number): Promise<Candidate[]> {
  const statuses = ["Captured", "QA Review", "Ready", "Scheduled", "Failed"];
  const response = await fetch(`https://api.notion.com/v1/databases/${NOTION_SCHEDULER_DB()}/query`, {
    method: "POST",
    headers: { Authorization: `Bearer ${process.env.NOTION_TOKEN}`, "Notion-Version": "2022-06-28", "Content-Type": "application/json" },
    body: JSON.stringify({ page_size: 100, filter: { or: statuses.map(name => ({ property: "Status", select: { equals: name } })) } }),
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(`Notion ${response.status}: ${body.message ?? "request failed"}`);
  return (body.results ?? []).map((page: any) => {
    const p = page.properties ?? {};
    return fromSchedulerRow(
      {
        id: page.id,
        name: plain(p.Name),
        url: page.url,
        status: plain(p.Status),
        brand: plain(p.Brand),
        publishApproval: plain(p["Human Publish Approval"]),
        scheduledAt: plain(p["Scheduled At"]) || null,
        nextAction: plain(p["Next Action"]),
        nextOwner: plain(p["Next Owner"]),
        lastError: plain(p["Last Error"]),
        editedAt: page.last_edited_time ?? null,
      } satisfies SchedulerRow,
      now,
    );
  });
}

export async function buildQueue(now = Date.now()): Promise<Queue> {
  const results = await Promise.all([
    readSource("airtable", "Airtable · leads, Remap, payments", airtableConfigured(), "Add AIRTABLE_API_TOKEN and AIRTABLE_BASE_ID in Railway.", () => readAirtable(now)),
    readSource("linear", "Linear · fitness issues", Boolean(process.env.LINEAR_API_KEY), "Add LINEAR_API_KEY in Railway.", () => readLinear(now)),
    readSource("notion", "Notion · Content Scheduler", Boolean(process.env.NOTION_TOKEN), "Add NOTION_TOKEN in Railway and share the Scheduler database with that integration.", () => readNotion(now)),
  ]);
  return rank(results.flatMap(r => r.candidates), results.map(r => r.status), now);
}
