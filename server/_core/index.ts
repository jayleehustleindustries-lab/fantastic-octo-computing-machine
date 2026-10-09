import "dotenv/config";
import express from "express";
import { createServer } from "http";
import net from "net";
import { createExpressMiddleware } from "@trpc/server/adapters/express";
import { registerOAuthRoutes } from "./oauth";
import { handleStripeWebhook, stripeConfigured } from "../remap";
import { registerStorageProxy } from "./storageProxy";
import { appRouter, siteCapabilities } from "../routers";
import { ENV } from "./env";
import { createContext } from "./context";
import { serveStatic, setupVite } from "./vite";

function isPortAvailable(port: number): Promise<boolean> {
  return new Promise(resolve => {
    const server = net.createServer();
    server.listen(port, () => {
      server.close(() => resolve(true));
    });
    server.on("error", () => resolve(false));
  });
}

async function findAvailablePort(startPort: number = 3000): Promise<number> {
  for (let port = startPort; port < startPort + 20; port++) {
    if (await isPortAvailable(port)) {
      return port;
    }
  }
  throw new Error(`No available port found starting from ${startPort}`);
}

async function startServer() {
  const app = express();
  const server = createServer(app);
  // Railway sits in front as a proxy; trust it so req.ip is the visitor's address.
  app.set("trust proxy", 1);
  // Configure body parser with larger size limit for file uploads
  // Stripe signs the raw request body, so this route must read it before the JSON parser does.
  app.post("/api/stripe/webhook", express.raw({ type: "application/json", limit: "1mb" }), async (req, res) => {
    const signature = req.get("stripe-signature");
    if (!stripeConfigured() || !signature) {
      res.status(400).send("Stripe webhook not configured");
      return;
    }
    try {
      await handleStripeWebhook(req.body as Buffer, signature);
      res.json({ received: true });
    } catch (error) {
      console.error("[Stripe] webhook rejected:", error instanceof Error ? error.message : error);
      res.status(400).send("Webhook error");
    }
  });

  app.use(express.json({ limit: "50mb" }));
  app.use(express.urlencoded({ limit: "50mb", extended: true }));

  // Railway's healthcheck. Also shows which optional services are switched on.
  app.get("/api/health", (_req, res) => {
    res.json({ ok: true, ...siteCapabilities() });
  });

  // Manus runtime pieces, only when this runs inside Manus.
  if (ENV.forgeApiUrl && ENV.forgeApiKey) registerStorageProxy(app);
  if (ENV.oAuthServerUrl) registerOAuthRoutes(app);
  // tRPC API
  app.use(
    "/api/trpc",
    createExpressMiddleware({
      router: appRouter,
      createContext,
    })
  );
  // development mode uses Vite, production mode uses static files
  if (process.env.NODE_ENV === "development") {
    await setupVite(app, server);
  } else {
    serveStatic(app);
  }

  const preferredPort = parseInt(process.env.PORT || "3000");
  const port = await findAvailablePort(preferredPort);

  if (port !== preferredPort) {
    console.log(`Port ${preferredPort} is busy, using port ${port} instead`);
  }

  server.listen(port, () => {
    console.log(`Server running on http://localhost:${port}/`);
  });
}

startServer().catch(console.error);
