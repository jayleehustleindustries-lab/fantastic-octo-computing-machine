# Handoff — finishing the EHC photo ingest

Written for another Claude session (or a subagent) picking this up cold.
Read this before touching anything.

## First: which project is this?

This repo holds **three unrelated businesses** — see the root
`CLAUDE.md`. This task is **EHC**, the secondhand apparel resale
operation in `storefront/`. Not the JayLeeFit fitness data layer, not
`content-engine/`. Don't blend them.

Work happens on branch `claude/apparel-resale-storefront-jz63ws`, tracked
by **PR #5** (draft) against the repo's actual default branch
`claude/fitness-airtable-client-data-g1iot3` — **not `main`**.

## The one-line task

Pull the remaining already-edited product photos out of Google Drive into
`storefront/photo-inbox/`, deduplicated. That's it. Do not reprocess
them, do not generate anything, do not spend credits.

## Critical: these photos are already edited

They came out of Photoroom before that subscription lapsed. Verified by
opening two directly: `IMG_2109-Photoroom.jpg` (2400×2400) and
`IMG_4094-Photoroom.jpeg` (1600×1600). Both are already subject-cut-out
on pure white at marketplace spec.

**Do not run background removal on them.** No Adobe, no Higgsfield, no
credits. The whole job is moving bytes.

## How to pull a file (the only working method)

The environment's network policy **blocks every Google host at the
gateway** — `drive.google.com`, `lh3.googleusercontent.com`,
`drive.usercontent.google.com` all return 403 to CONNECT. curl/wget will
not work. Verified, not assumed.

The Google Drive MCP connector is the only route:

```
mcp__<drive-server>__download_file_content(fileId: "<id>")
```

The Drive server's tool prefix is a UUID that changes between sessions —
find it with ToolSearch for `download_file_content`.

Each call returns ~500KB of base64, which overflows to a file under
`/root/.claude/projects/<project>/<session>/tool-results/`. That's
expected and fine — you never read it into context. Decode the whole
directory at once afterwards.

## Decoding into the inbox

This is idempotent and deduplicates by content hash. Run it after any
batch of downloads:

```python
import json, base64, glob, hashlib, os
src = glob.glob('/root/.claude/projects/*/*/tool-results/*download_file_content*.txt')
out = 'photo-inbox'
seen = {}
for f in os.listdir(out):                     # seed from what's already committed
    p = os.path.join(out, f)
    if os.path.isfile(p) and not f.endswith('.md'):
        seen[hashlib.sha256(open(p,'rb').read()).hexdigest()] = f
for p in sorted(src):
    try: d = json.load(open(p))
    except Exception: continue
    if 'content' not in d or not str(d.get('mimeType','')).startswith('image/'): continue
    raw = base64.b64decode(d['content']); h = hashlib.sha256(raw).hexdigest()
    if h in seen: continue
    seen[h] = d['title']
    open(os.path.join(out, d['title']), 'wb').write(raw)
```

**Deduplicate by SHA-256 of contents, never by filename.** Roughly half
the Drive library is byte-identical twins uploaded twice under the same
name. Name-based dedupe produces `foo (1).jpg` and you end up assigning
the same photo to two different items.

Then regenerate the index and commit:

```bash
npx tsx lib/build-inbox-index.ts
npx tsc --noEmit && npx next build     # both must stay clean
```

## Drive locations

| Folder | ID |
|---|---|
| `EHC-Image-Import-Folder` | `1AmYNK5rc-AEVBG6Bdj_AZ43WITtvVvmy` |
| `EHC-Background-Edited-Images` | `1GnI3SG6IsNs_5_s31EGEi4tBYqkZyt6y` |
| `Pictures` | `1zmoPPxl5cW5BJE6FM8FmiHF3_JsHYAr9` |

Search query used to enumerate them:

```
(parentId = '1GnI3SG6IsNs_5_s31EGEi4tBYqkZyt6y' or parentId = '1AmYNK5rc-AEVBG6Bdj_AZ43WITtvVvmy' or parentId = '1zmoPPxl5cW5BJE6FM8FmiHF3_JsHYAr9') and mimeType contains 'image/'
```

Pass `excludeContentSnippets: true`. Results paginate — page 1 returns
100 files and there are further pages not yet enumerated, so the total
remaining is **unknown**. Don't state a count you haven't verified.

## Known-remaining file IDs (from page 1, not yet pulled)

| File | ID |
|---|---|
| IMG_0484-Photoroom.jpg | `1lHAgWEoBvVgq1-_we3si66OdxGrtdiuP` |
| IMG_0485-Photoroom.jpg | `1ks5GQ_9xaG-07IEm8wmLGj5XhWyfoAC6` |
| IMG_0486-Photoroom.jpg | `1Kzx1S43VXaDgyN7fkpDtyQ52oVeRTEPe` |
| IMG_0493-Photoroom.jpg | `1jDGk7O2dI-bVR-EGapQS9Srv4WwIAR2_` |
| IMG_0495-Photoroom.jpg | `1c2y1TIeiqV_PudcFMZReQPcHpiiYxYsX` |
| IMG_2111-Photoroom.jpg | `1bLl70UHPc1DZnt0KYq6SF6LSPt7jWaEO` |
| IMG_2118-Photoroom.jpg | `1WPvjo_dB7NAosD1N-pkJgHytvCgGN82b` |
| IMG_2795-Photoroom.jpg | `1vjta6X20xlPgFhSw-ZFTdNLLibyFPdfN` |
| IMG_2797-Photoroom.jpg | `1v1WPq1OXcJCXXeW6BPWMc-KQwqIIud1f` |
| IMG_2808-Photoroom.jpg | `1dkV-_s5IHrE_87OPMin3WwYuBDz86ZO8` |
| IMG_4070-Photoroom.jpeg | `1ix5b0RLWf9asc7Lg9xvdYNQey8F4wbj0` |
| IMG_4072-Photoroom.jpeg | `1zMg1kdoVU6AbYbLCm03W3b2Z2yS4TNGX` |
| IMG_4073-Photoroom.jpeg | `1ZyOVlCzwKtWq8hE_FXusfwoOpVEJpXKX` |
| IMG_4075-Photoroom.jpeg | `1viKoXxMSuIp7m3Yklj-NLA3AvXn2ZCkF` |
| IMG_4076-Photoroom.jpeg | `18g_2P-xZ4iFx6jE5Wi6Xv2hwzf3LHgyt` |
| IMG_4079-Photoroom.jpeg | `11cHxFKqxAUY7eU3dDrCd-gEamRmWxYPT` |
| IMG_4080-Photoroom.jpeg | `1v_fDOFWyiJNN0y6GCAGF_tgpwtniHKWK` |
| IMG_4081-Photoroom.jpeg | `1Q5lgrA3-Gzpz2M6tL1U_8pfjcu74mtzn` |
| IMG_4083-Photoroom.jpeg | `1ifwKb1Lq9MJH0EBuWDy2BHIpeZq12y2a` |
| IMG_4085-Photoroom.jpeg | `1mSe1wtPZAlC46VQZM1x8NBqH7I-3RaTX` |
| IMG_4086-Photoroom.jpeg | `1UvDYSqobtPtZvEATlo6e9zZm4R_tdbAJ` |
| IMG_4089-Photoroom.jpeg | `1ktzKNttPbht51KI97Pogj_fQYzBubJwr` |
| IMG_4092-Photoroom.jpeg | `172E1BqvEOnqcmHDsAopItjjhom41wp16` |
| IMG_4095-Photoroom.jpeg | `1FYD9lvJ5BbdTeNtpiqQoyIcDrd-on8RJ` |
| IMG_4096-Photoroom.jpeg | `1h0VkFwmaTEJsVfjCbuI3OmmBh7-Nuptz` |

## Things to skip

- Files Drive tags `"Screenshot"` — `IMG_7090/7091/7092.PNG` and similar.
  These look like eBay comps, not inventory.
- Anything already in `photo-inbox/` (the decoder handles this).

## Do NOT do these

- **Do not assign photos to SKUs.** Nothing in a phone filename says
  which item it is. A wrong photo→SKU mapping ships the wrong picture to
  a real buyer, which is the exact trust failure `storefront/BRAND-VOICE.md`
  exists to prevent. The owner does this step with
  `npx tsx lib/assign-photo.ts <file> <SKU>`.
- **Do not write to the Google Sheets.** There's no write access, and
  `Poshmark Agentic Inventory Command Sheet` is maintained by another
  agent (Codex) — writing there risks a conflict.
- **Do not spend generation credits.** Nothing here needs generating.
- **Do not push to any branch** other than
  `claude/apparel-resale-storefront-jz63ws`.

## Open blockers the owner has to clear (not you)

1. `EHC Inventory Log` (`1-UcTy4Cr_NPK622SPRXob7LfpHFEw5874mv9y5E90Ys`)
   has **owner-only permissions**. The storefront reads it anonymously via
   the CSV-export endpoint, so it can't, and silently falls back to the
   10 demo items in `lib/sample-products.ts`. Needs
   *Anyone with the link → Viewer*.
2. `EHC-Background-Edited-Images` is shared **anyone → Writer**. Anyone
   with the link can delete the photos. Should be Viewer.
3. The Adobe connector is disconnected and Higgsfield's session expired.
   Neither is needed for this task.
