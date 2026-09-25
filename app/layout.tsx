import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Vig Tracker",
  description: "Personal betting pick tracker — hit rate vs. breakeven, over time.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
