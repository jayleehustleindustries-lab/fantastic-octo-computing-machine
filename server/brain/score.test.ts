import { describe, expect, it } from "vitest";
import { fromLead, fromLinearIssue, fromPayment, fromRemapOrder, fromSchedulerRow, hotLeadScore, MUTE, rank, type Candidate } from "./score";

const NOW = Date.parse("2026-10-27T18:00:00Z");
const hoursAgo = (h: number) => new Date(NOW - h * 3600_000).toISOString();

describe("hotLeadScore", () => {
  it("holds at 90 for 48 hours, then drops 10 a day to a floor of 60", () => {
    expect(hotLeadScore(NOW - 2 * 3600_000, NOW)).toBe(90);
    expect(hotLeadScore(NOW - 48 * 3600_000, NOW)).toBe(90);
    expect(hotLeadScore(NOW - 50 * 3600_000, NOW)).toBe(80);
    expect(hotLeadScore(NOW - 73 * 3600_000, NOW)).toBe(70);
    expect(hotLeadScore(NOW - 30 * 24 * 3600_000, NOW)).toBe(60);
  });
});

describe("Airtable rules", () => {
  it("scores a payment report waiting for review as money at 100", () => {
    const c = fromPayment("recA", { Name: "Sam", Amount: "$297", Method: "Cash App", "Reported Date": hoursAgo(3) }, NOW);
    expect(c).toMatchObject({ kind: "money", score: 100, source: "airtable" });
    expect(c.title).toContain("$297 via Cash App");
    expect(c.why).toContain("3h ago");
  });

  it("flags failed and stuck paid Remap orders, and mutes ones still on time", () => {
    expect(fromRemapOrder("r1", { Name: "A", Status: "Failed", Error: "timeout" }, NOW).score).toBe(100);
    expect(fromRemapOrder("r2", { Name: "B", Status: "Paid", "Paid At": hoursAgo(1) }, NOW).score).toBe(100);
    const fresh = fromRemapOrder("r3", { Name: "C", Status: "Paid", "Paid At": new Date(NOW - 5 * 60_000).toISOString() }, NOW);
    expect(fresh.muted).toBe(MUTE.noAction);
  });

  it("treats a finished application with no next action as a hot lead", () => {
    const c = fromLead("l1", { "Lead Name": "Dee", "Funnel Stage": "Application complete", "Created Date": hoursAgo(26) }, NOW);
    expect(c).toMatchObject({ kind: "lead", score: 90 });
    expect(c.muted).toBeUndefined();
  });

  it("mutes leads that already have a next action, sample records and buyers", () => {
    expect(fromLead("l2", { "Lead Name": "E", "Funnel Stage": "Application complete", "Next Action": "Call Tue" }, NOW).muted).toBe(MUTE.handled);
    expect(fromLead("l3", { "Lead Name": "Sample Lead", "Funnel Stage": "Application complete" }, NOW).muted).toBe(MUTE.sample);
    expect(fromLead("l4", { "Lead Name": "F", "Funnel Stage": "Remap purchased" }, NOW).muted).toBe(MUTE.noAction);
  });

  it("gives a half-finished application a low, visible score", () => {
    expect(fromLead("l5", { "Lead Name": "G", "Funnel Stage": "Application — phase 2 of 4", "Created Date": hoursAgo(5) }, NOW).score).toBe(50);
  });
});

describe("Linear rules", () => {
  const issue = { identifier: "JOR-41", title: "Remap checkout copy", team: "JOR" };
  it("ranks urgent, overdue, due-soon and high priority in that order", () => {
    expect(fromLinearIssue({ ...issue, priority: 1 }, NOW).score).toBe(85);
    expect(fromLinearIssue({ ...issue, priority: 3, dueDate: "2026-10-20" }, NOW).score).toBe(80);
    expect(fromLinearIssue({ ...issue, priority: 3, dueDate: "2026-10-28" }, NOW).score).toBe(75);
    expect(fromLinearIssue({ ...issue, priority: 2 }, NOW).score).toBe(70);
    expect(fromLinearIssue({ ...issue, priority: 3 }, NOW).muted).toBe(MUTE.noAction);
  });

  it("mutes work that isn't fitness", () => {
    expect(fromLinearIssue({ ...issue, title: "AI automation offer pricing", priority: 1 }, NOW).muted).toBe(MUTE.notFitness);
    expect(fromLinearIssue({ ...issue, priority: 1, labels: ["EHC"] }, NOW).muted).toBe(MUTE.notFitness);
  });

  it("uses LINEAR_FITNESS_SCOPE when given", () => {
    expect(fromLinearIssue({ ...issue, priority: 1, project: "Coaching" }, NOW, ["coaching"]).score).toBe(85);
    expect(fromLinearIssue({ ...issue, priority: 1, project: "Other" }, NOW, ["coaching"]).muted).toBe(MUTE.notFitness);
  });
});

describe("Notion scheduler rules", () => {
  const row = { id: "n1", name: "JLH-WED-LEAD", brand: "JayLeeHustle" };
  it("asks for publish approval when content goes out within 72 hours", () => {
    const c = fromSchedulerRow({ ...row, status: "Ready", publishApproval: "NOT_APPROVED", scheduledAt: hoursAgo(-30) }, NOW);
    expect(c).toMatchObject({ kind: "gate", score: 70 });
  });

  it("surfaces failed and QA review rows, and mutes everything else", () => {
    expect(fromSchedulerRow({ ...row, status: "Failed", lastError: "caption too long" }, NOW).score).toBe(65);
    expect(fromSchedulerRow({ ...row, status: "QA Review" }, NOW).score).toBe(62);
    expect(fromSchedulerRow({ ...row, status: "Captured" }, NOW).muted).toBe(MUTE.noAction);
    expect(fromSchedulerRow({ ...row, brand: "EHC", status: "Failed" }, NOW).muted).toBe(MUTE.notFitness);
  });
});

describe("rank", () => {
  const make = (id: string, score: number, extra: Partial<Candidate> = {}): Candidate => ({
    id, source: "airtable", kind: "lead", score, title: id, why: "", next: "", at: hoursAgo(1), ...extra,
  });

  it("keeps the top 3 as DO NOW, the next 7 as NEXT, and counts the rest", () => {
    const q = rank(Array.from({ length: 12 }, (_, i) => make(`c${i}`, 50 + i)), [], NOW);
    expect(q.do_now.map(s => s.score)).toEqual([61, 60, 59]);
    expect(q.next).toHaveLength(7);
    expect(q.more).toBe(2);
  });

  it("mutes stale items but never stale money, and groups mute reasons", () => {
    const q = rank(
      [
        make("old-lead", 90, { at: hoursAgo(24 * 40) }),
        make("old-money", 100, { kind: "money", at: hoursAgo(24 * 40) }),
        make("noise1", 0, { muted: MUTE.notFitness }),
        make("noise2", 0, { muted: MUTE.notFitness }),
      ],
      [],
      NOW,
    );
    expect(q.do_now.map(s => s.id)).toEqual(["old-money"]);
    expect(q.muted).toEqual([
      { reason: MUTE.notFitness, count: 2 },
      { reason: MUTE.stale, count: 1 },
    ]);
    expect(q.muted_total).toBe(3);
  });

  it("puts the older item first on a tie", () => {
    const q = rank([make("new", 90, { at: hoursAgo(1) }), make("old", 90, { at: hoursAgo(10) })], [], NOW);
    expect(q.do_now.map(s => s.id)).toEqual(["old", "new"]);
  });
});
