import type { Express } from "express";
import { mcpAuthRouter, getOAuthProtectedResourceMetadataUrl } from "@modelcontextprotocol/sdk/server/auth/router.js";
import { requireBearerAuth } from "@modelcontextprotocol/sdk/server/auth/middleware/bearerAuth.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { basicClientAuth, createAuthProvider, MCP_SCOPE, mcpConfigProblem, siteUrl } from "./auth";
import { createMcpServer } from "./tools";

/**
 * The website as an MCP server at /mcp, for Claude's custom connectors.
 * Stateless: every POST gets a fresh server and transport. Off (404) until
 * MCP_OWNER_PASSWORD, MCP_SIGNING_SECRET and the site URL are set.
 */
export function registerMcp(app: Express): void {
  const problem = mcpConfigProblem();
  if (problem) {
    console.log(`[MCP] connector off: ${problem}`);
    return;
  }
  const site = siteUrl()!;
  const resource = new URL("/mcp", site);
  const provider = createAuthProvider(resource);

  app.post("/mcp-login", (req, res) => provider.handleLogin(req, res));
  app.post(["/token", "/revoke"], basicClientAuth);
  app.use(
    mcpAuthRouter({
      provider,
      issuerUrl: site,
      resourceServerUrl: resource,
      scopesSupported: [MCP_SCOPE],
      resourceName: "Everyday Hustle Co.",
    }),
  );

  const bearer = requireBearerAuth({
    verifier: provider,
    resourceMetadataUrl: getOAuthProtectedResourceMetadataUrl(resource),
    expectedResource: resource,
  });

  app.post("/mcp", bearer, async (req, res) => {
    const server = createMcpServer();
    const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined, enableJsonResponse: true });
    res.on("close", () => {
      void transport.close();
      void server.close();
    });
    try {
      await server.connect(transport);
      await transport.handleRequest(req, res, req.body);
    } catch (error) {
      console.error("[MCP] request failed:", error);
      if (!res.headersSent) res.status(500).json({ jsonrpc: "2.0", error: { code: -32603, message: "Internal server error" }, id: null });
    }
  });

  app.all("/mcp", (_req, res) => {
    res.status(405).set("Allow", "POST").json({ jsonrpc: "2.0", error: { code: -32000, message: "Method not allowed." }, id: null });
  });

  console.log(`[MCP] connector on at ${resource.href}`);
}
