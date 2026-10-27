import type { Express, Request, Response } from "express";
import { takeSlot } from "../claude";
import { BRAIN_COOKIE, brainSessionSeconds, brainSessionValid, mcpConfigProblem, passwordMatches, sealBrainSession } from "../mcp/auth";
import { buildQueue } from "./queue";

/**
 * The Neural HUD's API for the owner-only /brain page. Signs in with the same
 * owner password as the Claude connector and keeps a signed 12-hour cookie.
 * Off (503) until the connector's owner password and signing secret are set.
 */

const LOGINS_PER_HOUR = 10;

function readCookie(req: Request, name: string): string | undefined {
  for (const part of (req.headers.cookie ?? "").split(";")) {
    const [key, ...rest] = part.trim().split("=");
    if (key === name) return decodeURIComponent(rest.join("="));
  }
  return undefined;
}

function cookieOptions(req: Request) {
  return { httpOnly: true, secure: req.secure, sameSite: "strict" as const, path: "/api/brain" };
}

function offline(res: Response): boolean {
  const problem = mcpConfigProblem();
  if (!problem) return false;
  res.status(503).json({ error: `The Neural HUD is off: ${problem}. Set it in Railway → jayleefit-web → Variables.` });
  return true;
}

export function registerBrain(app: Express): void {
  app.post("/api/brain/login", (req, res) => {
    if (offline(res)) return;
    if (!takeSlot("brain-login", req.ip || "unknown", LOGINS_PER_HOUR)) {
      res.status(429).json({ error: "Too many sign-in attempts. Try again in an hour." });
      return;
    }
    const password = typeof req.body?.password === "string" ? req.body.password : "";
    if (!password || !passwordMatches(password)) {
      res.status(401).json({ error: "That password doesn't match the owner password." });
      return;
    }
    res.cookie(BRAIN_COOKIE, sealBrainSession(), { ...cookieOptions(req), maxAge: brainSessionSeconds() * 1000 });
    res.json({ ok: true });
  });

  app.post("/api/brain/logout", (req, res) => {
    res.clearCookie(BRAIN_COOKIE, cookieOptions(req));
    res.json({ ok: true });
  });

  app.get("/api/brain/queue", async (req, res) => {
    if (offline(res)) return;
    res.set("Cache-Control", "no-store");
    if (!brainSessionValid(readCookie(req, BRAIN_COOKIE))) {
      res.status(401).json({ error: "Sign in with the owner password." });
      return;
    }
    try {
      res.json(await buildQueue());
    } catch (error) {
      console.error("[Brain] queue failed:", error);
      res.status(500).json({ error: "The queue couldn't be built. Check the Railway logs." });
    }
  });
}
