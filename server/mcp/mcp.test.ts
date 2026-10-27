import crypto from "node:crypto";
import type { AddressInfo } from "node:net";
import type { Server } from "node:http";
import express from "express";
import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";

const leads = [
  { id: "recAAAAAAAAAAAAA1", fields: { "Lead Name": "Ana Test", Email: "ana@example.com", "Funnel Stage": "Chat lead", Source: "Instagram DM → jayleefit.com Ask Jay chat", Notes: "x".repeat(400) } },
];
const listRecords = vi.fn(async () => ({ records: leads, offset: "itrNext/rec1" }));
const updateRecord = vi.fn(async (_table: string, id: string, fields: Record<string, unknown>) => ({ id, fields: { ...leads[0].fields, ...fields } }));
vi.mock("../airtable", async importOriginal => ({
  ...(await importOriginal<typeof import("../airtable")>()),
  airtableConfigured: () => true,
  listRecords: (...args: unknown[]) => listRecords(...(args as [])),
  findLeadByEmail: async (email: string) => leads.find(l => l.fields.Email === email) ?? null,
  updateRecord: (...args: [string, string, Record<string, unknown>]) => updateRecord(...args),
}));

import { registerMcp } from "./index";
import { registerBrain } from "../brain";
import { resetLimits } from "../claude";

const PASSWORD = "correct horse battery";
const CALLBACK = "https://claude.ai/api/mcp/auth_callback";
let base: string;
let server: Server;

beforeAll(async () => {
  const app = express();
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));
  server = app.listen(0);
  await new Promise(resolve => server.once("listening", resolve));
  base = `http://localhost:${(server.address() as AddressInfo).port}`;
  process.env.PUBLIC_SITE_URL = base;
  process.env.MCP_OWNER_PASSWORD = PASSWORD;
  process.env.MCP_SIGNING_SECRET = "s".repeat(48);
  registerMcp(app);
  registerBrain(app);
});

afterAll(() => {
  server.close();
  delete process.env.PUBLIC_SITE_URL;
  delete process.env.MCP_OWNER_PASSWORD;
  delete process.env.MCP_SIGNING_SECRET;
});

const form = (data: Record<string, string>) => ({
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams(data).toString(),
  redirect: "manual" as const,
});

async function register(redirect = CALLBACK) {
  const res = await fetch(`${base}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_name: "Claude", redirect_uris: [redirect], token_endpoint_auth_method: "client_secret_post" }),
  });
  return { status: res.status, body: await res.json() };
}

/** Walks the sign-in a Claude connector does and returns its tokens. */
async function signIn() {
  resetLimits();
  const { body: client } = await register();
  const verifier = crypto.randomBytes(32).toString("base64url");
  const challenge = crypto.createHash("sha256").update(verifier).digest("base64url");
  const params = new URLSearchParams({
    response_type: "code", client_id: client.client_id, redirect_uri: CALLBACK,
    code_challenge: challenge, code_challenge_method: "S256", state: "st8", resource: `${base}/mcp`,
  });
  const page = await (await fetch(`${base}/authorize?${params}`)).text();
  const signedForm = page.match(/name="form" value="([^"]+)"/)![1].replace(/&amp;/g, "&");
  const login = await fetch(`${base}/mcp-login`, form({ form: signedForm, password: PASSWORD, action: "allow" }));
  const location = new URL(login.headers.get("location")!);
  const code = location.searchParams.get("code")!;
  const tokenRes = await fetch(`${base}/token`, form({
    grant_type: "authorization_code", code, code_verifier: verifier, redirect_uri: CALLBACK,
    client_id: client.client_id, client_secret: client.client_secret, resource: `${base}/mcp`,
  }));
  return { client, code, verifier, signedForm, location, tokenRes, tokens: await tokenRes.json() };
}

async function rpc(token: string, method: string, params: Record<string, unknown> = {}) {
  const res = await fetch(`${base}/mcp`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", Accept: "application/json, text/event-stream" },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }),
  });
  return { status: res.status, body: res.headers.get("content-type")?.includes("json") ? await res.json() : await res.text() };
}

describe("website MCP sign-in", () => {
  it("advertises OAuth metadata and challenges unauthenticated calls", async () => {
    const meta = await (await fetch(`${base}/.well-known/oauth-protected-resource/mcp`)).json();
    expect(meta.resource).toBe(`${base}/mcp`);
    const as = await (await fetch(`${base}/.well-known/oauth-authorization-server`)).json();
    expect(as.registration_endpoint).toBe(`${base}/register`);
    const res = await fetch(`${base}/mcp`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    expect(res.status).toBe(401);
    expect(res.headers.get("www-authenticate")).toContain("resource_metadata");
  });

  it("only registers Claude's callbacks and localhost", async () => {
    expect((await register("https://evil.example/cb")).status).toBe(400);
    expect((await register("http://localhost:53682/callback")).status).toBe(201);
  });

  it("signs in with the owner password and issues working tokens", async () => {
    const { location, tokenRes, tokens } = await signIn();
    expect(location.origin + location.pathname).toBe(CALLBACK);
    expect(location.searchParams.get("state")).toBe("st8");
    expect(tokenRes.status).toBe(200);
    expect(tokens.access_token).toBeTruthy();
    expect(tokens.refresh_token).toBeTruthy();
  });

  it("rejects a wrong password, a reused code and a tampered token", async () => {
    const { client, code, verifier, signedForm, tokens } = await signIn();
    const wrong = await fetch(`${base}/mcp-login`, form({ form: signedForm, password: "nope", action: "allow" }));
    expect(wrong.status).toBe(401);
    expect(await wrong.text()).toContain("isn&#39;t right");

    const reuse = await fetch(`${base}/token`, form({
      grant_type: "authorization_code", code, code_verifier: verifier, redirect_uri: CALLBACK,
      client_id: client.client_id, client_secret: client.client_secret,
    }));
    expect(reuse.status).toBe(400);

    const tampered = tokens.access_token.replace(/.$/, c => (c === "A" ? "B" : "A"));
    expect((await rpc(tampered, "tools/list")).status).toBe(401);
  });

  it("accepts client credentials sent as HTTP Basic", async () => {
    const { client, tokens } = await signIn();
    const res = await fetch(`${base}/token`, {
      ...form({ grant_type: "refresh_token", refresh_token: tokens.refresh_token }),
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        Authorization: `Basic ${Buffer.from(`${encodeURIComponent(client.client_id)}:${encodeURIComponent(client.client_secret)}`).toString("base64")}`,
      },
    });
    expect(res.status).toBe(200);
    expect(client.token_endpoint_auth_method).toBe("client_secret_post");
  });

  it("refreshes tokens", async () => {
    const { client, tokens } = await signIn();
    const res = await fetch(`${base}/token`, form({
      grant_type: "refresh_token", refresh_token: tokens.refresh_token,
      client_id: client.client_id, client_secret: client.client_secret,
    }));
    expect(res.status).toBe(200);
    expect((await res.json()).access_token).toBeTruthy();
  });

  it("locks sign-in after five wrong passwords", async () => {
    const { signedForm } = await signIn();
    resetLimits();
    for (let i = 0; i < 5; i++) await fetch(`${base}/mcp-login`, form({ form: signedForm, password: "nope", action: "allow" }));
    const locked = await fetch(`${base}/mcp-login`, form({ form: signedForm, password: PASSWORD, action: "allow" }));
    expect(locked.status).toBe(429);
  });
});

describe("website MCP tools", () => {
  it("lists the tools and runs them", async () => {
    const { tokens } = await signIn();
    const list = await rpc(tokens.access_token, "tools/list");
    const names = list.body.result.tools.map((t: { name: string }) => t.name);
    expect(names).toEqual(expect.arrayContaining([
      "jayleefit_site_info", "jayleefit_calculate_numbers", "jayleefit_site_status", "jayleefit_list_leads",
      "jayleefit_get_lead", "jayleefit_list_remap_orders", "jayleefit_get_remap_order", "jayleefit_list_payment_reports",
      "jayleefit_find_client", "jayleefit_update_lead_stage", "jayleefit_set_payment_status", "jayleefit_retry_remap", "jayleefit_signal_queue",
    ]));

    const calc = await rpc(tokens.access_token, "tools/call", {
      name: "jayleefit_calculate_numbers",
      arguments: { units: "metric", sex: "male", age: 35, height: 180, weight: 90, activity: "moderate", goal: "fat-loss" },
    });
    expect(calc.body.result.structuredContent).toMatchObject({ bmr: 1855, targetCalories: 2300, proteinG: 180 });

    const leadsRes = await rpc(tokens.access_token, "tools/call", { name: "jayleefit_list_leads", arguments: { stage: "chat", limit: 5 } });
    const data = leadsRes.body.result.structuredContent;
    expect(data.leads[0]).toMatchObject({ email: "ana@example.com", stage: "Chat lead" });
    expect(data.leads[0].notes.length).toBeLessThan(310);
    expect(data).toMatchObject({ has_more: true, next_cursor: "itrNext/rec1" });
    expect(listRecords).toHaveBeenCalledWith("leads", expect.objectContaining({ formula: expect.stringContaining("FIND(LOWER('chat')"), pageSize: 5 }));

    const update = await rpc(tokens.access_token, "tools/call", {
      name: "jayleefit_update_lead_stage", arguments: { lead: "ana@example.com", stage: "Discovery call booked", note: "Call Tue 3pm" },
    });
    expect(update.body.result.structuredContent).toMatchObject({ updated: true, previous_stage: "Chat lead" });
    expect(updateRecord).toHaveBeenCalledWith("leads", "recAAAAAAAAAAAAA1", expect.objectContaining({ "Funnel Stage": "Discovery call booked", Notes: expect.stringContaining("Call Tue 3pm") }));
  });

  it("returns actionable errors for bad input", async () => {
    const { tokens } = await signIn();
    const res = await rpc(tokens.access_token, "tools/call", {
      name: "jayleefit_calculate_numbers",
      arguments: { units: "imperial", sex: "male", age: 35, height: 180, weight: 198, activity: "moderate", goal: "fat-loss" },
    });
    expect(res.body.result.isError).toBe(true);
    expect(res.body.result.content[0].text).toContain("inches");
  });
});

describe("Neural HUD", () => {
  it("ranks the queue through the connector and offers the daily brief prompt", async () => {
    const { tokens } = await signIn();
    const res = await rpc(tokens.access_token, "tools/call", { name: "jayleefit_signal_queue", arguments: {} });
    const queue = res.body.result.structuredContent;
    expect(queue.do_now.length).toBeGreaterThan(0);
    expect(queue.do_now[0].score).toBeGreaterThanOrEqual(queue.do_now.at(-1).score);
    expect(queue.sources).toEqual(expect.arrayContaining([
      expect.objectContaining({ source: "airtable", connected: true }),
      expect.objectContaining({ source: "linear", connected: false }),
      expect.objectContaining({ source: "notion", connected: false }),
    ]));
    expect(queue.also_check.join(" ")).toContain("Gmail");
    expect(queue.hud).toBe(`${base}/brain`);

    const prompts = await rpc(tokens.access_token, "prompts/list");
    expect(prompts.body.result.prompts.map((p: { name: string }) => p.name)).toContain("daily_brief");
    const brief = await rpc(tokens.access_token, "prompts/get", { name: "daily_brief" });
    expect(brief.body.result.messages[0].content.text).toContain("jayleefit_signal_queue");
  });

  it("keeps the HUD API behind the owner password", async () => {
    expect((await fetch(`${base}/api/brain/queue`)).status).toBe(401);
    const json = (password: string) => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ password }) });
    expect((await fetch(`${base}/api/brain/login`, json("wrong password!"))).status).toBe(401);
    const login = await fetch(`${base}/api/brain/login`, json(PASSWORD));
    expect(login.status).toBe(200);
    const cookie = login.headers.get("set-cookie")!;
    expect(cookie).toMatch(/HttpOnly/i);
    expect(cookie).toMatch(/SameSite=Strict/i);
    const queue = await fetch(`${base}/api/brain/queue`, { headers: { cookie: cookie.split(";")[0] } });
    expect(queue.status).toBe(200);
    expect(await queue.json()).toHaveProperty("do_now");
    const tampered = cookie.split(";")[0].replace(/.$/, c => (c === "A" ? "B" : "A"));
    expect((await fetch(`${base}/api/brain/queue`, { headers: { cookie: tampered } })).status).toBe(401);
  });
});
