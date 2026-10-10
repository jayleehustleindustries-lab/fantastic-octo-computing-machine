# Project Oklahoma: brief for Google research agents
As of 2026-10-10.

## 1. What this is
- A research model for WNBA player props: points, rebounds, assists, PRA and 3PM.
- It follows Bill Benter's method:
  1. Model each player's stat distribution.
  2. Blend with de-vigged market prices.
  3. Size stakes with fractional Kelly.
- It is used to choose small $5 Dabble pick'em slips (More/Less) on a bankroll of about $40.
- Nothing places bets automatically.

## 2. Where the model stands
- **Method:** Poisson GLM mean plus negative-binomial spread. Walk-forward backtest over 2021–2026. The leakage test passes.
- **Baseline:** beats the season-average baseline by 0.03–0.04 log-loss per prop, in every season.
- **Newest candidate:** adds "started last game" × playoffs. It beats the current model in 6 of 6 seasons on points and PRA, and removes about 93% of the playoff bench over-projection. It passed its gate but is not yet reviewed or in production.
- **Calibration:** raw probabilities are overconfident (slope 0.82–0.95). Calibration is applied to points only.
- **NOT proven:** any edge against real sportsbook or Dabble lines. We have no historical prop-odds data yet. This is the #1 gap.

## 3. What our first pass found (UNVERIFIED: search snippets only)
- Benter's edge came from blending his model with the public's odds, not from the model alone.
- Pros grade models by closing-line value (CLV). About 70–400 bets give a CLV signal, versus about 1,000–2,000 bets to judge by win/loss.
- Testing many variants against the same holdout inflates results.
- Dabble US break-even per leg: 2-pick 3x needs 57.7%, 3-pick 6x 55.0%, 4-pick 10x 56.2%, 5-pick 20x 54.9%. A -110 sportsbook bet needs 52.4%.
- On Dabble Australia, a push is not a refund. The US rule is unconfirmed.
- A $5 slip on about $40 is roughly 3x full Kelly, so the bust risk is high.
- Dabble's terms ban automated entry and scraping.
- Small modelers rarely win on news speed. The defensible edge is modelling how minutes and usage shift between players.
- The Odds API has player-prop history from May 2023. Estimated cost: $120–250.

## 4. Rules
- Use public, official or licensed data only. No scraping against a site's terms, no private social media, no insider or non-public information.
- Do not buy or sign up for anything paid. Report prices; the owner decides.
- Back every claim with: URL, publisher, date, and a short direct quote. Mark it "verified" only if you opened the page and the quote is on it.
- Write "not found" instead of guessing.

## 5. Legwork, in priority order
- **T1. Verify our sources.** Open the URLs in Appendix A. For each claim it backs, confirm or reject it. Output: a sheet with columns URL | claim | verified Y/N | quote | page date.
- **T2. Historical WNBA prop odds.** Which providers sell timestamped historical WNBA player-prop lines, including closing lines? Cover points, rebounds, assists, PRA and 3PM. For each: start date, books covered, price, and whether a free sample exists. Candidates: The Odds API, SportsDataIO, OddsJam, Unabated, SportsGameOdds, BettingPros, Pinnacle. Output: a comparison table.
- **T3. Dabble US rules,** from Dabble's own help centre and terms. We need:
  - The payout table for 2–8 picks.
  - Power vs flex play.
  - How pushes, voids and DNPs settle.
  - Line-change rules and state availability.
  - The automation clause.
  - The date you checked.
- **T4. Benter primary source.** Benter (1994), "Computer Based Horse Race Handicapping and Wagering Systems: A Report". We need:
  - The exact model-vs-public blending formula.
  - How the weights were fit.
  - The Kelly fraction used.
  - Sample sizes.
  - Also check Bolton & Chapman (1986).
- **T5. Prop market efficiency.** Find evidence on NBA/WNBA player-prop pricing errors, especially pick'em apps (PrizePicks, Underdog, Dabble) versus sharp books. Which prop types are softest? How fast do lines move after injury news?
- **T6. WNBA availability data.** The 2025–26 official injury-report rules and timing, when starting lineups become public, and free official sources for both.
- **T7. Validation.** Accepted sample sizes for CLV versus results. Ways to correct for testing many variants, such as the deflated Sharpe ratio, White's reality check, and holdout discipline.

## 6. Question the final report must answer
Is a Benter-style WNBA player-prop model, used for small Dabble pick'em slips, a real path to an edge? What must change (data, model, staking or venue) to get there?

## 7. Return format
One section per task, each with:
- A 3-line summary.
- A source table (URL | publisher | date | quote | verified).
- Open questions.

Keep each claim next to its source so NotebookLM can cite it.

Appendix A: sources (from `handoff/sources.txt`)

