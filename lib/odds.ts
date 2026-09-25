export type OddsFormat = "american" | "multiplier";

export type Pick = {
  id: string;
  event_date: string;
  sport: string;
  matchup: string;
  platform: string;
  player: string | null;
  market: string;
  line: number | null;
  side: string;
  odds_format: OddsFormat;
  odds_value: number;
  parlay_id: string | null;
  legs_in_parlay: number;
  stake: number;
  potential_payout: number;
  result: "pending" | "win" | "loss" | "push";
  actual_payout: number | null;
  notes: string | null;
};

/** Implied win probability required to break even, given how the odds were priced. */
export function breakevenProbability(pick: Pick): number {
  if (pick.odds_format === "american") {
    const o = pick.odds_value;
    return o < 0 ? -o / (-o + 100) : 100 / (o + 100);
  }
  // Multiplier / power-play payout (e.g. Dabble, PrizePicks): odds_value is the
  // total payout multiplier for the whole slip, legs_in_parlay legs must all hit.
  const combinedBreakeven = 1 / pick.odds_value;
  return Math.pow(combinedBreakeven, 1 / pick.legs_in_parlay);
}

export function profitFor(pick: Pick): number {
  switch (pick.result) {
    case "win":
      return pick.potential_payout - pick.stake;
    case "loss":
      return -pick.stake;
    case "push":
      return 0;
    case "pending":
    default:
      return 0;
  }
}

export type Stats = {
  total: number;
  pending: number;
  wins: number;
  losses: number;
  pushes: number;
  graded: number;
  hitRate: number | null; // wins / (wins + losses), excludes pushes/pending
  avgBreakevenRequired: number | null; // average across graded picks, weighted equally
  edge: number | null; // hitRate - avgBreakevenRequired
  totalStaked: number;
  totalProfit: number;
  roi: number | null; // totalProfit / totalStaked, graded picks only
};

export function computeStats(picks: Pick[]): Stats {
  const graded = picks.filter((p) => p.result !== "pending");
  const wins = graded.filter((p) => p.result === "win").length;
  const losses = graded.filter((p) => p.result === "loss").length;
  const pushes = graded.filter((p) => p.result === "push").length;
  const decided = wins + losses;

  const hitRate = decided > 0 ? wins / decided : null;

  const breakevens = graded
    .filter((p) => p.result === "win" || p.result === "loss")
    .map(breakevenProbability);
  const avgBreakevenRequired =
    breakevens.length > 0
      ? breakevens.reduce((a, b) => a + b, 0) / breakevens.length
      : null;

  const edge =
    hitRate !== null && avgBreakevenRequired !== null
      ? hitRate - avgBreakevenRequired
      : null;

  const totalStaked = graded.reduce((sum, p) => sum + Number(p.stake), 0);
  const totalProfit = graded.reduce((sum, p) => sum + profitFor(p), 0);
  const roi = totalStaked > 0 ? totalProfit / totalStaked : null;

  return {
    total: picks.length,
    pending: picks.filter((p) => p.result === "pending").length,
    wins,
    losses,
    pushes,
    graded: graded.length,
    hitRate,
    avgBreakevenRequired,
    edge,
    totalStaked,
    totalProfit,
    roi,
  };
}

export function formatPercent(n: number | null, digits = 1): string {
  if (n === null || Number.isNaN(n)) return "—";
  return `${(n * 100).toFixed(digits)}%`;
}

export function formatMoney(n: number): string {
  const sign = n < 0 ? "-" : "";
  return `${sign}$${Math.abs(n).toFixed(2)}`;
}
