# Grok Handoff — The Outlier Task

**Written for Grok (or any agent picking this up).
Read everything below before doing anything.**

## What this is

This is the one task that has survived every session and every agent
handoff since this repo started. Four sessions, two agent handoffs
(Claude → Manus → Grok), and it's still not done. The technical pipeline
is fully built. The actual work — matching 68 real photos to real
inventory SKUs — has never been completed.

Every storefront product currently renders **"Photo coming soon"** because
`storefront/public/products/` doesn't exist. Zero photos are assigned.

## Which project

This is **EHC** — the secondhand apparel resale storefront in
`storefront/`. Not the JayLeeFit fitness coaching data layer, not
`content-engine/`. See root `CLAUDE.md` for the full breakdown.

**Branch:** `claude/jaylee-fit-website-build-aor3la`

## The pipeline (fully built, never used to completion)

```
Google Drive photos
       ↓  (MCP connector — gateway blocks direct HTTP to Google)
storefront/photo-inbox/           ← 68 photos sitting here right now
       ↓  (human visual matching using tools/photo-matcher.html)
npx tsx lib/assign-photo.ts <file> <SKU>
       ↓
storefront/public/products/<SKU>/1.jpg, 2.jpg, ...
       ↓  (auto-rebuilds image manifest)
Storefront renders real product images
```

Every piece of this pipeline exists and works. The gap is step 2: a human
looking at each photo and deciding which inventory item it belongs to.

## What's already here

### 68 photos in `storefront/photo-inbox/`

Already background-removed by Photoroom (before that subscription lapsed).
Pure white backgrounds, marketplace-ready. These are real product photos of
real secondhand clothing items.

### Visual matcher tool — `storefront/tools/`

- `build-photo-matcher.py` — generates `photo-matcher.html`
- `photo-matcher.html` — a self-contained visual matching UI

The matcher shows each inbox photo alongside searchable live inventory
from the EHC Inventory Log. Click an item to pair them. Emits a
`filename → SKU` list. Progress persists to localStorage so the matching
pass can happen across multiple sittings.

**To regenerate the matcher** (if new photos are added):
```bash
cd storefront && python3 tools/build-photo-matcher.py
```

### Assignment script — `storefront/lib/assign-photo.ts`

```bash
cd storefront
npx tsx lib/assign-photo.ts IMG_2109-Photoroom.jpg A1-MD-0003
```

Moves the file from `photo-inbox/` to `public/products/<SKU>/<next-index>.jpg`
and auto-rebuilds the image manifest. Appends on repeat runs so multiple
photos per item build up in order. Pass `--copy` to leave the inbox file
in place.

### More photos still in Google Drive (not yet pulled)

25+ known file IDs listed in `storefront/photo-inbox/HANDOFF.md`, plus
unpaginated results beyond page 1 of the Drive search. The full search
query and Drive folder IDs are documented there too.

**Network constraint:** The environment's gateway blocks all Google hosts
(drive.google.com, lh3.googleusercontent.com, etc. — all return 403).
The Google Drive MCP connector is the only route. See
`storefront/photo-inbox/HANDOFF.md` for the exact download + decode
workflow.

## What Grok can do autonomously

### 1. Pull remaining photos from Google Drive

Follow the protocol in `storefront/photo-inbox/HANDOFF.md` exactly:

1. Use `ToolSearch` to find `download_file_content` (the Drive MCP tool
   prefix changes between sessions)
2. Download each file by its Drive ID (25 known IDs listed in HANDOFF.md)
3. Paginate the Drive search to find any beyond page 1
4. Run the base64 decoder script (in HANDOFF.md) to decode downloads into
   `photo-inbox/`, deduplicated by SHA-256
5. Rebuild the index: `npx tsx lib/build-inbox-index.ts`
6. Verify the build still passes: `npx tsc --noEmit && npx next build`
7. Commit and push

### 2. Regenerate the visual matcher

After adding new photos to the inbox:
```bash
cd storefront && python3 tools/build-photo-matcher.py
```
Commit the updated `photo-matcher.html`.

### 3. Facilitate the matching pass

The actual photo-to-SKU matching requires the **owner** (the human) to:
- Open `storefront/tools/photo-matcher.html` in a browser
- Look at each photo and match it to the correct inventory item
- Record the pairings

Then either the owner or Grok runs `assign-photo.ts` for each pairing.

**Do NOT guess photo-to-SKU mappings.** Nothing in a phone filename like
`IMG_2109-Photoroom.jpg` tells you which garment it is. A wrong mapping
ships the wrong picture to a real buyer. This is explicitly called out in
`CLAUDE.md` and `storefront/photo-inbox/HANDOFF.md`.

### 4. Run assignments once pairings are known

When the owner provides `filename → SKU` pairs:
```bash
cd storefront
npx tsx lib/assign-photo.ts IMG_XXXX-Photoroom.jpg A1-MD-XXXX
# repeat for each pairing
```

Then verify: `npx tsc --noEmit && npx next build`

## What only the owner can do

1. **The visual matching pass** — look at real photos, identify which
   clothing item each one shows, match to the correct SKU.

2. **Fix Google Sheet permissions** — `EHC Inventory Log`
   (`1-UcTy4Cr_NPK622SPRXob7LfpHFEw5874mv9y5E90Ys`) still has
   owner-only access. The storefront needs "Anyone with the link →
   Viewer" to read inventory. Until then, it silently falls back to 10
   demo items from `lib/sample-products.ts`.

3. **Fix Drive folder permissions** — `EHC-Background-Edited-Images` is
   shared as "anyone → Writer" (should be Viewer to prevent accidental
   deletion).

## What NOT to do

- **Do not assign photos to SKUs automatically.** Phone filenames carry
  zero information about which item they show.
- **Do not write to Google Sheets.** No write credential exists, and the
  Poshmark Command Sheet is maintained by Codex — writing risks conflicts.
- **Do not spend generation credits.** These photos are already edited.
  No Adobe, no Higgsfield, no background removal. The job is moving bytes.
- **Do not push to any branch** other than
  `claude/jaylee-fit-website-build-aor3la`.

## Why this keeps stalling

The technical pipeline is done. The blocker is a human-in-the-loop step:
looking at 68+ photos of secondhand clothing and matching each to the
right inventory row. No agent can safely do this — the items are real,
the buyers are real, and a wrong photo-to-SKU mapping is a trust failure.

The owner needs to:
1. Open `tools/photo-matcher.html` in their browser
2. Spend ~30-60 minutes matching photos to items
3. Hand the pairings to an agent (or run `assign-photo.ts` themselves)

That's it. That's the entire remaining blocker for getting real product
images on the storefront.

## Persistence directive

**Stay on this until it's resolved.** When picking up work, check:
1. Are there still photos in `photo-inbox/` with no corresponding
   directory in `public/products/`? If yes, the task isn't done.
2. Are there still Drive photos not yet pulled? Pull them.
3. Has the owner done the matching pass? If not, prompt them.
4. Once pairings exist, run the assignments and verify the build.

Don't context-switch to other tasks until this pipeline is flowing.
