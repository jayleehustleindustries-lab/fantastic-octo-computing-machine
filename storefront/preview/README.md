# Old Light — shareable storefront preview

`old-light-preview.html` is the whole storefront as **one self-contained
file**. No server, no build, no network: open it in a browser, or send it
to someone who needs to see the shop before it's deployed.

It exists because the real Next.js site can't be shown to anyone until
it's hosted, and the two blockers on hosting (sheet sharing, photo
assignment) are outside the code. This is how the brand gets reviewed in
the meantime.

## What's real in it

Every one of the **78 products is a real row** from the live EHC
inventory database — real SKUs, prices, brands, sizes, grades and
descriptions. Not mock data.

The brand tokens in `src/index.css` are copied verbatim from
`app/globals.css`, and `phaseForScore()` in `src/App.tsx` uses the same
thresholds as `lib/products.ts`, so the preview and the real site can't
quietly drift apart.

## What's deliberately not real

- **Every tile shows a placeholder**, because no photo is matched to a
  SKU yet. The preview says so on the page rather than dressing itself
  up with stock imagery — `../BRAND-VOICE.md` makes "say the flaw first"
  the brand's first principle, and a demo that oversells its own
  readiness breaks that before a buyer ever arrives.
- **No checkout.** The real storefront runs Stripe and re-prices every
  cart item server-side; none of that belongs in a static file.
- **Fonts are system stacks.** The real site loads Cormorant Garamond,
  Libre Franklin and Space Mono; a published artifact runs under a CSP
  that blocks external font hosts, so the closest local serif/sans/mono
  are used instead. Expect the type to look slightly heavier here than
  on the deployed site.

## Regenerating it

Product data comes from the inventory database, exported to
`src/products.json` as an array of
`{sku,name,brand,gender,type,size,color,condition,score,price,desc,status,available,location}`.

To rebuild after the data or copy changes:

```bash
bash <skills>/web-artifacts-builder/scripts/init-artifact.sh old-light
cd old-light
cp <repo>/storefront/preview/src/*.{tsx,css,json} src/
cp <repo>/storefront/preview/index.html .
bash <skills>/web-artifacts-builder/scripts/bundle-artifact.sh
```

Then copy `bundle.html` back to `preview/old-light-preview.html`.

## Keeping it honest as things land

The status panel at the bottom reports live counts — items, catalog
value, photos matched, items missing measurements. **Those numbers are
the point.** When photos start getting assigned, regenerate so "0 photos
matched" stops being true. A preview that keeps claiming stale numbers
is worse than no preview.
