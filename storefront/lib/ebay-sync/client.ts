/**
 * Thin wrapper around eBay's Sell APIs (Inventory, Taxonomy, Metadata).
 * Defaults to eBay's Sandbox environment — a real production listing
 * should only happen after a sandbox dry run looks right, same
 * "preview before you spend/publish" rule used elsewhere in this repo.
 *
 * Untested against eBay's live API (no credentials exist yet — see
 * ../../../root/.claude/plans for the prerequisite). Endpoint shapes
 * follow eBay's documented REST conventions; verify against
 * developer.ebay.com once real credentials are available, before the
 * first real run.
 *
 * Required env vars:
 *   EBAY_APP_ID       — Client ID from the eBay Developer Program
 *   EBAY_CERT_ID      — Client Secret from the eBay Developer Program
 *   EBAY_REFRESH_TOKEN — obtained once via eBay's OAuth consent flow
 *                         (the user must do this step themselves)
 *   EBAY_ENV          — "sandbox" (default) or "production"
 *   EBAY_MARKETPLACE_ID — defaults to EBAY_US
 */

const ENV = process.env.EBAY_ENV === "production" ? "production" : "sandbox";
const API_BASE =
  ENV === "production" ? "https://api.ebay.com" : "https://api.sandbox.ebay.com";
const MARKETPLACE_ID = process.env.EBAY_MARKETPLACE_ID || "EBAY_US";

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is not set. See storefront/lib/ebay-sync/README.md.`);
  }
  return value;
}

let cachedAccessToken: { token: string; expiresAt: number } | null = null;

/** Exchanges the long-lived refresh token for a short-lived access token. */
async function getAccessToken(): Promise<string> {
  if (cachedAccessToken && cachedAccessToken.expiresAt > Date.now()) {
    return cachedAccessToken.token;
  }

  const appId = requireEnv("EBAY_APP_ID");
  const certId = requireEnv("EBAY_CERT_ID");
  const refreshToken = requireEnv("EBAY_REFRESH_TOKEN");

  const tokenUrl =
    ENV === "production"
      ? "https://api.ebay.com/identity/v1/oauth2/token"
      : "https://api.sandbox.ebay.com/identity/v1/oauth2/token";

  const basicAuth = Buffer.from(`${appId}:${certId}`).toString("base64");
  const res = await fetch(tokenUrl, {
    method: "POST",
    headers: {
      Authorization: `Basic ${basicAuth}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      refresh_token: refreshToken,
      scope: "https://api.ebay.com/oauth/api_scope/sell.inventory",
    }),
  });

  if (!res.ok) {
    throw new Error(`eBay token refresh failed: ${res.status} ${await res.text()}`);
  }

  const data = (await res.json()) as { access_token: string; expires_in: number };
  cachedAccessToken = {
    token: data.access_token,
    expiresAt: Date.now() + (data.expires_in - 60) * 1000,
  };
  return data.access_token;
}

async function ebayFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = await getAccessToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "Content-Language": "en-US",
      ...init.headers,
    },
  });
  if (!res.ok) {
    throw new Error(`eBay API error on ${path}: ${res.status} ${await res.text()}`);
  }
  return res;
}

/** Resolves a real eBay category ID from a free-text search — never guessed. */
export async function getCategorySuggestions(
  query: string
): Promise<{ categoryId: string; categoryName: string } | null> {
  const treeRes = await ebayFetch(
    `/commerce/taxonomy/v1/get_default_category_tree_id?marketplace_id=${MARKETPLACE_ID}`
  );
  const { categoryTreeId } = (await treeRes.json()) as { categoryTreeId: string };

  const res = await ebayFetch(
    `/commerce/taxonomy/v1/category_tree/${categoryTreeId}/get_category_suggestions?q=${encodeURIComponent(
      query
    )}`
  );
  const data = (await res.json()) as {
    categorySuggestions?: { category: { categoryId: string; categoryName: string } }[];
  };
  const top = data.categorySuggestions?.[0];
  return top ? { categoryId: top.category.categoryId, categoryName: top.category.categoryName } : null;
}

/** Resolves the real, category-specific set of valid condition values — never guessed. */
export async function getItemConditionPolicies(
  categoryId: string
): Promise<{ conditionId: string; conditionDescription: string }[]> {
  const res = await ebayFetch(
    `/sell/metadata/v1/marketplace/${MARKETPLACE_ID}/get_item_condition_policies?filter=categoryIds:{${categoryId}}`
  );
  const data = (await res.json()) as {
    itemConditionPolicies?: {
      itemConditions?: { conditionId: string; conditionDescription: string }[];
    }[];
  };
  return data.itemConditionPolicies?.[0]?.itemConditions ?? [];
}

export async function createOrReplaceInventoryItem(
  sku: string,
  body: Record<string, unknown>
): Promise<void> {
  await ebayFetch(`/sell/inventory/v1/inventory_item/${encodeURIComponent(sku)}`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export async function createOffer(body: Record<string, unknown>): Promise<{ offerId: string }> {
  const res = await ebayFetch("/sell/inventory/v1/offer", {
    method: "POST",
    body: JSON.stringify(body),
  });
  return (await res.json()) as { offerId: string };
}

export async function publishOffer(offerId: string): Promise<{ listingId: string }> {
  const res = await ebayFetch(`/sell/inventory/v1/offer/${offerId}/publish`, {
    method: "POST",
  });
  return (await res.json()) as { listingId: string };
}

export { ENV as EBAY_ENV, MARKETPLACE_ID as EBAY_MARKETPLACE_ID };
