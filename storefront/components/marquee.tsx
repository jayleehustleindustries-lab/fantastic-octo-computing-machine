/**
 * Runs on every page, so this is the brand's most repeated statement —
 * it says what we do for the buyer, not what they stand to lose by
 * waiting. See BRAND-VOICE.md.
 */
const DEFAULT_ITEMS = [
  "EVERY PIECE ALREADY HAS A PAST",
  "GRADED BEFORE IT'S PRICED",
  "CLOSE CALLS ROUND DOWN, NEVER UP",
  "MEN'S & WOMEN'S",
  "ONE PRICE — NO BIDDING WAR",
];

export default function Marquee({ items = DEFAULT_ITEMS }: { items?: string[] }) {
  const track = [...items, ...items];

  return (
    <div className="overflow-hidden border-y border-line bg-gold text-void">
      <div className="marquee-track flex w-max whitespace-nowrap py-2">
        {track.map((item, i) => (
          <span
            key={i}
            className="mx-4 font-mono text-xs font-bold tracking-widest uppercase"
          >
            {item} <span className="mx-4">{"//"}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
