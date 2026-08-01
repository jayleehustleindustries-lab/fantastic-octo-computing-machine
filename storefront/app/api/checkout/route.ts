import { NextResponse } from "next/server";
import { getStripe } from "@/lib/stripe";
import { getProducts } from "@/lib/products";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const skus: unknown = body?.skus;

  if (!Array.isArray(skus) || skus.length === 0) {
    return NextResponse.json({ error: "Cart is empty." }, { status: 400 });
  }

  // Re-price against live inventory server-side — never trust the client's
  // cart for price or availability.
  const products = await getProducts();
  const lineItems = [];
  const unavailable: string[] = [];

  for (const sku of skus) {
    const product = products.find((p) => p.sku === sku);
    if (!product || !product.inStock) {
      unavailable.push(String(sku));
      continue;
    }
    lineItems.push({
      quantity: 1,
      price_data: {
        currency: "usd",
        unit_amount: Math.round(product.price * 100),
        product_data: {
          name: `${product.brand ? `${product.brand} — ` : ""}${product.name}`,
          description: `Size ${product.size} · ${product.condition} · SKU ${product.sku}`,
          images: product.images.slice(0, 1),
        },
      },
    });
  }

  if (unavailable.length > 0) {
    return NextResponse.json(
      { error: "Some items already sold or unavailable.", unavailable },
      { status: 409 }
    );
  }

  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || new URL(request.url).origin;

  try {
    const stripe = getStripe();
    const session = await stripe.checkout.sessions.create({
      mode: "payment",
      line_items: lineItems,
      success_url: `${siteUrl}/checkout/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${siteUrl}/checkout/cancel`,
      shipping_address_collection: { allowed_countries: ["US", "CA"] },
      // Flat rate until real carrier rates are wired up (e.g. via Shippo) —
      // better than quoting $0 shipping on physical one-off items.
      shipping_options: [
        {
          shipping_rate_data: {
            type: "fixed_amount",
            fixed_amount: { amount: 699, currency: "usd" },
            display_name: "Standard shipping (5-7 business days)",
          },
        },
      ],
    });

    return NextResponse.json({ url: session.url });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Checkout failed.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
