# JayLeeFit- Finishing Plan

**Date:** 2026-09-25
**Branch:** `claude/jaylee-fit-website-build-aor3la`
**Engine:** Claude Opus / Fable — persistent planning brain across sessions

---

## Current State: What Actually Exists

### Storefront (EHC / Old Light) — 80% built, 0% live

| Area | Status | What's there |
|---|---|---|
| **Next.js app** | Builds clean | 11 routes: home, shop (catalog + filters), product detail, about, privacy, shipping/returns, terms, checkout success/cancel, Stripe checkout API, webhook |
| **12 components** | Working | Navbar, cart drawer, product cards, moon-phase badges, cross-promo banner, footer, marquee, price tags |
| **Stripe checkout** | Real but sandbox | Server re-prices from live inventory. Webhook verifies. Needs live keys for real money |
| **Inventory data** | Falls back to demo | Google Sheet is owner-only, so the app silently loads 10 hardcoded items instead of the real 71+ |
| **Product photos** | Zero assigned | 68 photos in `photo-inbox/`, matcher UI built, assignment CLI built, but `public/products/` is empty |
| **eBay sync** | Code exists | Real Sell API integration, sandbox default, needs credentials |
| **Facebook/Vendoo export** | Code exists | Copy-paste listing generators from live sheet data |
| **Asset pipeline** | Stage 1 only | Prompt templates for 4 shot angles, no generation run |
| **Deployment** | Not deployed | Needs Vercel + domain + env vars |

### JayLeeFit Coaching — Website built, not deployed

| Area | Status |
|---|---|
| Airtable schema | Live base (`JayLeeFit Client Hub`), 5 tables, macro engine works |
| Website (`jayleefit-website/`) | Builds clean. Home, About, Intake form → `/api/intake` → Airtable Clients table. Dark + gold theme. Needs `AIRTABLE_API_TOKEN` and a deploy |
| Methodology site (`mao-methodology/`) | Exists (13 sections); not reviewed in this plan |
| Testimonials | Home page shows "Our clients report" quotes — confirm these are real client words before launch, or remove them |
| Telegram bot | Designed (n8n guide exists), not built |
| ManyChat automation | Designed (docs/), not built |
| Client app | Design brief exists, not built |

### Content Engine — Design only

| Area | Status |
|---|---|
| Architecture doc | Complete (320 lines), multi-role pipeline designed |
| Video prompt builder | Pure functions exist (Kling 3.0 / Veo 3.1 request shapes) |
| Airtable base | Not created |
| Metricool | Confirmed live (brand 6394851), not wired |
| Running pipeline | Nothing runs |

---

## The Plan: Three Phases to "Finished"

### Phase 1 — Unblock the Storefront (owner actions + agent work)

These are the gates. Nothing else matters until they're cleared.

#### 1A. Owner must do (no agent can substitute):

| # | Action | Time | Why it's blocked |
|---|---|---|---|
| 1 | **Share the Google Sheet** — open `EHC Inventory Log`, Share → "Anyone with the link → Viewer" | 30 sec | Without this, the storefront shows 10 demo items instead of real inventory |
| 2 | **Fix Drive folder permissions** — `EHC-Background-Edited-Images` from Writer → Viewer | 30 sec | Anyone with the link can currently delete photos |
| 3 | **Do the photo matching pass** — open `storefront/tools/photo-matcher.html` in a browser, match each photo to its inventory item | 30-60 min | Phone filenames carry zero item info — only a human who knows the inventory can do this |
| 4 | **Add a contact email** to the site (BRAND-VOICE.md flags this as a launch blocker) | 5 min | Legal/trust requirement for a real storefront |
| 5 | **Set up Vercel** — connect repo, add env vars, point domain | 15 min | Needs the owner's Vercel account + DNS access |

#### 1B. Agent work (can happen now, in parallel):

| # | Task | Effort | Depends on |
|---|---|---|---|
| 1 | **Pull remaining Drive photos** — 25+ known IDs in `photo-inbox/HANDOFF.md`, plus unpaginated pages | ~30 min | Google Drive MCP connector (gateway blocks HTTP) |
| 2 | **Regenerate photo matcher** after new photos land | 5 min | Task 1 |
| 3 | **Run photo assignments** once owner provides pairings | 5 min per batch | Owner completing 1A.3 |
| 4 | **Verify real inventory loads** once sheet is shared | 2 min | Owner completing 1A.1 |
| 5 | **Add contact email component** to footer/about page | 15 min | Owner providing email in 1A.4 |

### Phase 2 — Ship the Storefront

Once Phase 1 gates are cleared:

| # | Task | Effort | Notes |
|---|---|---|---|
| 1 | **Deploy to Vercel** — configure `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `GOOGLE_SHEET_ID`, `NEXT_PUBLIC_SHOW_CROSS_PROMO`, `NEXT_PUBLIC_JAYLEEFIT_URL` | 20 min | Owner provides Stripe live keys + domain |
| 2 | **Switch Stripe to live mode** — update keys, verify webhook endpoint, test a real checkout flow | 30 min | Stripe account must be activated for payouts |
| 3 | **End-to-end smoke test** — browse catalog, filter, add to cart, checkout, verify webhook fires | 30 min | After deploy |
| 4 | **Push first real listings** — run `ebay-sync` with `--publish` for 5-10 items, generate Facebook/Vendoo exports | 1 hr | eBay developer credentials needed |
| 5 | **SEO + Open Graph** — add meta tags, OG images, sitemap | 30 min | After deploy |

### Phase 3 — Connect the Ecosystem

After the storefront is live and selling:

| # | Task | Effort | Priority |
|---|---|---|---|
| 1 | **Wire Metricool** to the content engine architecture | 2-4 hrs | High — analytics already confirmed live |
| 2 | **Create the Content Engine Airtable base** — Content Queue, Assets, Performance, AgentLog tables per ARCHITECTURE.md | 1-2 hrs | High — enables the whole pipeline |
| 3 | **Deploy the JayLeeFit coaching website** — `jayleefit-website/` is built; needs Airtable token, domain (jayleefit.com), and an end-to-end intake test | 1-2 hrs | High — this is the coaching business's front door |
| 4 | **Run the image-gen pilot** — 5-10 items through asset-pipeline Stage 2, cost-preview first | 1-2 hrs | Medium — only after real photos are assigned |
| 5 | **Wire Google Sheet writes** — either service account or move tracking to Airtable | 2-4 hrs | Medium — enables auto-marking items sold |
| 6 | **Activate the content pipeline** — schedule first batch through the agent crew | 2-4 hrs | Lower — needs Airtable base + video gen credits |

---

## Decision Points for the Owner

Before work starts, these choices shape what gets built:

1. **Deployment platform:** Vercel (recommended, Next.js native) vs. Railway vs. other?
2. **Domain:** What domain for Old Light? (e.g., `oldlightgoods.com`, `shopoldlight.com`)
3. **JayLeeFit website:** Deploy `jayleefit-website/` to jayleefit.com as-is, or add booking/payments first?
6. **eBay path:** The storefront has both the Vendoo-hub route (current direction) and a replayed `lib/ebay-sync` Sell API CLI. Keep one.
4. **Content engine priority:** Start building it now, or wait until storefront is live and selling?
5. **Image generation budget:** How much Higgsfield credit to spend on the pilot batch? (~1.25 credits per 1K product image via `recraft_v4_1`)

---

## GitHub Access Blocker

**Push access is currently down.** The Claude GitHub App needs to be installed or reconnected:

- **Install:** https://github.com/apps/claude/installations/select_target
- **Reconnect:** https://claude.ai/customize/connectors?auth_start=github&auth_start_force=1

There is 1 unpushed commit (`dd81b93` — GROK_HANDOFF.md) waiting to go up. Once access is restored, everything can flow.

---

## File Map (quick reference)

```
JayLeeFit-/
├── CLAUDE.md                    # Multi-project guide (read first)
├── GROK_HANDOFF.md              # Photo-to-SKU outlier task handoff
├── FINISHING_PLAN.md            # This file
├── README.md                    # JayLeeFit coaching data layer
├── airtable-schema.json         # Live Airtable base IDs
├── docs/                        # Coaching project docs (5 files)
│
├── storefront/                  # EHC / Old Light storefront
│   ├── app/                     # Next.js 16 routes (11 routes)
│   ├── components/              # React components (12 files)
│   ├── lib/
│   │   ├── products.ts          # Sheet CSV fetch + dual-layout parsing
│   │   ├── sample-products.ts   # 10 demo items (fallback)
│   │   ├── assign-photo.ts      # CLI: photo → SKU assignment
│   │   ├── build-image-manifest.ts
│   │   ├── build-inbox-index.ts
│   │   ├── product-images.generated.ts  # EMPTY — no photos assigned
│   │   ├── asset-pipeline/      # Image prompt engine (Stage 1 only)
│   │   ├── ebay-sync/           # Real eBay Sell API integration
│   │   ├── marketplace-export/  # Facebook + Vendoo listing generators
│   │   └── ops/                 # Health engine + system prompts
│   ├── photo-inbox/             # 68 photos, matcher handoff, index
│   ├── tools/                   # photo-matcher.html + builder
│   ├── public/products/         # EMPTY (.gitkeep) — the gap
│   ├── preview/                 # Self-contained HTML preview
│   ├── BRAND-VOICE.md           # "Care is the product"
│   └── README.md                # Full storefront docs
│
└── content-engine/              # Social content pipeline (design only)
    ├── ARCHITECTURE.md          # Full pipeline design (320 lines)
    ├── README.md                # Scoping doc
    └── lib/video/               # Prompt builders (pure functions)
```

---

## Persistence Protocol

For any agent picking this up:

1. **Check GitHub access first** — if push is blocked, flag it immediately
2. **Check `public/products/` contents** — if empty, the outlier task isn't done
3. **Check if the Google Sheet loads** — `curl` the CSV export URL; if it 403s, the owner hasn't shared it
4. **Don't context-switch** — the storefront launch is the priority until it ships
5. **Cost-gate everything** — preview before spending any generation credits
6. **Don't blend the three projects** — check which one a request belongs to before acting
