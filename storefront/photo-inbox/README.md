# Photo inbox — edited photos waiting on a SKU

Already-edited product photos pulled out of Google Drive. These are **not
raw** — they came out of Photoroom before that subscription lapsed, and
they're already at marketplace spec: subject cut out, pure white
background, square (mostly 2400×2400).

**They don't need background removal. Don't reprocess them.**

They sit here rather than in `public/products/` because nothing in a
phone filename (`IMG_2109-Photoroom.jpg`) says which inventory item it
is. That match is a human call.

This folder is deliberately **outside `public/`**, so nothing here is
served or bundled until it's been assigned to a SKU.

## Assigning a photo to an item

```bash
npx tsx lib/assign-photo.ts IMG_2109-Photoroom.jpg A1-MD-0003
```

That moves it to `public/products/A1-MD-0003/1.jpg` and regenerates the
manifest, so it shows up on the storefront immediately. Run it again for
the same SKU and it appends as `2.jpg`, `3.jpg`, and so on — first photo
assigned is the one used as the card/hero image, so lead with the best
full-garment shot.

Add `--copy` to leave the original in the inbox.

## What's here

See **[INDEX.md](INDEX.md)** for the current file list with dimensions —
it's generated, so it stays accurate as the inbox grows:

```bash
npx tsx lib/build-inbox-index.ts
```

Anything flagged **not square** wants a crop before assignment: the
storefront's product grid is 4:5 and marketplaces prefer square.

**More still to come.** This is a partial pull of a larger Drive library.
Every image is one connector call (the environment's proxy blocks direct
Drive downloads), so it comes across in batches rather than all at once.
Two things to know about the remainder:

- **Roughly half of it is exact duplicates.** Nearly every file appears
  twice at identical byte size. Deduplication here is by SHA-256 of the
  file contents, so byte-identical copies are dropped on the way in
  rather than landing as `foo (1).jpg`.
- **Some files aren't product photos.** Several are Drive-tagged
  "Screenshot" (`IMG_7090/7091/7092.PNG`) and look like eBay comps, not
  inventory. Those should be skipped, not assigned.

## Why detail shots matter here

The measurement and care-tag shots are worth keeping and assigning, not
discarding in favour of pretty hero shots only. `BRAND-VOICE.md`'s first
principle is "say the flaw first" — a ruler across the inseam and a
readable care tag are that principle as photography, and they're what
stops a buyer opening the box surprised.
