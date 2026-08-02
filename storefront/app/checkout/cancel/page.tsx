import Link from "next/link";

export default function CheckoutCancelPage() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center px-4 py-24 text-center sm:px-6">
      <p className="font-mono text-xs uppercase tracking-widest text-ember">Checkout canceled</p>
      <h1 className="mt-4 font-display text-4xl font-semibold tracking-wide">STILL IN YOUR CART.</h1>
      <p className="mt-4 max-w-md font-sans text-sm text-ash">
        Nothing was charged, and your cart is still saved. Take the time you need —
        we&apos;d rather you were sure about a piece than quick about it.
      </p>
      <Link
        href="/shop"
        className="mt-8 bg-gold px-6 py-3 font-mono text-xs font-bold uppercase tracking-widest text-void hover:opacity-90"
      >
        Back To Shop
      </Link>
    </div>
  );
}
