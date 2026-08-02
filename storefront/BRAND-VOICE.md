# Old Light — brand voice

The design system lives in `README.md`. This is the other half: what we
say, why, and the lines we don't cross. If a piece of copy anywhere —
site, eBay listing, Facebook post, shipping email, caption — can't pass
the tests below, rewrite it.

## The thesis, in one sentence

**Care is the product.** Nobody needs another used hoodie; what's
actually scarce in resale is a seller who looked at the thing properly
before selling it to you. So our job is not to make you hurry. It's to
make you sure.

## Why care is the strategy, not a nicety

Every competitor in secondhand sells the same underlying good: someone
else's clothes. The differentiators available are price, selection, and
trust. We can't win selection — we're one person and a thrift run, not a
warehouse. We can compete on price, but so can anyone, and racing there
ends with liquidation-pallet margins.

Trust is the only one that compounds. In a market where the buyer's real
fear is *"what won't they tell me about this?"*, the seller who names the
flaw first wins the repeat customer. That's not sentiment — it's the one
moat a one-person operation can actually build.

Which means care can't be an adjective we apply to ourselves. It has to
show up as **things we do that cost us something**: rounding grades down,
naming flaws in the listing, carrying the risk when we call it wrong.
Claimed care is marketing. Demonstrated care is the brand.

## The metaphor, corrected

Old light has been doing the wrong job in our copy.

We've been using it to mean **transience** — "the light moves on, hurry."
But that's not what old light is. Old light is the opposite: it's light
that *survived*. It crossed an unreasonable distance, took years doing
it, and still arrived lit. The emotional truth of old light isn't
vanishing. It's **persistence**.

That single flip changes the whole register:

| | Scarcity read | Care read |
|---|---|---|
| What the metaphor means | it's about to disappear | it already lasted |
| What we're asking for | hurry | trust |
| What the customer feels | pressure | permission |
| Line it produces | "once it's gone, it's gone" | "it made it this far — it'll go further with you" |

Same metaphor. Same aesthetic. Opposite pressure. We keep the celestial
world entirely; we stop using it as a countdown clock.

## Five principles, each with a test

**1. Say the flaw first.**
The wear, the pilling, the missing tag goes in the opening of a
description, not buried after the sell. A buyer who learns the flaw from
us trusts everything else we said. A buyer who finds it in the mail
believes nothing we say again.
*Test: could this listing embarrass us when the box gets opened?*

**2. Scarcity is a reason for disclosure, not a deadline.**
One-of-one is a true fact and we may state it — once, plainly. Its honest
purpose is *"there's no second one to swap it for, so here's everything
we know."* Its dishonest purpose is a whip. Stating it six times across a
page is the whip.
*Test: does this sentence help them decide, or just make them anxious?*

**3. Patience is our flex.**
Every other resale surface is engineered to rush. Telling someone to take
their time is the most distinctive thing we can do, and it costs us
almost nothing — we're not running a flash sale, we're selling one item
that nobody else has.
*Test: am I inviting a decision or forcing one?*

**4. We carry the risk, not the customer.**
Care lives in policy, not vocabulary. "We grade honestly" is a claim;
"if we get the grade wrong, that's ours to fix, not yours" is a cost we
absorb. Only the second one is worth printing.
*Test: does this sentence cost us anything if we mean it?*

**5. Plain over clever, when they conflict.**
The voice is warm, spare, a little literary — but the moment style makes
a fact fuzzier, the fact wins. Prices, conditions, measurements, and
policies are stated flatly. Save the poetry for the About page and the
marquee, where nobody's making a purchase decision off a metaphor.
*Test: would someone deciding whether to spend $40 find this clear?*

## The scarcity audit

What was live before this pass, and what replaced it:

| Surface | Before | After |
|---|---|---|
| Hero eyebrow | "Priced to move." | "Checked by hand." |
| Hero body | "Once it's gone, it's gone." | "…we'd rather you buy it knowing everything than buy it fast." |
| Home section | "Tonight's Shooting Stars" | "Brightest Tonight" (+ honest subline about what the sort means) |
| Product page | "Only 1 available — once the light moves on, it's gone." | "One of one — so everything we know about it is on this page, flaws included." |
| Product page color | `text-ember` (alarm) on in-stock items | `text-ash` (calm); ember reserved for genuine state changes like SOLD |
| Marquee | "Once it's gone, it's gone" / "graded by the moon, not a number" | "Close calls round down, never up" / "One price — no bidding war" |
| Cancel page | "don't sit on it too long" | "Take your time — we'd rather you were sure." |
| Footer | "authenticated by hand" | "checked by hand" (see unearned claims below) |

Net: seven pressure lines down to one factual statement of one-of-one,
and the round-down promise promoted from a code comment to the home page.

## Voice by surface

**Home / About** — the most latitude for the metaphor. Still ends on a
concrete commitment, never on a mood.

**Product pages** — closest to plain. Brand, name, price, grade, size,
flaws, then one calm sentence. The customer is deciding here; don't make
them decode.

**eBay / Facebook listings** (`lib/ebay-sync/`, `lib/marketplace-export/`)
— off-site, so brand voice yields to platform norms and searchability,
but principle 1 is non-negotiable: the flaw goes in the description on
every platform. The existing round-down condition mapping is the voice
working correctly in code; keep it that way if the mapping is ever
revisited.

**Policy pages** — flat, specific, no metaphor. This is where care is
proven, so ambiguity here is more expensive than anywhere else on the
site.

**Post-purchase** (success page, shipping mail) — the sale is done, so
there is zero reason for urgency language. Confirm, reassure, tell them
exactly what happens next.

## Words we use / words we don't

**Use:** checked, graded, measured, flaws, as-is, honestly, one price,
worn, kept, arrived, lasted, take your time.

**Don't use:** *authenticated* (a specific service we don't perform —
see below), *deadstock* / *NWT* unless literally true, *steal* / *snag* /
*cop*, countdown language ("hurry," "last chance," "before it's gone"),
manufactured hype ("insane," "crazy deal," "fire"), and any invented
original price to discount from.

## Three claims we must earn before we make them

Care means not shipping a promise we can't back yet. All three of these
are live gaps, not hypotheticals:

1. **Photos.** Any "photographed as-is / no filter hiding wear" claim is
   unbacked while every real item still renders "Photo coming soon."
   The home-page process step is worded around what's true today (flaws
   named in the description); the photo half of that promise goes live
   only when real photos are wired to real SKUs.

2. **"Authenticated."** The footer claimed pieces were "authenticated by
   hand." Authentication is a specific counterfeit-verification service.
   Unless that's genuinely being performed per item, the word is a
   liability on a brand whose entire pitch is honesty — changed to
   "checked by hand." Reinstate only if it becomes literally true.

3. **A way to reach us.** Shipping & Returns tells buyers to "email us"
   and the site gives no address anywhere. A care promise with no inbox
   behind it is the exact failure this document exists to prevent — add
   a real contact route before launch.
