# ATP Shanghai Masters 1000 - Sunday Oct 11, 2026 - model report

Generated 2026-10-11 ~13:35 UTC. Re-runnable: `sim.py`, `calib_sigma.py`, `run_atp.py`, `tour_ref.py`, `gen_report.py` in this folder (`results.json`, `tour_ref.json` are the outputs). No sportsbook/app was logged into or scraped; only public search snippets (page fetches are blocked by the proxy, so every number below comes from a search snippet or from the model).

## 0. Read this first (timing and data-quality flags)

1. **Timing problem.** Shanghai is UTC+8. The Oct 11 (China-date) sessions are listed by P1 Travel as a day session at 12:30 and an evening session at 18:30 local = **04:30 UTC and 10:30 UTC** ([P1 Travel](https://www.p1travel.com/fr/tennis/atp-world-tours/atp-shanghai-masters-11-october-day-session)). At 13:00 UTC it is already 21:00 in Shanghai, so most or all of the Oct 11 China-date matches below are probably **finished or in their last match**. Exact per-match start times were **not found** (Bleacher Nation lists 'TBA'). Aggregators also disagree on dates: wincomparator and ats.io label these matches 11/10/2026, Kalshi shows De Minaur-Sakamoto at 'Sunday Oct 11, 12:00am EDT' (= 04:00 UTC), and a ran.de preview lists Zverev-Halys as 'Sunday 11 / Monday 12 October, ca. 6:30' ([ran.de](https://ran.joyn.de/sports/tennis/atp/alexander-zverev-im-sechzehntelfinale-von-shanghai-hier-laeuft-das-match-gegen-quentin-halys-live-im-tv-stream-ticker-198739)). So some of these could still be on the China-date Oct 12 card (starting 04:30 UTC Oct 12 = 11:30 PM US Central tonight). **Treat every price below as a stale pre-match snapshot and re-check the live order of play before betting anything.**
2. **No other ATP-level event today.** The next ATP events are Almaty (Oct 19-25) and Brussels/Lyon (Oct 19-25), then Basel/Vienna, Stockholm Nov 8-14 ([Too Many Rackets](https://toomanyrackets.com/2026-atp-tournament-schedule/), [Sports Digest](https://sportsdigest.in/2026-atp-tour-calendar-list-events/171916/amp/)). Sinner withdrew from Shanghai ([EWN](https://www.ewn.co.za/2026/10/03/world-no1-sinner-pulls-out-of-shanghai-masters-to-delay-return)); Djokovic lost to Hurkacz 6-4 6-3 on Oct 9 ([KSL](https://www.ksl.com/article/51634429/tennis-hurkacz-dumps-djokovic-out-of-shanghai-masters-to-reach-third-round)).
3. **Serve/return stats were NOT found in snippets** for these players (no tennis-abstract/ATP serve pages reachable). The hold%/break% profiles I feed the simulator are **my assumptions from general knowledge** (labelled below). They only shape tiebreak/3-set structure and one of the inputs to `p_model`; win probabilities are anchored to market + third-party model numbers.
4. **Odds source is thin.** Moneyline decimals come from wincomparator's preview pages (book unspecified, ~5% two-way overround); Kalshi gave one cross-check. bet365's real prices were not accessible. Totals lines were found for only 3 of 7 matches.
5. **No outcome data was reachable**, so the model cannot be backtested for Brier/log-loss. Validation below is internal-consistency only.

## 1. Slate (all hard court, outdoor, Qizhong Forest Sports City Arena; Round of 32 = 'third round' in the 96-draw)

Source for the 5-match list: [Bleacher Nation schedule](https://www.bleachernation.com/how-to-watch/2026/10/09/rolex-shanghai-masters-schedule-sunday-october-11-matchups-tv-live-stream-info/); Khachanov-Mannarino and Hurkacz-Zhou from [wincomparator](https://www.wincomparator.com/predictions/karen-khachanov-adrian-mannarino-8884860/) / [wincomparator](https://www.wincomparator.com/predictions/hurkacz-h-pol-yi-miao-zhou-8884945/). There may be an 8th match I could not find.

| Match | Round | Time (UTC) | ML decimal (fav / dog) | American | No-vig fav | Total-games line found |
|---|---|---|---|---|---|---|
| Zverev v Halys | R32 | TBD (sessions ~04:30 / ~10:30) | 1.17 / 5.00 | -588 / +400 | 81.0% | 20.5 (Stats Zone tip 'Over 20.5 games' (book/price not stated)) |
| Shelton v Gea | R32 | TBD (sessions ~04:30 / ~10:30) | 1.36 / 3.20 | -278 / +220 | 70.2% | not found (ats.io model projects 2-0, 23 games) |
| De Minaur v Sakamoto | R32 | TBD (sessions ~04:30 / ~10:30) | 1.29 / 3.75 | -345 / +275 | 71.2% | not found (MediaPronos: De Minaur -3 games) |
| Tiafoe v Davidovich Fokina | R32 | TBD (sessions ~04:30 / ~10:30) | 1.73 / 2.14 | -137 / +114 | 55.3% | not found |
| Mensik v F. Cerundolo | R32 | TBD (sessions ~04:30 / ~10:30) | 1.62 / 2.30 | -161 / +130 | 58.7% | sets market: Over 2.5 sets +110 (Sportytrader pick, Caesars) |
| Khachanov v Mannarino | R32 | TBD (sessions ~04:30 / ~10:30) | 1.30 / 3.50 | -333 / +250 | 72.9% | 22.5 (wincomparator o/u 22.5 (book unspecified); ats.io projects 20 games, UNDER) |
| Hurkacz v Zhou Yi | R32 | TBD (sessions ~04:30 / ~10:30) | 1.11 / 6.50 | -909 / +550 | 85.4% | 21.5 (ats.io o/u 21.5 (model-implied; projects 6-4 6-4 = 20 games, UNDER)) |

Market notes: De Minaur-Sakamoto no-vig is the average of Kalshi's 68% ([Kalshi](https://kalshi.com/markets/kxatpmatch/atp-tennis-match/kxatpmatch-26oct09desak)) and wincomparator's 1.29/3.75 (74.4%). Tiafoe-Davidovich Fokina: only Tiafoe's 1.73 was found; DF's price is **ASSUMED** from a 4.5% overround (2.14). Mensik is the market favourite (1.62 vs Cerundolo 2.30) even though wincomparator's own model picks Cerundolo (56.3%), Cerundolo leads the head-to-head (2-0 / 3-0 by source) and beat him 6-3 6-3 last week in Beijing ([Sportytrader](https://www.sportytrader.com/us/picks/francisco-cerundolo-jakub-mensik-378060/)). Shelton-Gea: wincomparator's odds (1.36 / 3.20) look short for a rank-8 vs rank-82 match (Elo-based ~82-85%) so the book price may be stale or soft.

## 2. Method

- **Point model:** each player has an iid probability of winning a point on serve; games use the exact hold formula, tiebreaks are simulated point-by-point (1-2-2-2 serve pattern), three sets with a final-set tiebreak (Masters rule), correct serve-order carry-over. 400,000 simulated matches per fixture.
- **Day-form noise:** each player draws a persistent per-match shift ~N(0, sigma) in point-win probability (+ for his serve, - for his opponent's). sigma = 0.0205 was chosen so a tour-like mix of favourites (fav win prob 52-88%, 80.5% average hold) gives a **38.3% three-set rate** (target 38%; the same mix gives mean 23.7 total games). Sensitivity run: sigma = 0.027 (about 35-36% three-set rate, matching Tennis Abstract's tour figure).
- **Assumed profiles (not sourced):** hold% / break% on hard - Zverev 86/23, Halys 80/17; Shelton 89/17, Gea 80/17; De Minaur 80/26, Sakamoto 85/13; Tiafoe 85/19, Davidovich Fokina 79/22; Mensik 87/17, F. Cerundolo 80/22; Khachanov 85/18, Mannarino 78/18; Hurkacz 89/14, Zhou Yi 78/14. Tour average assumed 80.5% hold. Sakamoto's high hold reflects 10.6 aces/match and 91.9% tournament hold in snippets ([Dimers](https://www.dimers.com/tennis/news/rei-sakamoto-vs-andrey-rublev-tennis-prediction-atp-shanghai-masters-2026-ac), [MediaPronos](https://mediapronos.com/?p=679855)).
- **Benter blend:** `p_blend = 0.3*p_model + 0.7*p_market_novig`. `p_model` = mean of (third-party model probabilities found, plus the assumed-profile simulator win probability `p_stats`). Edge = `p_blend * decimal - 1`; stake = quarter-Kelly of `edge/(decimal-1)`. The simulator is then re-calibrated so each match's win probability equals `p_blend` before totals are read off.
- **Totals:** market line treated as a 50/50 market, so `p_blend(over) = 0.3*P_model(over) + 0.35`; assumed -110 both sides (break-even 52.4%). Pick'em thresholds: 2-pick 57.7% -> raw model p >= 75.7%; 3-pick 55.0% -> p >= 66.7%; 4-pick 56.2%; 5-pick 54.9%.

## 3. Win probabilities, Benter blend and moneyline edges

| Fav v Dog | p_stats (assumed profiles) | third-party models | p_model | p_market (no-vig) | **p_blend fav** | Fav edge | Dog edge | Dog break-even price for 0% edge |
|---|---|---|---|---|---|---|---|---|
| Zverev v Halys | 75.8% | 83% | 79.4% | 81.0% | **80.5%** | -5.8% | -2.7% | 5.14 (+414) |
| Shelton v Gea | 71.8% | 84% | 77.9% | 70.2% | **72.5%** | -1.4% | -12.0% | 3.64 (+264) |
| De Minaur v Sakamoto | 67.3% | 60% | 63.6% | 71.2% | **68.9%** | -11.1% | +16.5% | 3.22 (+222) |
| Tiafoe v Davidovich Fokina | 57.8% | 56%, 62%, 50% | 56.6% | 55.3% | **55.7%** | -3.6% | -5.1% | 2.26 (+126) |
| Mensik v F. Cerundolo | 56.2% | 44%, 69% | 56.3% | 58.7% | **58.0%** | -6.1% | -3.3% | 2.38 (+138) |
| Khachanov v Mannarino | 66.0% | 70%, 60%, 64% | 65.0% | 72.9% | **70.6%** | -8.3% | +3.1% | 3.40 (+240) |
| Hurkacz v Zhou Yi | 74.9% | 81% | 77.9% | 85.4% | **83.1%** | -7.7% | +9.5% | 5.93 (+493) |

Third-party model notes: ZVE-HAL: wincomparator model 83% | SHE-GEA: Elo-derived (stringtension snapshots: Shelton hard ~2009/1981 vs Gea hard 1719 -> ~0.82-0.85); wincomparator's own 59% excluded (inconsistent with its odds) | DEM-SAK: wincomparator model 59.7-61.3% | DF-TIA: wincomparator 56.2%; stringtension Elo 62.0% / 50.3% (two snapshots) | CER-MEN: wincomparator model has Cerundolo 56.3% (Mensik 43.7%); stringtension hard Elo 1933 (Mensik) favours Mensik ~0.69; H2H Cerundolo 2-0/3-0 and 6-3 6-3 last week at Beijing | KHA-MAN: wincomparator 70.4%; ats.io 60%; stringtension Elo 63.8% | HUR-ZHO: wincomparator model 80.8%

## 4. Simulated scoreline distributions (calibrated to p_blend)

| Match | P(fav wins) | P(3 sets) base / alt(35%) | P(fav in straights) | Total games mean / median | Mean total (alt) |
|---|---|---|---|---|---|
| Zverev v Halys | 80.7% | 34.3% / 31.5% | 56.8% | 23.4 / 22 | 22.8 |
| Shelton v Gea | 72.4% | 39.6% / 36.3% | 47.2% | 24.9 / 23 | 24.4 |
| De Minaur v Sakamoto | 69.1% | 40.5% / 37.4% | 44.1% | 24.4 / 23 | 23.9 |
| Tiafoe v Davidovich Fokina | 55.6% | 43.7% / 40.4% | 32.3% | 24.7 / 23 | 24.1 |
| Mensik v F. Cerundolo | 58.3% | 43.6% / 40.4% | 34.3% | 25.0 / 23 | 24.5 |
| Khachanov v Mannarino | 70.8% | 39.9% / 36.8% | 45.8% | 24.3 / 23 | 23.8 |
| Hurkacz v Zhou Yi | 82.9% | 33.2% / 30.1% | 59.2% | 24.3 / 22 | 23.7 |

**P(total games OVER line)** - base model (sigma for 38% three-set rate); in brackets the sensitivity run (about 35% three-set rate). Distribution is bimodal (straight sets about 18-23, three sets about 27-35), so P(over 23.5) and P(over 24.5) are nearly equal.

| Match | 19.5 | 20.5 | 21.5 | 22.5 | 23.5 | 24.5 | 25.5 |
|---|---|---|---|---|---|---|---|
| Zverev v Halys | 66% (62%) | 58% (54%) | 52% (48%) | 44% (41%) | 38% (35%) | 37% (34%) | 34% (31%) |
| Shelton v Gea | 77% (73%) | 69% (65%) | 64% (59%) | 54% (50%) | 46% (43%) | 45% (42%) | 42% (39%) |
| De Minaur v Sakamoto | 74% (70%) | 66% (62%) | 60% (56%) | 52% (48%) | 45% (42%) | 44% (41%) | 41% (38%) |
| Tiafoe v Davidovich Fokina | 75% (72%) | 68% (64%) | 63% (58%) | 54% (50%) | 48% (45%) | 47% (43%) | 43% (40%) |
| Mensik v F. Cerundolo | 78% (74%) | 70% (66%) | 65% (61%) | 56% (52%) | 49% (46%) | 48% (45%) | 45% (41%) |
| Khachanov v Mannarino | 73% (69%) | 65% (61%) | 60% (55%) | 51% (47%) | 45% (41%) | 44% (40%) | 40% (37%) |
| Hurkacz v Zhou Yi | 74% (69%) | 65% (60%) | 59% (54%) | 49% (44%) | 40% (37%) | 40% (36%) | 37% (33%) |

**Games won per player (mean / median; P(More) at lines).** Lookup for any Dabble/Underdog 'games won' line (none were found for today).

| Player | Mean | Median | >7.5 | >8.5 | >9.5 | >10.5 | >11.5 | >12.5 | >13.5 |
|---|---|---|---|---|---|---|---|---|---|
| Zverev | 13.3 | 13 | 97% | 95% | 94% | 92% | 91% | 56% | 34% |
| Halys | 10.0 | 9 | 66% | 57% | 50% | 44% | 40% | 32% | 23% |
| Shelton | 13.5 | 13 | 96% | 94% | 91% | 89% | 87% | 62% | 40% |
| Gea | 11.4 | 12 | 79% | 70% | 63% | 56% | 52% | 43% | 32% |
| De Minaur | 13.2 | 13 | 94% | 91% | 88% | 86% | 84% | 58% | 38% |
| Sakamoto | 11.2 | 12 | 77% | 69% | 63% | 57% | 54% | 43% | 31% |
| Tiafoe | 12.6 | 13 | 89% | 84% | 81% | 77% | 74% | 54% | 37% |
| Davidovich Fokina | 12.0 | 12 | 84% | 78% | 73% | 69% | 65% | 50% | 35% |
| Mensik | 12.9 | 13 | 91% | 87% | 83% | 79% | 77% | 57% | 39% |
| F. Cerundolo | 12.1 | 13 | 84% | 78% | 72% | 67% | 64% | 50% | 36% |
| Khachanov | 13.2 | 13 | 95% | 92% | 89% | 87% | 85% | 58% | 38% |
| Mannarino | 11.1 | 12 | 76% | 68% | 61% | 55% | 52% | 41% | 30% |
| Hurkacz | 13.7 | 13 | 98% | 97% | 96% | 94% | 93% | 62% | 37% |
| Zhou Yi | 10.6 | 10 | 73% | 62% | 53% | 45% | 41% | 34% | 26% |

## 5. Outlier flags

**Underdogs with blended edge > 3% (all price-source dependent; all LOW confidence; verify the live price first):**

- **Sakamoto ML** at 3.75 (+275): p_blend 31.1% vs break-even 26.7%, edge +16.5%, quarter-Kelly 1.50% of bankroll. Needs a price of 3.22 (+222) or better to be +EV.
- **Mannarino ML** at 3.50 (+250): p_blend 29.4% vs break-even 28.6%, edge +3.1%, quarter-Kelly 0.31% of bankroll. Needs a price of 3.40 (+240) or better to be +EV.
- **Zhou Yi ML** at 6.50 (+550): p_blend 16.9% vs break-even 15.4%, edge +9.5%, quarter-Kelly 0.43% of bankroll. Needs a price of 5.93 (+493) or better to be +EV.

  - Sakamoto: the large edge exists because Kalshi's 68% for De Minaur is far below the book-implied 74%; if the real bet365 price is shorter than +221 the edge disappears. De Minaur also retired with an adductor problem in the China Open final ([Canberra Times](https://www.canberratimes.com.au/story/9365913/demon-gifted-walkover-as-djokovic-suffers-shock-defeat/)) but then got a walkover; Sakamoto (rank 137) beat Rublev 6-4 6-4 and is a big server.
  - Zhou Yi (rank 277 wildcard) beat Musetti 7-6 3-6 7-6 but the blended model gives Zhou only 16.9%; Hurkacz has won 8 straight in Shanghai and held all 10 service games against Djokovic ([Tennis Majors](https://www.tennismajors.com/?p=862876)). Edge comes mainly from third-party models at 78-81% vs a market at 85%.
  - Mannarino +3.1% is within the noise of price-source differences; treat as no bet.

**Totals lines a full game or more off the model median:** only Zverev-Halys. Line 20.5 ([Stats Zone](https://www.thestatszone.com/alexander-zverev-vs-quentin-halys-preview-prediction-2026-shanghai-masters-third-round-229401) tips Over 20.5) vs model median 22 (mean 23.4): P(over 20.5) = 58.1% base / 53.7% at a 35% three-set rate; blended edge at -110 = +0.1% (base), negative in the sensitivity run. **Not a bet.** Khachanov-Mannarino 22.5 vs median 23 and Hurkacz-Zhou 21.5 vs median 22 are within half a game. ats.io's 'projected totals' (20, 20, 23 games) are modal straight-set scores, not medians, and its UNDER leans (22.5 and 21.5) are not supported by this model (Khachanov-Mannarino P(over 22.5) = 51.1%, Hurkacz-Zhou P(over 21.5) = 59.1%).

| Total-games leg | Line | P_model(over) base / alt | Over p_blend | Over edge @-110 | Under p_blend | Under edge @-110 |
|---|---|---|---|---|---|---|
| Zverev v Halys | 20.5 | 58.1% / 53.7% | 52.4% | +0.1% | 47.6% | -9.2% |
| Khachanov v Mannarino | 22.5 | 51.1% / 47.3% | 50.3% | -3.9% | 49.7% | -5.2% |
| Hurkacz v Zhou Yi | 21.5 | 59.1% / 54.4% | 52.7% | +0.7% | 47.3% | -9.7% |

Cerundolo-Mensik 'Over 2.5 sets' at +110 (Caesars, per Sportytrader): model P(3 sets) = 43.6% (alt 40.4%); blended with the vig-inclusive 47.6% implied = 46.4% vs 47.6% break-even -> edge -2.5%. No bet.

**Dabble/Underdog pick'em legs clearing the thresholds:** none identifiable. No pick'em lines were found, and no total-games leg has a blended probability above 52.8% (needs 55.0% for a 3-pick, 57.7% for a 2-pick). Using the lookup table above: a 'More' leg needs raw model p >= 66.7% (3-pick) or 75.7% (2-pick); the few cells that exceed 66.7% (e.g. Halys More 7.5 = 66%, Gea More 8.5 = 70%) sit well below the medians, where a pick'em book would not post the line, so they are not actionable.

**Bottom line:** the market and the blended model agree within about 5 points on every match; after vig there is no moneyline or total with a robust positive edge. The three flagged underdog prices are the only positive-EV candidates and each depends on a price I could not verify and on matches that may already be over.

## 6. Validation (internal only; no outcome data reachable)

- Win-probability calibration: max |simulated win prob - target p_blend| across 7 matches = 0.30 points (MC standard error about 0.08 points).
- Three-set rate: tour-like mix = 38.3% (target 38%); even-match iid check (sigma=0) = 50.2% vs theoretical 50%; 7-match slate average = 39.3% (alt 36.1%), higher because several matches are near coin-flips.
- Market sanity: slate-average no-vig favourite probability = 70.7%; published ATP odds study says favourites win 72% of matches ([NYC Data Science Academy](https://nycdatascience.com/blog/?p=12289)). Consistent.
- Hold formula inverse check: inv_hold(0.805) -> 63.6% point-win on serve -> hold 80.5% (exact).
- Known bias risk: the tour-like mix gives a mean of about 23.7 total games, and I could not source an independent tour average games-per-match (an unsourced explainer says 18-25), so P(over) may run 3-5 points high (compare the 'alt' columns). Treat totals as +/-5 points uncertain.
- Not done (no data): Brier/log-loss, calibration plot, fitted Benter weight. w = 0.3 is the prescribed default, not fitted.

## 7. Tour-level stats for the men-vs-women comparison

| Item | Men (ATP, best-of-3 hard) | Source / status |
|---|---|---|
| Typical service hold, hard | **about 80-81% tour average = ASSUMPTION (not found).** Top holders 2025: Sinner 92.0% (713/775), Fritz 89.2%, Mpetshi Perricard 89.0%, Djokovic 88.7%, Opelka 88.5%; Djokovic career 86.1% | [ATP: Sinner serve/return Nov 2025](https://www.atptour.com/en/news/sinner-serve-return-november-2025), [ATP: Djokovic beyond the numbers](https://www.atptour.com/en/news/djokovic-infosys-atp-beyond-the-numbers-september-2025). Opponent strength matters: Fils holds 94.2% vs players outside the top 50 but 78.9% vs the top 50 ([Last Word on Sports](https://lastwordonsports.com/tennis/2026/04/19/hard-court-jekyll-hydes/)) |
| Three-set rate (best-of-3) | **about 35-36%** (36% in one Tennis Abstract season, about 35% in a 2024 post; Challengers 32%). Model target here 38% | [Tennis Abstract: odds of three-setters](https://tennisabstract.com/blog/?p=1694), [Tennis Abstract: Hubi's three-set magic](https://tennisabstract.com/blog/?p=6950) |
| Favourite win rate | **72%** of matches for the bookmaker favourite (ATP 2012-14, 7,509 matches); 'major upsets' (dog priced > 5.0 wins) about 2% of matches; rating-based heavy favourites (90-100% predicted) actually won 89.3% vs 96.0% predicted, overall upset rate about 1.5% (different definition) | [NYC Data Science Academy](https://nycdatascience.com/blog/?p=12289), [Tennis Recruiting](https://secure.tennisrecruiting.net/article.asp?id=2457). Today's slate: market favourite average 70.7%, blended 69.9% |
| Upset frequency by favourite band (model, equal-hold mix) | Fav 70% -> dog wins 30%; fav 82% -> 18%; fav 88% -> 12% (by construction); three-set rate falls from 43.8% (fav 52%) to 28.5% (fav 88%) | model (`tour_ref.py`) |
| Total-games spread (model, tour-like mix) | mean 23.7, SD 6.0, 10th/25th/50th/75th/90th pct = 17/19/22/29/32; straight-set matches average 19.6 games, three-setters 30.3. Bimodal. Unverified explainer range: 18-25 games per match | model (`tour_ref.py`); [SportsSurge explainer](https://sportssurge.alibaba.com/tennis/how-many-games-are-in-tennis) (unsourced) |
| P(over 22.5) by fav strength (model) | fav 58%: 53%; fav 70%: 50%; fav 82%: 42%; fav 88%: 36% | model |

Note for the women's comparison: this report supplies only the men's side. Women's hold rates are generally lower than men's (general knowledge, not sourced here), so compare hold%, three-set rate and favourite win rate at matched prices using the women's agent's own sourced numbers rather than anything inferred from this file.

## 8. What was NOT found (do not assume)

- Official order of play with per-match start times and courts for Oct 11 (and whether any of these moved to Oct 12).
- bet365 / Dabble / Underdog lines (never accessed by design). Tennis pick'em lines for these matches: **not found**.
- Hard-court serve/return stats (hold%, break%, SPW/RPW) for any of the 14 players; tour-average hold%.
- Total-games lines for Shelton-Gea, De Minaur-Sakamoto, Tiafoe-Davidovich Fokina, Cerundolo-Mensik (only a sets market).
- Davidovich Fokina's moneyline price (assumed 2.14 from Tiafoe's 1.73 and a 4.5% overround).
- Results of Oct 10-11 matches (search index has none). Saturday R64 winners (Alcaraz, Tsitsipas, Fils, Lehecka, Jodar etc.) and the full R32 card for Oct 12 are not covered.
- Elo/ranking figures from stringtension snapshots are inconsistent between pages (e.g. Khachanov hard Elo 1479 vs Mannarino 1889 while overall Elo says the opposite), so Elo was used only as a rough cross-check, never as a main input.
