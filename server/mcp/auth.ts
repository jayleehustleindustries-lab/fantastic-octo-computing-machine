import crypto from "node:crypto";
import type { Request, Response } from "express";
import type { OAuthRegisteredClientsStore } from "@modelcontextprotocol/sdk/server/auth/clients.js";
import { InvalidClientMetadataError, InvalidGrantError, InvalidTargetError, InvalidTokenError } from "@modelcontextprotocol/sdk/server/auth/errors.js";
import type { AuthorizationParams, OAuthServerProvider } from "@modelcontextprotocol/sdk/server/auth/provider.js";
import type { AuthInfo } from "@modelcontextprotocol/sdk/server/auth/types.js";
import type { OAuthClientInformationFull, OAuthTokens } from "@modelcontextprotocol/sdk/shared/auth.js";
import { takeSlot } from "../claude";
import { loginPage } from "./loginPage";

/**
 * Sign-in for the website's MCP connector. There is one user, the owner, who
 * signs in with MCP_OWNER_PASSWORD. Nothing is stored: client registrations,
 * codes and tokens are all HMAC-signed with MCP_SIGNING_SECRET, so a redeploy
 * never logs Claude out, and changing the secret signs every client out.
 */

export const MCP_SCOPE = "jayleefit";
const ACCESS_TTL_SECONDS = 60 * 60;
const REFRESH_TTL_SECONDS = 90 * 24 * 60 * 60;
const CODE_TTL_SECONDS = 2 * 60;
const LOGIN_FORM_TTL_SECONDS = 10 * 60;
const LOGIN_TRIES_PER_HOUR = 5;

/** Claude's OAuth callbacks. Claude Code listens on a localhost port. */
const CLAUDE_CALLBACKS = ["https://claude.ai/api/mcp/auth_callback", "https://claude.com/api/mcp/auth_callback"];

/** The site's public origin, e.g. https://www.jayleefit.com. */
export function siteUrl(): URL | null {
  const configured = process.env.PUBLIC_SITE_URL?.trim().replace(/\/+$/, "");
  const railway = process.env.RAILWAY_PUBLIC_DOMAIN?.trim();
  const origin = configured || (railway ? `https://${railway}` : "");
  return origin && URL.canParse(origin) ? new URL(`${origin}/`) : null;
}

/** Why the connector is off, or null when it's ready. */
export function mcpConfigProblem(): string | null {
  if (!process.env.MCP_OWNER_PASSWORD) return "MCP_OWNER_PASSWORD is not set";
  if (process.env.MCP_OWNER_PASSWORD.length < 10) return "MCP_OWNER_PASSWORD must be at least 10 characters";
  if (!process.env.MCP_SIGNING_SECRET) return "MCP_SIGNING_SECRET is not set";
  if (process.env.MCP_SIGNING_SECRET.length < 32) return "MCP_SIGNING_SECRET must be at least 32 characters";
  if (!siteUrl()) return "PUBLIC_SITE_URL is not set";
  return null;
}

export const mcpConfigured = () => mcpConfigProblem() === null;

// ── Signed values ───────────────────────────────────────────────────────────

type Kind = "client" | "login" | "code" | "access" | "refresh" | "brain";

const mac = (data: string) => crypto.createHmac("sha256", process.env.MCP_SIGNING_SECRET!).update(data).digest("base64url");

function seal(kind: Kind, payload: Record<string, unknown>, ttlSeconds?: number): string {
  const exp = ttlSeconds ? Math.floor(Date.now() / 1000) + ttlSeconds : undefined;
  const body = Buffer.from(JSON.stringify({ ...payload, exp })).toString("base64url");
  return `${body}.${mac(`${kind}.${body}`)}`;
}

function unseal<T extends Record<string, unknown>>(kind: Kind, value: unknown): (T & { exp?: number }) | null {
  if (typeof value !== "string" || value.length > 8000) return null;
  const [body, signature, extra] = value.split(".");
  if (!body || !signature || extra !== undefined) return null;
  const expected = Buffer.from(mac(`${kind}.${body}`));
  const given = Buffer.from(signature);
  if (expected.length !== given.length || !crypto.timingSafeEqual(expected, given)) return null;
  try {
    const payload = JSON.parse(Buffer.from(body, "base64url").toString("utf8"));
    if (payload.exp !== undefined && payload.exp < Date.now() / 1000) return null;
    return payload;
  } catch {
    return null;
  }
}

const clientSecretFor = (clientId: string) => mac(`client-secret.${clientId}`);

export function passwordMatches(given: string): boolean {
  const hash = (s: string) => crypto.createHash("sha256").update(s).digest();
  return crypto.timingSafeEqual(hash(given), hash(process.env.MCP_OWNER_PASSWORD ?? ""));
}

// ── Owner session for the Neural HUD page (/brain) ──────────────────────────

const BRAIN_SESSION_SECONDS = 12 * 60 * 60;
export const BRAIN_COOKIE = "jlh_brain";
export const brainSessionSeconds = () => BRAIN_SESSION_SECONDS;
export const sealBrainSession = () => seal("brain", { owner: true }, BRAIN_SESSION_SECONDS);
export const brainSessionValid = (value: unknown) => unseal<{ owner: boolean }>("brain", value)?.owner === true;

export function redirectAllowed(uri: string): boolean {
  if (CLAUDE_CALLBACKS.includes(uri)) return true;
  const extra = (process.env.MCP_EXTRA_REDIRECT_URIS ?? "").split(",").map(s => s.trim()).filter(Boolean);
  if (extra.includes(uri)) return true;
  if (!URL.canParse(uri)) return false;
  const url = new URL(uri);
  return url.protocol === "http:" && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);
}

// ── Clients (dynamic registration, no storage) ──────────────────────────────

type ClientCore = { r: string[]; n?: string; m: string; g?: string[]; iat: number };

const clientsStore: OAuthRegisteredClientsStore = {
  getClient(clientId) {
    const core = unseal<ClientCore>("client", clientId);
    if (!core) return undefined;
    return {
      client_id: clientId,
      client_id_issued_at: core.iat,
      redirect_uris: core.r,
      client_name: core.n,
      token_endpoint_auth_method: core.m,
      grant_types: core.g,
      response_types: ["code"],
      ...(core.m === "none" ? {} : { client_secret: clientSecretFor(clientId), client_secret_expires_at: 0 }),
    };
  },

  registerClient(client) {
    const blocked = client.redirect_uris.filter(uri => !redirectAllowed(uri));
    if (blocked.length) {
      throw new InvalidClientMetadataError(`This server only signs in Claude. Redirect URI not allowed: ${blocked.join(", ")}`);
    }
    const core: ClientCore = {
      r: client.redirect_uris,
      n: client.client_name?.slice(0, 100),
      // The token endpoint reads the secret from the form body or a Basic header.
      m: client.token_endpoint_auth_method === "none" ? "none" : "client_secret_post",
      g: client.grant_types,
      iat: Math.floor(Date.now() / 1000),
    };
    const clientId = seal("client", core);
    return clientsStore.getClient(clientId) as OAuthClientInformationFull;
  },
};

// ── The provider ────────────────────────────────────────────────────────────

type LoginForm = { c: string; ru: string; cc: string; st?: string };
type CodePayload = { c: string; ru: string; cc: string; j: string };
type TokenPayload = { c: string; rs?: string; j: string };

/** Codes are single use while this process is up; their 2-minute life and PKCE cover a restart. */
const usedCodes = new Map<string, number>();

function markCodeUsed(id: string, exp: number): boolean {
  const now = Date.now() / 1000;
  usedCodes.forEach((expiry, key) => {
    if (expiry < now) usedCodes.delete(key);
  });
  if (usedCodes.has(id)) return false;
  usedCodes.set(id, exp);
  return true;
}

export function createAuthProvider(resource: URL): OAuthServerProvider & { handleLogin: (req: Request, res: Response) => void } {
  const nonce = () => crypto.randomBytes(12).toString("base64url");

  function issueTokens(clientId: string): OAuthTokens {
    return {
      access_token: seal("access", { c: clientId, rs: resource.href, j: nonce() }, ACCESS_TTL_SECONDS),
      token_type: "bearer",
      expires_in: ACCESS_TTL_SECONDS,
      refresh_token: seal("refresh", { c: clientId, j: nonce() }, REFRESH_TTL_SECONDS),
      scope: MCP_SCOPE,
    };
  }

  function checkResource(requested?: URL) {
    if (requested && requested.href.replace(/\/$/, "") !== resource.href.replace(/\/$/, "")) {
      throw new InvalidTargetError(`This server only issues tokens for ${resource.href}`);
    }
  }

  function readCode(client: OAuthClientInformationFull, code: string) {
    const payload = unseal<CodePayload>("code", code);
    if (!payload || payload.c !== client.client_id) throw new InvalidGrantError("The sign-in code is invalid or has expired. Connect again.");
    return payload;
  }

  function render(res: Response, status: number, options: Parameters<typeof loginPage>[0]) {
    res
      .status(status)
      .set({
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "no-store",
        "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
      })
      .send(loginPage(options));
  }

  function redirectWith(res: Response, redirectUri: string, params: Record<string, string | undefined>) {
    const url = new URL(redirectUri);
    for (const [key, value] of Object.entries(params)) if (value !== undefined) url.searchParams.set(key, value);
    res.redirect(302, url.href);
  }

  return {
    clientsStore,

    async authorize(client, params: AuthorizationParams, res) {
      checkResource(params.resource);
      const form = seal("login", { c: client.client_id, ru: params.redirectUri, cc: params.codeChallenge, st: params.state } satisfies LoginForm, LOGIN_FORM_TTL_SECONDS);
      render(res, 200, { form, clientName: client.client_name });
    },

    /** POST /mcp-login: the owner's password, or Cancel. */
    handleLogin(req, res) {
      const body = (req.body ?? {}) as Record<string, unknown>;
      const form = unseal<LoginForm>("login", body.form);
      if (!form || !clientsStore.getClient(form.c)) {
        render(res, 400, { expired: true });
        return;
      }
      if (body.action === "cancel") {
        redirectWith(res, form.ru, { error: "access_denied", error_description: "Sign-in was cancelled.", state: form.st });
        return;
      }
      if (!takeSlot("mcp-login", req.ip ?? "unknown", LOGIN_TRIES_PER_HOUR)) {
        render(res, 429, { form: String(body.form), error: "Too many tries. Wait an hour, then connect again." });
        return;
      }
      if (typeof body.password !== "string" || !passwordMatches(body.password)) {
        render(res, 401, { form: String(body.form), error: "That password isn't right." });
        return;
      }
      const code = seal("code", { c: form.c, ru: form.ru, cc: form.cc, j: nonce() } satisfies CodePayload, CODE_TTL_SECONDS);
      redirectWith(res, form.ru, { code, state: form.st });
    },

    async challengeForAuthorizationCode(client, code) {
      return readCode(client, code).cc;
    },

    async exchangeAuthorizationCode(client, code, _verifier, redirectUri, requestedResource) {
      const payload = readCode(client, code);
      if (redirectUri && redirectUri !== payload.ru) throw new InvalidGrantError("redirect_uri doesn't match the one used to sign in.");
      checkResource(requestedResource);
      if (!markCodeUsed(payload.j, payload.exp ?? 0)) throw new InvalidGrantError("This sign-in code was already used. Connect again.");
      return issueTokens(client.client_id);
    },

    async exchangeRefreshToken(client, refreshToken, _scopes, requestedResource) {
      const payload = unseal<TokenPayload>("refresh", refreshToken);
      if (!payload || payload.c !== client.client_id) throw new InvalidGrantError("The refresh token is invalid or has expired. Connect again.");
      checkResource(requestedResource);
      return issueTokens(client.client_id);
    },

    async verifyAccessToken(token): Promise<AuthInfo> {
      const payload = unseal<TokenPayload>("access", token);
      if (!payload || !clientsStore.getClient(payload.c)) throw new InvalidTokenError("Invalid or expired access token");
      return {
        token,
        clientId: payload.c,
        scopes: [MCP_SCOPE],
        expiresAt: payload.exp,
        resource: payload.rs ? new URL(payload.rs) : undefined,
      };
    },
  };
}

/**
 * Lets clients that send their credentials as HTTP Basic (the OAuth default)
 * use the token endpoint, which reads them from the form body.
 */
export function basicClientAuth(req: Request, _res: Response, next: () => void): void {
  const header = req.get("authorization");
  if (header?.startsWith("Basic ")) {
    const decoded = Buffer.from(header.slice(6), "base64").toString("utf8");
    const split = decoded.indexOf(":");
    if (split > 0) {
      const body = (req.body ?? {}) as Record<string, unknown>;
      body.client_id ??= decodeURIComponent(decoded.slice(0, split));
      body.client_secret ??= decodeURIComponent(decoded.slice(split + 1));
      req.body = body;
    }
  }
  next();
}
