# NFL player-prop projections - Sunday Oct 11 2026 (nflverse "Week 5") - Dabble / Underdog / bet365 comparison

Generated Sun Oct 11 2026 ~13:30 UTC from public data only (nflverse player stats + schedule/consensus lines, public news snippets). No sportsbook / DFS app was logged into or scraped.

## 0. Read this first

* **Week label:** the task said "Week 6", but nflverse (and every public article found) calls today's Sunday Oct 11 slate **Week 5**; Week 6 starts Thu Oct 15. I projected the 13 games on the board **today** (plus Monday BUF@LA, flagged `Mon`). Kickoffs: PHI@JAX 13:30 UTC (London - starts before most people read this), nine 17:00 UTC games, 20:05/20:25 UTC games, BAL@ATL 00:20 UTC.
* **Public lines were thin.** WebFetch is blocked in this sandbox and search returns snippets only. I found real 2026-Week-5 consensus numbers for only ~10 props (table in section 2). **No public Dabble / Underdog / bet365 lines were found** - not fabricated. Prices not seen are marked ASSUMED.
* **Bottom line: the market looks efficient against this model.** After the Benter blend (w=0.30) only 4 of the ~10 priced props clear the -110 break-even, each by 1.7% to 3.4% edge, **none clears a pick'em per-leg bar** (3-pick 55.0%, 2-pick 57.7%). Treat everything as small-stakes ($1) and low confidence.
* For anything you see in the Dabble/Underdog app, use the **lookup columns in section 3**: each projection lists the posted-line cut-offs at which More/Less would clear the bar after blending (p_market = 0.5 for pick'em).

## 1. Method and validation

**Model (per stat):** player mean = exponentially-weighted (half-life in games, fitted) average of his own games across 2022-2026, shrunk toward a role prior (QB / RB1 / WR-TE rank 1-2); times a log-linear (quasi-Poisson GLM) adjustment for opponent defence (shrunk EWMA of stat allowed to that position group), team implied total (from consensus total & spread) and spread; distribution = Negative Binomial with dispersion from method of moments. All features are causal (only games before the target game). Role set backtested = starting QB, RB1, top-2 WR/TE by prior target share (among players who actually appeared).

**Fitted (final, trained 2023 to 2026 wk5-TNF):** pass_yds: half-life 5 games, shrink k=6, GLM [int, log opp, log implied, spread/7] = [0.01, 0.49, 0.42, -0.04], NB alpha=0.115; pass_tds: half-life 5 games, shrink k=6, GLM [int, log opp, log implied, spread/7] = [0.0, 0.03, 0.7, -0.0], NB alpha=0.001; rush_yds: half-life 3 games, shrink k=3, GLM [int, log opp, log implied, spread/7] = [-0.0, 0.4, 0.24, 0.03], NB alpha=0.300; rec_yds: half-life 8 games, shrink k=3, GLM [int, log opp, log implied, spread/7] = [-0.01, 0.45, 0.43, -0.05], NB alpha=0.375; receptions: half-life 5 games, shrink k=3, GLM [int, log opp, log implied, spread/7] = [-0.01, 0.33, 0.39, -0.06], NB alpha=0.060

**Out-of-sample test = 2025 weeks 6-18** (fit on 2023, 2024, 2025 wk1-5; features strictly pre-game). n = 369 QB, 381 RB1, 768 WR/TE-slots.

| Stat | MAE model | MAE EWMA-only | MAE naive EWMA | P(over at median-line) pred / obs | -10% line pred / obs | +10% line pred / obs | mean(proj) vs mean(actual) |
|---|---|---|---|---|---|---|---|
| Pass yds | 59.2 | 62.4 | 63.5 | 49.7% / 51.2% | 61.7% / 61.8% | 39.0% / 39.6% | 224.5 vs 215.0 |
| Pass TDs | 0.96 | 0.97 | 1.01 | 0.5: 75.2% / 75.1% ; 1.5: 42.4% / 43.6% ; 2.5: 19.1% / 18.2% | - | - | 1.47 vs 1.43 |
| Rush yds (RB1) | 28.5 | 29.0 | 29.2 | 49.4% / 52.2% | 57.0% / 58.3% | 43.4% / 47.5% | 62.4 vs 64.2 |
| Rec yds (top-2 WR/TE) | 26.9 | 27.4 | 26.9 | 49.3% / 46.0% | 56.2% / 52.0% | 44.1% / 41.9% | 54.6 vs 51.6 |
| Receptions | 1.81 | 1.83 | 1.82 | 41.5% / 36.1% (line = floor(med)+.5) | 58.8% / 55.6% | 27.0% / 22.5% | 4.46 vs 4.18 |

* Pooled over all stats and offset lines (-20% to +20%): model log-loss 0.6310 vs 0.6410 for EWMA-only (no opp/script adj). Model-preferred-side buckets: p>=0.55 -> predicted 66.1%, hit 65.7% (n=10,421); p>=0.66 -> 76.7% vs 77.7% (n=3,875); p>=0.76 -> 82.7% vs 83.4% (n=1,824). **QB and RB probabilities are well calibrated.**
* **Known weakness:** receiving yards / receptions were over-projected ~6% in the 2025 test window (league-wide receiving fell ~6% vs 2023-24), so receiving *Over* probabilities there were ~3-5 pts too high. The 2026 year-to-date actual/projection ratio is 0.99 (rec yds) and 0.98 (receptions), 1.02 (pass yds), 1.01 (rush yds), so no correction was applied, but treat receiving Overs with extra caution.
* **Not validated against the market:** no historical prop lines are available publicly, so w (model weight) could not be fitted; w = 0.30 is the assumed Benter weight. The validation shows the model is calibrated to *outcomes*, not that it beats closing lines - the market is probably sharper, which is why the blended edges are small.

## 2. Publicly reported lines vs model (both sides, after blending)

p_blend = 0.30 x p_model + 0.70 x p_market(no-vig). Break-even = 1/decimal price. Edge = p_blend x decimal - 1. "Pick'em 3-leg OK" = p_blend >= 55.0%.

| Player | Game | Market | Side | Line | Price | Mean/Median | p_model | p_market | p_blend | Break-even | Edge | 3-leg bar | Line reliability / source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Jayden Daniels | WAS vs NYG | pass_yds | UNDER | 210.5 | -110 | 193.7 / 186 | 63.9% | 50.0% | 54.2% | 52.4% | +3.4% | no | Low: Legal Sports Report snippet (opponent mislabeled in snippet); prices ASSUMED |
| Cam Ward | TEN vs HOU | pass_yds | UNDER | 193.5 | -110 | 181.7 / 175 | 61.7% | 50.0% | 53.5% | 52.4% | +2.1% | no | Medium: SportsBettingDime 10/9 (193.5 current); prices ASSUMED |
| C.J. Stroud | HOU vs TEN | pass_yds | UNDER | 243.5 | -110 | 230.2 / 221 | 60.9% | 50.0% | 53.3% | 52.4% | +1.7% | no | Medium: SportsBettingDime line-move piece 10/9 (243.5 current); prices ASSUMED -110/-110 |
| Chase Brown | CIN vs MIA | rush_yds | UNDER | 65.5 | -110 | 62.2 / 56 | 60.9% | 50.0% | 53.3% | 52.4% | +1.7% | no | Low: FantasyAlarm expert pick (over 65.5); prices ASSUMED |
| Michael Wilson | ARI vs DET | rec_yds | UNDER | 70 | +100 | 69.4 / 61 | 58.8% | 46.9% | 50.5% | 50.0% | +1.0% | n/a (priced market) | Medium: FantasyLife pick article (over 70 -130); UNDER price ASSUMED +100 |
| Amon-Ra St. Brown | DET vs ARI | rec_yds | UNDER | 80 | -110 | 85.7 / 75 | 53.9% | 50.0% | 51.2% | 52.4% | -2.3% | no | Low: Squawka editorial pick (over 80); prices ASSUMED |
| Jalen Hurts | PHI vs JAX | pass_tds | OVER | 0.5 | -225 | 1.2 / 1 | 71.0% | 65.6% | 67.2% | 69.2% | -2.9% | n/a (priced market) | Medium: Inquirer 10/8; UNDER price not found -> +175 ASSUMED |
| Jalen Hurts | PHI vs JAX | pass_yds | UNDER | 193.5 | -112 | 193.9 / 186 | 54.3% | 50.0% | 51.3% | 52.8% | -2.9% | no | Medium: Inquirer 10/8 (FD 193.5 / DK 189.5, ~-112/-114) |
| Chris Olave | NO vs MIN | rec_yds | UNDER | 70 | -110 | 76.5 / 67 | 52.7% | 50.0% | 50.8% | 52.4% | -3.0% | no | Low: Squawka editorial pick (over 70); prices ASSUMED |
| Jared Goff | DET vs ARI | pass_yds | OVER | 280.5 | -110 | 297.7 / 286 | 52.3% | 50.0% | 50.7% | 52.4% | -3.2% | no | Low: StackedFantasy snippet; prices ASSUMED |
| Jared Goff | DET vs ARI | pass_yds | UNDER | 280.5 | -110 | 297.7 / 286 | 47.7% | 50.0% | 49.3% | 52.4% | -5.9% | no | Low: StackedFantasy snippet; prices ASSUMED |
| Chris Olave | NO vs MIN | rec_yds | OVER | 70 | -110 | 76.5 / 67 | 47.3% | 50.0% | 49.2% | 52.4% | -6.1% | no | Low: Squawka editorial pick (over 70); prices ASSUMED |
| Amon-Ra St. Brown | DET vs ARI | rec_yds | OVER | 80 | -110 | 85.7 / 75 | 46.1% | 50.0% | 48.8% | 52.4% | -6.8% | no | Low: Squawka editorial pick (over 80); prices ASSUMED |
| Jalen Hurts | PHI vs JAX | pass_yds | OVER | 193.5 | -112 | 193.9 / 186 | 45.7% | 50.0% | 48.7% | 52.8% | -7.8% | no | Medium: Inquirer 10/8 (FD 193.5 / DK 189.5, ~-112/-114) |
| Jalen Hurts | PHI vs JAX | pass_tds | UNDER | 0.5 | +175 | 1.2 / 1 | 29.0% | 34.4% | 32.8% | 36.4% | -9.8% | n/a (priced market) | Medium: Inquirer 10/8; UNDER price not found -> +175 ASSUMED |
| Chase Brown | CIN vs MIA | rush_yds | OVER | 65.5 | -110 | 62.2 / 56 | 39.1% | 50.0% | 46.7% | 52.4% | -10.8% | no | Low: FantasyAlarm expert pick (over 65.5); prices ASSUMED |
| C.J. Stroud | HOU vs TEN | pass_yds | OVER | 243.5 | -110 | 230.2 / 221 | 39.1% | 50.0% | 46.7% | 52.4% | -10.8% | no | Medium: SportsBettingDime line-move piece 10/9 (243.5 current); prices ASSUMED -110/-110 |
| Cam Ward | TEN vs HOU | pass_yds | OVER | 193.5 | -110 | 181.7 / 175 | 38.4% | 50.0% | 46.5% | 52.4% | -11.2% | no | Medium: SportsBettingDime 10/9 (193.5 current); prices ASSUMED |
| Michael Wilson | ARI vs DET | rec_yds | OVER | 70 | -130 | 69.4 / 61 | 41.2% | 53.1% | 49.5% | 56.5% | -12.4% | n/a (priced market) | Medium: FantasyLife pick article (over 70 -130); UNDER price ASSUMED +100 |
| Jayden Daniels | WAS vs NYG | pass_yds | OVER | 210.5 | -110 | 193.7 / 186 | 36.1% | 50.0% | 45.8% | 52.4% | -12.5% | no | Low: Legal Sports Report snippet (opponent mislabeled in snippet); prices ASSUMED |

Notes: Daniels uses his projection with the two injury-shortened 2026 games (dislocated elbow) dropped from his history (raw model said 186 mean; adjusted 194). Hurts, Goff, St. Brown, Olave have no edge on either side. Wilson UNDER 70 clears only if the under is priced +100 or better (assumed) - not recommended. Allen over 249.5 and Stafford 280.5 are Monday-night lines, not evaluated.

## 3. Projection tables (for comparing any Dabble / Underdog line)

Columns: **Mean/Median/SD** = model; **P(over)** at five lines around the median; **More clears if line <=** / **Less clears if line >=** = the posted-line cut-off at which the leg beats the break-even after blending, for a 3-pick pick'em (needs p_model>=66.8%), 2-pick pick'em (>=75.8%) and a -110 sportsbook prop (>=57.9%). "-" = no line qualifies. `lowdata` = fewer than ~6 effective games of history. Status flags come from public injury news (Oct 7-11) - **re-check inactives ~90 min before kickoff**.

### Passing yards (starting QB)

| Player | Game (day, kick ET) | Mean | Med | SD | P(over) at lines | More <= (3pk/2pk/-110) | Less >= (3pk/2pk/-110) | Status |
|---|---|---|---|---|---|---|---|---|
| Josh Allen (QB, QB) | BUF v LA (Mon 20:15) | 241.8 | 232 | 83.3 | 212.5: 60% / 222.5: 55% / 232.5: 50% / 242.5: 45% / 252.5: 41% | 198.5 / 179.5 / 215.5 | 270.5 / 294.5 / 249.5 |  |
| Matthew Stafford (QB, QB) | LA v BUF (Mon 20:15) | 281.3 | 270 | 96.7 | 250.5: 59% / 260.5: 54% / 270.5: 50% / 280.5: 46% / 290.5: 42% | 230.5 / 209.5 / 251.5 | 314.5 / 342.5 / 290.5 |  |
| Trevor Lawrence (QB, QB) | JAX v PHI (Sun 09:30) | 220.9 | 212 | 76.2 | 192.5: 61% / 202.5: 55% / 212.5: 50% / 222.5: 45% / 232.5: 40% | 181.5 / 163.5 / 197.5 | 246.5 / 269.5 / 228.5 |  |
| Jalen Hurts (QB, QB) | PHI v JAX (Sun 09:30) | 193.9 | 186 | 67.1 | 166.5: 62% / 176.5: 56% / 186.5: 50% / 196.5: 44% / 206.5: 38% | 158.5 / 143.5 / 173.5 | 216.5 / 236.5 / 200.5 |  |
| Tyson Bagent (QB, QB) | CHI v GB (Sun 13:00) | 160.5 | 154 | 55.8 | 134.5: 65% / 144.5: 57% / 154.5: 50% / 164.5: 43% / 174.5: 36% | 131.5 / 118.5 / 143.5 | 179.5 / 196.5 / 165.5 |  |
| Joe Burrow (QB, QB) | CIN v MIA (Sun 13:00) | 261.8 | 252 | 90.1 | 232.5: 59% / 242.5: 54% / 252.5: 50% / 262.5: 45% / 272.5: 41% | 214.5 / 194.5 / 233.5 | 292.5 / 318.5 / 270.5 |  |
| Deshaun Watson (QB, QB) | CLE v NYJ (Sun 13:00) | 193.7 | 186 | 67.0 | 166.5: 62% / 176.5: 56% / 186.5: 50% / 196.5: 44% / 206.5: 38% | 158.5 / 143.5 / 172.5 | 216.5 / 236.5 / 200.5 |  |
| Jordan Love (QB, QB) | GB v CHI (Sun 13:00) | 230.1 | 221 | 79.4 | 201.5: 60% / 211.5: 55% / 221.5: 50% / 231.5: 45% / 241.5: 40% | 188.5 / 170.5 / 205.5 | 257.5 / 280.5 / 237.5 |  |
| C.J. Stroud (QB, QB) | HOU v TEN (Sun 13:00) | 230.2 | 221 | 79.4 | 201.5: 60% / 211.5: 55% / 221.5: 50% / 231.5: 45% / 241.5: 40% | 188.5 / 170.5 / 205.5 | 257.5 / 280.5 / 237.5 |  |
| Daniel Jones (QB, QB) | IND v PIT (Sun 13:00) | 211.4 | 203 | 73.0 | 183.5: 61% / 193.5: 56% / 203.5: 50% / 213.5: 44% / 223.5: 39% | 173.5 / 156.5 / 188.5 | 236.5 / 257.5 / 218.5 |  |
| Kirk Cousins (QB, QB) | LV v NE (Sun 13:00) | 217.2 | 209 | 75.0 | 189.5: 61% / 199.5: 55% / 209.5: 50% / 219.5: 44% / 229.5: 39% | 178.5 / 161.5 / 193.5 | 242.5 / 264.5 / 224.5 |  |
| Malik Willis (QB, QB) | MIA v CIN (Sun 13:00) | 173.3 | 167 | 60.1 | 147.5: 63% / 157.5: 56% / 167.5: 49% / 177.5: 43% / 187.5: 37% | 141.5 / 128.5 / 154.5 | 193.5 / 211.5 / 179.5 |  |
| Kyler Murray (QB, QB) | MIN v NO (Sun 13:00) | 198.0 | 190 | 68.5 | 170.5: 62% / 180.5: 56% / 190.5: 50% / 200.5: 44% / 210.5: 39% | 162.5 / 146.5 / 176.5 | 221.5 / 241.5 / 204.5 |  |
| Drake Maye (QB, QB) | NE v LV (Sun 13:00) | 231.4 | 223 | 79.8 | 203.5: 60% / 213.5: 55% / 223.5: 49% / 233.5: 44% / 243.5: 40% | 189.5 / 171.5 / 206.5 | 258.5 / 282.5 / 238.5 |  |
| Tyler Shough (QB, QB) | NO v MIN (Sun 13:00) | 226.0 | 217 | 78.0 | 197.5: 61% / 207.5: 55% / 217.5: 50% / 227.5: 45% / 237.5: 40% | 185.5 / 167.5 / 201.5 | 252.5 / 275.5 / 233.5 |  |
| Jameis Winston (QB, QB) | NYG v WAS (Sun 13:00) | 199.3 | 192 | 68.9 | 172.5: 62% / 182.5: 55% / 192.5: 49% / 202.5: 44% / 212.5: 38% | 163.5 / 147.5 / 177.5 | 222.5 / 243.5 / 205.5 |  |
| Geno Smith (QB, QB) | NYJ v CLE (Sun 13:00) | 204.8 | 197 | 70.8 | 177.5: 61% / 187.5: 55% / 197.5: 50% / 207.5: 44% / 217.5: 39% | 167.5 / 151.5 / 182.5 | 228.5 / 249.5 / 211.5 |  |
| Aaron Rodgers (QB, QB) | PIT v IND (Sun 13:00) | 240.5 | 231 | 82.9 | 211.5: 60% / 221.5: 55% / 231.5: 50% / 241.5: 45% / 251.5: 40% | 197.5 / 178.5 / 214.5 | 268.5 / 293.5 / 248.5 |  |
| Cam Ward (QB, QB) | TEN v HOU (Sun 13:00) | 181.7 | 175 | 63.0 | 155.5: 63% / 165.5: 56% / 175.5: 49% / 185.5: 43% / 195.5: 37% | 148.5 / 134.5 / 162.5 | 203.5 / 221.5 / 187.5 |  |
| Jayden Daniels (QB, QB) | WAS v NYG (Sun 13:00) | 193.7 | 186 | 67.0 | 166.5: 62% / 176.5: 56% / 186.5: 50% / 196.5: 44% / 206.5: 38% | 158.5 / 143.5 / 172.5 | 216.5 / 236.5 / 200.5 | Expected to play after elbow dislocation (2026 injury-shortened games excluded from his history); backup Mariota hurt (MCL) |
| Bo Nix (QB, QB) | DEN v LAC (Sun 16:05) | 214.2 | 206 | 74.0 | 186.5: 61% / 196.5: 55% / 206.5: 50% / 216.5: 44% / 226.5: 39% | 175.5 / 158.5 / 191.5 | 239.5 / 261.5 / 221.5 |  |
| Justin Herbert (QB, QB) | LAC v DEN (Sun 16:05) | 208.9 | 201 | 72.2 | 181.5: 61% / 191.5: 55% / 201.5: 50% / 211.5: 44% / 221.5: 39% | 171.5 / 154.5 / 186.5 | 233.5 / 254.5 / 215.5 |  |
| Jacoby Brissett (QB, QB) | ARI v DET (Sun 16:25) | 252.4 | 243 | 86.9 | 223.5: 59% / 233.5: 54% / 243.5: 50% / 253.5: 45% / 263.5: 41% | 207.5 / 187.5 / 225.5 | 281.5 / 307.5 / 260.5 |  |
| Jared Goff (QB, QB) | DET v ARI (Sun 16:25) | 297.7 | 286 | 102.2 | 266.5: 58% / 276.5: 54% / 286.5: 50% / 296.5: 46% / 306.5: 42% | 244.5 / 221.5 / 266.5 | 332.5 / 362.5 / 307.5 |  |
| Drew Lock (QB, QB) | SEA v SF (Sun 16:25) | 184.2 | 177 | 63.8 | 157.5: 63% / 167.5: 56% / 177.5: 50% / 187.5: 43% / 197.5: 38% | 150.5 / 136.5 / 164.5 | 205.5 / 224.5 / 190.5 |  |
| Brock Purdy (QB, QB) | SF v SEA (Sun 16:25) | 225.7 | 217 | 77.9 | 197.5: 60% / 207.5: 55% / 217.5: 50% / 227.5: 45% / 237.5: 40% | 185.5 / 167.5 / 201.5 | 252.5 / 275.5 / 233.5 |  |
| Michael Penix Jr. (QB, QB) | ATL v BAL (Sun 20:20) | 227.3 | 219 | 78.4 | 199.5: 60% / 209.5: 55% / 219.5: 49% / 229.5: 44% / 239.5: 40% | 186.5 / 168.5 / 203.5 | 253.5 / 277.5 / 234.5 |  |
| Tyler Huntley (QB, QB) | BAL v ATL (Sun 20:20) | 161.8 | 156 | 56.2 | 136.5: 64% / 146.5: 57% / 156.5: 49% / 166.5: 42% / 176.5: 36% | 132.5 / 119.5 / 144.5 | 181.5 / 197.5 / 167.5 | Starting for injured Lamar Jackson (ankle) - small-sample QB |

### Passing TDs (starting QB)

| Player | Game (day, kick ET) | Mean | Med | SD | P(over) at lines | More <= (3pk/2pk/-110) | Less >= (3pk/2pk/-110) | Status |
|---|---|---|---|---|---|---|---|---|
| Josh Allen (QB, QB) | BUF v LA (Mon 20:15) | 1.6 | 1 | 1.2 | 0.5: 79% / 1.5: 46% / 2.5: 20% | 0.5 / 0.5 / 0.5 | 2.5 / 2.5 / 2.5 |  |
| Matthew Stafford (QB, QB) | LA v BUF (Mon 20:15) | 2.2 | 2 | 1.5 | 0.5: 89% / 1.5: 64% / 2.5: 37% | 0.5 / 0.5 / 1.5 | 3.5 / 3.5 / 2.5 |  |
| Trevor Lawrence (QB, QB) | JAX v PHI (Sun 09:30) | 1.8 | 2 | 1.3 | 0.5: 83% / 1.5: 53% / 2.5: 27% | 0.5 / 0.5 / 0.5 | 2.5 / 3.5 / 2.5 |  |
| Jalen Hurts (QB, QB) | PHI v JAX (Sun 09:30) | 1.2 | 1 | 1.1 | 0.5: 71% / 1.5: 35% / 2.5: 13% | 0.5 / - / 0.5 | 2.5 / 2.5 / 1.5 |  |
| Tyson Bagent (QB, QB) | CHI v GB (Sun 13:00) | 0.8 | 1 | 0.9 | 0.5: 56% / 1.5: 20% / 2.5: 5% | - / - / - | 1.5 / 1.5 / 1.5 |  |
| Joe Burrow (QB, QB) | CIN v MIA (Sun 13:00) | 1.9 | 2 | 1.4 | 0.5: 86% / 1.5: 58% / 2.5: 31% | 0.5 / 0.5 / 0.5 | 2.5 / 3.5 / 2.5 |  |
| Deshaun Watson (QB, QB) | CLE v NYJ (Sun 13:00) | 1.1 | 1 | 1.1 | 0.5: 67% / 1.5: 31% / 2.5: 10% | 0.5 / - / 0.5 | 1.5 / 2.5 / 1.5 |  |
| Jordan Love (QB, QB) | GB v CHI (Sun 13:00) | 1.6 | 1 | 1.3 | 0.5: 80% / 1.5: 47% / 2.5: 21% | 0.5 / 0.5 / 0.5 | 2.5 / 2.5 / 2.5 |  |
| C.J. Stroud (QB, QB) | HOU v TEN (Sun 13:00) | 1.4 | 1 | 1.2 | 0.5: 74% / 1.5: 39% / 2.5: 16% | 0.5 / - / 0.5 | 2.5 / 2.5 / 1.5 |  |
| Daniel Jones (QB, QB) | IND v PIT (Sun 13:00) | 1.1 | 1 | 1.1 | 0.5: 68% / 1.5: 31% / 2.5: 11% | 0.5 / - / 0.5 | 1.5 / 2.5 / 1.5 |  |
| Kirk Cousins (QB, QB) | LV v NE (Sun 13:00) | 1.6 | 1 | 1.3 | 0.5: 79% / 1.5: 47% / 2.5: 21% | 0.5 / 0.5 / 0.5 | 2.5 / 2.5 / 2.5 |  |
| Malik Willis (QB, QB) | MIA v CIN (Sun 13:00) | 0.8 | 1 | 0.9 | 0.5: 53% / 1.5: 18% / 2.5: 4% | - / - / - | 1.5 / 1.5 / 1.5 |  |
| Kyler Murray (QB, QB) | MIN v NO (Sun 13:00) | 1.1 | 1 | 1.1 | 0.5: 67% / 1.5: 30% / 2.5: 10% | 0.5 / - / 0.5 | 1.5 / 2.5 / 1.5 |  |
| Drake Maye (QB, QB) | NE v LV (Sun 13:00) | 1.6 | 1 | 1.3 | 0.5: 79% / 1.5: 46% / 2.5: 21% | 0.5 / 0.5 / 0.5 | 2.5 / 2.5 / 2.5 |  |
| Tyler Shough (QB, QB) | NO v MIN (Sun 13:00) | 1.4 | 1 | 1.2 | 0.5: 75% / 1.5: 41% / 2.5: 17% | 0.5 / - / 0.5 | 2.5 / 2.5 / 1.5 |  |
| Jameis Winston (QB, QB) | NYG v WAS (Sun 13:00) | 1.1 | 1 | 1.0 | 0.5: 67% / 1.5: 30% / 2.5: 10% | - / - / 0.5 | 1.5 / 2.5 / 1.5 |  |
| Geno Smith (QB, QB) | NYJ v CLE (Sun 13:00) | 1.3 | 1 | 1.1 | 0.5: 73% / 1.5: 38% / 2.5: 14% | 0.5 / - / 0.5 | 2.5 / 2.5 / 1.5 |  |
| Aaron Rodgers (QB, QB) | PIT v IND (Sun 13:00) | 1.5 | 1 | 1.2 | 0.5: 78% / 1.5: 45% / 2.5: 19% | 0.5 / 0.5 / 0.5 | 2.5 / 2.5 / 2.5 |  |
| Cam Ward (QB, QB) | TEN v HOU (Sun 13:00) | 0.9 | 1 | 0.9 | 0.5: 59% / 1.5: 22% / 2.5: 6% | - / - / 0.5 | 1.5 / 1.5 / 1.5 |  |
| Jayden Daniels (QB, QB) | WAS v NYG (Sun 13:00) | 1.3 | 1 | 1.2 | 0.5: 74% / 1.5: 39% / 2.5: 15% | 0.5 / - / 0.5 | 2.5 / 2.5 / 1.5 | Expected to play after elbow dislocation (2026 injury-shortened games excluded from his history); backup Mariota hurt (MCL) |
| Bo Nix (QB, QB) | DEN v LAC (Sun 16:05) | 1.4 | 1 | 1.2 | 0.5: 74% / 1.5: 39% / 2.5: 16% | 0.5 / - / 0.5 | 2.5 / 2.5 / 1.5 |  |
| Justin Herbert (QB, QB) | LAC v DEN (Sun 16:05) | 1.2 | 1 | 1.1 | 0.5: 69% / 1.5: 33% / 2.5: 12% | 0.5 / - / 0.5 | 1.5 / 2.5 / 1.5 |  |
| Jacoby Brissett (QB, QB) | ARI v DET (Sun 16:25) | 1.6 | 1 | 1.3 | 0.5: 80% / 1.5: 49% / 2.5: 23% | 0.5 / 0.5 / 0.5 | 2.5 / 2.5 / 2.5 |  |
| Jared Goff (QB, QB) | DET v ARI (Sun 16:25) | 2.2 | 2 | 1.5 | 0.5: 88% / 1.5: 63% / 2.5: 37% | 0.5 / 0.5 / 1.5 | 3.5 / 3.5 / 2.5 |  |
| Drew Lock (QB, QB) | SEA v SF (Sun 16:25) | 1.3 | 1 | 1.1 | 0.5: 73% / 1.5: 38% / 2.5: 15% | 0.5 / - / 0.5 | 2.5 / 2.5 / 1.5 |  |
| Brock Purdy (QB, QB) | SF v SEA (Sun 16:25) | 1.9 | 2 | 1.4 | 0.5: 85% / 1.5: 56% / 2.5: 29% | 0.5 / 0.5 / 0.5 | 2.5 / 3.5 / 2.5 |  |
| Michael Penix Jr. (QB, QB) | ATL v BAL (Sun 20:20) | 1.2 | 1 | 1.1 | 0.5: 71% / 1.5: 35% / 2.5: 13% | 0.5 / - / 0.5 | 2.5 / 2.5 / 1.5 |  |
| Tyler Huntley (QB, QB) | BAL v ATL (Sun 20:20) | 0.9 | 1 | 0.9 | 0.5: 58% / 1.5: 21% / 2.5: 6% | - / - / - | 1.5 / 1.5 / 1.5 | Starting for injured Lamar Jackson (ankle) - small-sample QB |

### Rushing yards (RB1 / RB2)

| Player | Game (day, kick ET) | Mean | Med | SD | P(over) at lines | More <= (3pk/2pk/-110) | Less >= (3pk/2pk/-110) | Status |
|---|---|---|---|---|---|---|---|---|
| James Cook (RB, RB1) | BUF v LA (Mon 20:15) | 83.5 | 75 | 46.7 | 65.5: 59% / 70.5: 54% / 75.5: 50% / 80.5: 45% / 85.5: 41% | 57.5 / 47.5 / 66.5 | 96.5 / 110.5 / 84.5 |  [lowdata] |
| Ty Johnson (RB, RB2) | BUF v LA (Mon 20:15) | 31.5 | 28 | 18.2 | 18.5: 74% / 23.5: 62% / 28.5: 49% / 33.5: 39% / 38.5: 29% | 20.5 / 17.5 / 24.5 | 36.5 / 42.5 / 32.5 |  [lowdata] |
| Kyren Williams (RB, RB1) | LA v BUF (Mon 20:15) | 76.0 | 68 | 42.5 | 58.5: 60% / 63.5: 55% / 68.5: 50% / 73.5: 45% / 78.5: 40% | 51.5 / 43.5 / 60.5 | 87.5 / 100.5 / 77.5 |  [lowdata] |
| Blake Corum (RB, RB2) | LA v BUF (Mon 20:15) | 53.4 | 48 | 30.1 | 38.5: 64% / 43.5: 56% / 48.5: 49% / 53.5: 43% / 58.5: 36% | 36.5 / 30.5 / 42.5 | 61.5 / 71.5 / 54.5 |  [lowdata] |
| Bhayshul Tuten (RB, RB1) | JAX v PHI (Sun 09:30) | 58.9 | 53 | 33.2 | 43.5: 63% / 48.5: 56% / 53.5: 49% / 58.5: 43% / 63.5: 38% | 40.5 / 33.5 / 46.5 | 68.5 / 78.5 / 59.5 |  [lowdata] |
| Chris Rodriguez Jr. (RB, RB2) | JAX v PHI (Sun 09:30) | 49.3 | 44 | 27.9 | 34.5: 66% / 39.5: 57% / 44.5: 50% / 49.5: 42% / 54.5: 36% | 33.5 / 27.5 / 38.5 | 57.5 / 65.5 / 50.5 |  [lowdata] |
| Tank Bigsby (RB, RB1) | PHI v JAX (Sun 09:30) | 35.3 | 32 | 20.2 | 22.5: 70% / 27.5: 59% / 32.5: 48% / 37.5: 39% / 42.5: 30% | 23.5 / 19.5 / 27.5 | 41.5 / 47.5 / 36.5 | Lead back with Barkley out - projection understates volume [lowdata] |
| D'Andre Swift (RB, RB1) | CHI v GB (Sun 13:00) | 71.4 | 64 | 40.0 | 54.5: 61% / 59.5: 55% / 64.5: 50% / 69.5: 45% / 74.5: 40% | 48.5 / 40.5 / 56.5 | 82.5 / 94.5 / 72.5 |  [lowdata] |
| Kyle Monangai (RB, RB2) | CHI v GB (Sun 13:00) | 71.8 | 65 | 40.3 | 55.5: 60% / 60.5: 54% / 65.5: 49% / 70.5: 44% / 75.5: 39% | 49.5 / 41.5 / 56.5 | 82.5 / 95.5 / 73.5 |  [lowdata] |
| Chase Brown (RB, RB1) | CIN v MIA (Sun 13:00) | 62.2 | 56 | 35.0 | 46.5: 62% / 51.5: 56% / 56.5: 49% / 61.5: 43% / 66.5: 38% | 42.5 / 35.5 / 49.5 | 71.5 / 82.5 / 63.5 |  [lowdata] |
| Samaje Perine (RB, RB2) | CIN v MIA (Sun 13:00) | 36.8 | 33 | 21.1 | 23.5: 70% / 28.5: 59% / 33.5: 49% / 38.5: 40% / 43.5: 31% | 24.5 / 20.5 / 28.5 | 42.5 / 49.5 / 37.5 |  [lowdata] |
| Quinshon Judkins (RB, RB1) | CLE v NYJ (Sun 13:00) | 52.1 | 47 | 29.5 | 37.5: 64% / 42.5: 56% / 47.5: 49% / 52.5: 42% / 57.5: 36% | 35.5 / 29.5 / 41.5 | 60.5 / 69.5 / 53.5 |  [lowdata] |
| Dylan Sampson (RB, RB2) | CLE v NYJ (Sun 13:00) | 33.4 | 30 | 19.2 | 20.5: 72% / 25.5: 60% / 30.5: 49% / 35.5: 39% / 40.5: 30% | 22.5 / 18.5 / 25.5 | 38.5 / 44.5 / 34.5 |  [lowdata] |
| MarShawn Lloyd (RB, RB1) | GB v CHI (Sun 13:00) | 39.1 | 35 | 22.3 | 25.5: 69% / 30.5: 59% / 35.5: 49% / 40.5: 40% / 45.5: 32% | 26.5 / 21.5 / 30.5 | 45.5 / 52.5 / 39.5 |  [lowdata] |
| Kaleb Johnson (RB, RB2) | GB v CHI (Sun 13:00) | 35.3 | 32 | 20.2 | 22.5: 70% / 27.5: 59% / 32.5: 48% / 37.5: 39% / 42.5: 30% | 23.5 / 19.5 / 27.5 | 41.5 / 47.5 / 36.5 |  [lowdata] |
| David Montgomery (RB, RB1) | HOU v TEN (Sun 13:00) | 43.8 | 39 | 24.9 | 29.5: 68% / 34.5: 59% / 39.5: 50% / 44.5: 42% / 49.5: 34% | 29.5 / 24.5 / 34.5 | 50.5 / 58.5 / 44.5 |  [lowdata] |
| Woody Marks (RB, RB2) | HOU v TEN (Sun 13:00) | 44.5 | 40 | 25.3 | 30.5: 67% / 35.5: 58% / 40.5: 49% / 45.5: 41% / 50.5: 34% | 30.5 / 25.5 / 34.5 | 51.5 / 59.5 / 45.5 |  [lowdata] |
| Jonathan Taylor (RB, RB1) | IND v PIT (Sun 13:00) | 71.4 | 64 | 40.0 | 54.5: 61% / 59.5: 55% / 64.5: 50% / 69.5: 45% / 74.5: 40% | 48.5 / 40.5 / 56.5 | 82.5 / 94.5 / 72.5 |  [lowdata] |
| Seth McGowan (RB, RB2) | IND v PIT (Sun 13:00) | 37.1 | 33 | 21.2 | 23.5: 71% / 28.5: 60% / 33.5: 50% / 38.5: 40% / 43.5: 32% | 24.5 / 20.5 / 28.5 | 43.5 / 49.5 / 37.5 |  [lowdata] |
| Ashton Jeanty (RB, RB1) | LV v NE (Sun 13:00) | 60.4 | 54 | 34.0 | 44.5: 63% / 49.5: 56% / 54.5: 50% / 59.5: 44% / 64.5: 38% | 41.5 / 34.5 / 47.5 | 69.5 / 80.5 / 61.5 | QUESTIONABLE (ankle/foot, not seen at Fri practice) [lowdata] |
| Mike Washington Jr. (RB, RB2) | LV v NE (Sun 13:00) | 44.0 | 40 | 25.0 | 30.5: 66% / 35.5: 57% / 40.5: 48% / 45.5: 40% / 50.5: 33% | 29.5 / 24.5 / 34.5 | 51.5 / 58.5 / 44.5 |  [lowdata] |
| Ollie Gordon II (RB, RB1) | MIA v CIN (Sun 13:00) | 41.9 | 38 | 23.9 | 28.5: 67% / 33.5: 58% / 38.5: 48% / 43.5: 40% / 48.5: 33% | 28.5 / 23.5 / 32.5 | 48.5 / 56.5 / 42.5 | Lead back with Achane out - projection understates volume [lowdata] |
| Aaron Jones (RB, RB1) | MIN v NO (Sun 13:00) | 68.8 | 62 | 38.6 | 52.5: 61% / 57.5: 55% / 62.5: 49% / 67.5: 44% / 72.5: 39% | 46.5 / 39.5 / 54.5 | 79.5 / 91.5 / 69.5 |  [lowdata] |
| Jordan Mason (RB, RB2) | MIN v NO (Sun 13:00) | 56.7 | 51 | 32.0 | 41.5: 63% / 46.5: 56% / 51.5: 49% / 56.5: 43% / 61.5: 37% | 38.5 / 32.5 / 44.5 | 65.5 / 75.5 / 57.5 |  [lowdata] |
| TreVeyon Henderson (RB, RB1) | NE v LV (Sun 13:00) | 61.3 | 55 | 34.5 | 45.5: 62% / 50.5: 56% / 55.5: 50% / 60.5: 44% / 65.5: 38% | 41.5 / 34.5 / 48.5 | 70.5 / 81.5 / 62.5 |  [lowdata] |
| Rhamondre Stevenson (RB, RB2) | NE v LV (Sun 13:00) | 56.7 | 51 | 32.0 | 41.5: 63% / 46.5: 56% / 51.5: 49% / 56.5: 43% / 61.5: 37% | 38.5 / 32.5 / 44.5 | 65.5 / 75.5 / 57.5 |  [lowdata] |
| Travis Etienne (RB, RB1) | NO v MIN (Sun 13:00) | 51.7 | 46 | 29.2 | 36.5: 65% / 41.5: 57% / 46.5: 50% / 51.5: 43% / 56.5: 37% | 35.5 / 29.5 / 40.5 | 59.5 / 68.5 / 52.5 |  [lowdata] |
| Alvin Kamara (RB, RB2) | NO v MIN (Sun 13:00) | 41.6 | 37 | 23.7 | 27.5: 69% / 32.5: 59% / 37.5: 50% / 42.5: 41% / 47.5: 34% | 27.5 / 23.5 / 32.5 | 48.5 / 55.5 / 42.5 |  [lowdata] |
| Cam Skattebo (RB, RB1) | NYG v WAS (Sun 13:00) | 56.4 | 51 | 31.8 | 41.5: 63% / 46.5: 56% / 51.5: 49% / 56.5: 43% / 61.5: 37% | 38.5 / 32.5 / 44.5 | 65.5 / 75.5 / 57.5 |  [lowdata] |
| Najee Harris (RB, RB2) | NYG v WAS (Sun 13:00) | 43.4 | 39 | 24.7 | 29.5: 67% / 34.5: 58% / 39.5: 49% / 44.5: 41% / 49.5: 34% | 29.5 / 24.5 / 34.5 | 50.5 / 57.5 / 44.5 |  [lowdata] |
| Breece Hall (RB, RB1) | NYJ v CLE (Sun 13:00) | 60.1 | 54 | 33.8 | 44.5: 62% / 49.5: 56% / 54.5: 49% / 59.5: 43% / 64.5: 38% | 40.5 / 34.5 / 47.5 | 69.5 / 79.5 / 61.5 |  [lowdata] |
| Braelon Allen (RB, RB2) | NYJ v CLE (Sun 13:00) | 42.0 | 38 | 23.9 | 28.5: 67% / 33.5: 58% / 38.5: 49% / 43.5: 40% / 48.5: 33% | 28.5 / 23.5 / 32.5 | 48.5 / 56.5 / 42.5 |  [lowdata] |
| Jaylen Warren (RB, RB1) | PIT v IND (Sun 13:00) | 71.9 | 65 | 40.3 | 55.5: 60% / 60.5: 54% / 65.5: 49% / 70.5: 44% / 75.5: 39% | 49.5 / 41.5 / 56.5 | 82.5 / 95.5 / 73.5 |  [lowdata] |
| Rico Dowdle (RB, RB2) | PIT v IND (Sun 13:00) | 47.1 | 42 | 26.7 | 32.5: 66% / 37.5: 58% / 42.5: 50% / 47.5: 42% / 52.5: 35% | 31.5 / 26.5 / 36.5 | 54.5 / 62.5 / 48.5 |  [lowdata] |
| Tony Pollard (RB, RB1) | TEN v HOU (Sun 13:00) | 52.9 | 48 | 29.9 | 38.5: 63% / 43.5: 56% / 48.5: 49% / 53.5: 42% / 58.5: 36% | 35.5 / 29.5 / 41.5 | 61.5 / 70.5 / 53.5 |  [lowdata] |
| Tyjae Spears (RB, RB2) | TEN v HOU (Sun 13:00) | 29.2 | 26 | 16.9 | 16.5: 76% / 21.5: 62% / 26.5: 49% / 31.5: 38% / 36.5: 28% | 19.5 / 16.5 / 22.5 | 34.5 / 39.5 / 30.5 |  [lowdata] |
| Jacory Croskey-Merritt (RB, RB1) | WAS v NYG (Sun 13:00) | 51.2 | 46 | 28.9 | 36.5: 65% / 41.5: 57% / 46.5: 49% / 51.5: 42% / 56.5: 36% | 34.5 / 28.5 / 40.5 | 59.5 / 68.5 / 52.5 |  [lowdata] |
| Rachaad White (RB, RB2) | WAS v NYG (Sun 13:00) | 45.7 | 41 | 25.9 | 31.5: 66% / 36.5: 58% / 41.5: 49% / 46.5: 42% / 51.5: 35% | 30.5 / 25.5 / 35.5 | 53.5 / 60.5 / 46.5 |  [lowdata] |
| J.K. Dobbins (RB, RB1) | DEN v LAC (Sun 16:05) | 57.5 | 52 | 32.4 | 42.5: 63% / 47.5: 56% / 52.5: 49% / 57.5: 43% / 62.5: 37% | 39.5 / 32.5 / 45.5 | 66.5 / 76.5 / 58.5 |  [lowdata] |
| RJ Harvey (RB, RB2) | DEN v LAC (Sun 16:05) | 41.5 | 37 | 23.6 | 27.5: 69% / 32.5: 59% / 37.5: 50% / 42.5: 41% / 47.5: 34% | 27.5 / 23.5 / 32.5 | 48.5 / 55.5 / 42.5 |  [lowdata] |
| Omarion Hampton (RB, RB1) | LAC v DEN (Sun 16:05) | 55.2 | 50 | 31.2 | 40.5: 63% / 45.5: 56% / 50.5: 49% / 55.5: 42% / 60.5: 36% | 37.5 / 31.5 / 43.5 | 63.5 / 73.5 / 56.5 |  [lowdata] |
| Keaton Mitchell (RB, RB2) | LAC v DEN (Sun 16:05) | 40.0 | 36 | 22.8 | 26.5: 69% / 31.5: 58% / 36.5: 49% / 41.5: 40% / 46.5: 33% | 26.5 / 22.5 / 31.5 | 46.5 / 53.5 / 40.5 |  [lowdata] |
| Jeremiyah Love (RB, RB1) | ARI v DET (Sun 16:25) | 60.5 | 54 | 34.0 | 44.5: 63% / 49.5: 56% / 54.5: 50% / 59.5: 44% / 64.5: 38% | 41.5 / 34.5 / 47.5 | 69.5 / 80.5 / 61.5 |  [lowdata] |
| Tyler Allgeier (RB, RB2) | ARI v DET (Sun 16:25) | 41.3 | 37 | 23.5 | 27.5: 68% / 32.5: 59% / 37.5: 49% / 42.5: 41% / 47.5: 33% | 27.5 / 23.5 / 32.5 | 47.5 / 55.5 / 42.5 |  [lowdata] |
| Jahmyr Gibbs (RB, RB1) | DET v ARI (Sun 16:25) | 78.6 | 71 | 44.0 | 61.5: 59% / 66.5: 54% / 71.5: 49% / 76.5: 45% / 81.5: 40% | 53.5 / 45.5 / 62.5 | 90.5 / 104.5 / 79.5 |  [lowdata] |
| Sione Vaki (RB, RB2) | DET v ARI (Sun 16:25) | 32.2 | 29 | 18.5 | 19.5: 73% / 24.5: 60% / 29.5: 48% / 34.5: 38% / 39.5: 29% | 21.5 / 17.5 / 24.5 | 37.5 / 43.5 / 32.5 |  [lowdata] |
| Emanuel Wilson (RB, RB1) | SEA v SF (Sun 16:25) | 53.9 | 48 | 30.5 | 38.5: 65% / 43.5: 57% / 48.5: 50% / 53.5: 43% / 58.5: 37% | 36.5 / 30.5 / 42.5 | 62.5 / 71.5 / 54.5 |  [lowdata] |
| Jadarian Price (RB, RB2) | SEA v SF (Sun 16:25) | 52.5 | 47 | 29.7 | 37.5: 65% / 42.5: 57% / 47.5: 50% / 52.5: 43% / 57.5: 36% | 35.5 / 29.5 / 41.5 | 60.5 / 69.5 / 53.5 |  [lowdata] |
| Christian McCaffrey (RB, RB1) | SF v SEA (Sun 16:25) | 58.8 | 53 | 33.1 | 43.5: 63% / 48.5: 56% / 53.5: 49% / 58.5: 43% / 63.5: 37% | 39.5 / 33.5 / 46.5 | 68.5 / 78.5 / 59.5 |  [lowdata] |
| Kaelon Black (RB, RB2) | SF v SEA (Sun 16:25) | 41.2 | 37 | 23.5 | 27.5: 68% / 32.5: 58% / 37.5: 49% / 42.5: 41% / 47.5: 33% | 27.5 / 23.5 / 32.5 | 47.5 / 55.5 / 42.5 |  [lowdata] |
| Bijan Robinson (RB, RB1) | ATL v BAL (Sun 20:20) | 92.8 | 84 | 51.8 | 74.5: 58% / 79.5: 53% / 84.5: 49% / 89.5: 45% / 94.5: 41% | 63.5 / 53.5 / 73.5 | 106.5 / 122.5 / 94.5 |  [lowdata] |
| Brian Robinson (RB, RB2) | ATL v BAL (Sun 20:20) | 47.1 | 42 | 26.7 | 32.5: 66% / 37.5: 58% / 42.5: 50% / 47.5: 42% / 52.5: 35% | 31.5 / 26.5 / 36.5 | 54.5 / 62.5 / 48.5 |  [lowdata] |
| Derrick Henry (RB, RB1) | BAL v ATL (Sun 20:20) | 78.6 | 71 | 44.0 | 61.5: 59% / 66.5: 54% / 71.5: 49% / 76.5: 45% / 81.5: 40% | 53.5 / 45.5 / 62.5 | 90.5 / 104.5 / 79.5 |  [lowdata] |
| Justice Hill (RB, RB2) | BAL v ATL (Sun 20:20) | 29.0 | 26 | 16.8 | 16.5: 75% / 21.5: 62% / 26.5: 49% / 31.5: 37% / 36.5: 28% | 19.5 / 15.5 / 22.5 | 33.5 / 39.5 / 29.5 |  [lowdata] |

### Receiving yards (top-2 WR/TE; 3rd = next up)

| Player | Game (day, kick ET) | Mean | Med | SD | P(over) at lines | More <= (3pk/2pk/-110) | Less >= (3pk/2pk/-110) | Status |
|---|---|---|---|---|---|---|---|---|
| Keon Coleman (WR, Next) | BUF v LA (Mon 20:15) | 44.3 | 39 | 27.9 | 29.5: 65% / 34.5: 57% / 39.5: 49% / 44.5: 42% / 49.5: 35% | 28.5 / 22.5 / 33.5 | 51.5 / 60.5 / 44.5 |  |
| DJ Moore (WR, Top2) | BUF v LA (Mon 20:15) | 44.7 | 39 | 28.2 | 29.5: 66% / 34.5: 57% / 39.5: 49% / 44.5: 42% / 49.5: 36% | 28.5 / 22.5 / 33.5 | 51.5 / 60.5 / 45.5 |  |
| Khalil Shakir (WR, Top2) | BUF v LA (Mon 20:15) | 50.0 | 44 | 31.4 | 34.5: 63% / 39.5: 56% / 44.5: 49% / 49.5: 42% / 54.5: 37% | 31.5 / 25.5 / 37.5 | 58.5 / 67.5 / 50.5 |  |
| Tyler Higbee (TE, Next) | LA v BUF (Mon 20:15) | 40.3 | 35 | 25.5 | 25.5: 68% / 30.5: 58% / 35.5: 49% / 40.5: 42% / 45.5: 34% | 25.5 / 20.5 / 30.5 | 46.5 / 54.5 / 40.5 |  |
| Davante Adams (WR, Top2) | LA v BUF (Mon 20:15) | 69.8 | 61 | 43.6 | 51.5: 60% / 56.5: 55% / 61.5: 50% / 66.5: 45% / 71.5: 40% | 44.5 / 36.5 / 52.5 | 80.5 / 94.5 / 70.5 |  |
| Puka Nacua (WR, Top2) | LA v BUF (Mon 20:15) | 100.3 | 88 | 62.3 | 78.5: 57% / 83.5: 53% / 88.5: 50% / 93.5: 46% / 98.5: 43% | 64.5 / 52.5 / 76.5 | 115.5 / 135.5 / 100.5 |  |
| Brenton Strange (TE, Next) | JAX v PHI (Sun 09:30) | 39.9 | 35 | 25.2 | 25.5: 67% / 30.5: 58% / 35.5: 49% / 40.5: 41% / 45.5: 34% | 25.5 / 20.5 / 29.5 | 46.5 / 54.5 / 40.5 |  |
| Jakobi Meyers (WR, Top2) | JAX v PHI (Sun 09:30) | 46.6 | 41 | 29.3 | 31.5: 64% / 36.5: 56% / 41.5: 49% / 46.5: 42% / 51.5: 36% | 29.5 / 24.5 / 35.5 | 54.5 / 63.5 / 46.5 |  |
| Parker Washington (WR, Top2) | JAX v PHI (Sun 09:30) | 53.9 | 47 | 33.9 | 37.5: 63% / 42.5: 56% / 47.5: 50% / 52.5: 44% / 57.5: 38% | 34.5 / 27.5 / 40.5 | 62.5 / 73.5 / 54.5 |  |
| Dontayvion Wicks (WR, Next) | PHI v JAX (Sun 09:30) | 34.0 | 30 | 21.6 | 20.5: 70% / 25.5: 59% / 30.5: 48% / 35.5: 39% / 40.5: 31% | 21.5 / 17.5 / 25.5 | 39.5 / 46.5 / 34.5 |  |
| Dallas Goedert (TE, Top2) | PHI v JAX (Sun 09:30) | 39.4 | 34 | 24.9 | 24.5: 68% / 29.5: 59% / 34.5: 50% / 39.5: 42% / 44.5: 34% | 24.5 / 20.5 / 29.5 | 45.5 / 53.5 / 39.5 | Back from MCL sprain, no designation |
| Zach Ertz (TE, Top2) | PHI v JAX (Sun 09:30) | 35.3 | 31 | 22.4 | 21.5: 69% / 26.5: 59% / 31.5: 49% / 36.5: 40% / 41.5: 32% | 22.5 / 17.5 / 26.5 | 41.5 / 48.5 / 35.5 |  |
| Colston Loveland (TE, Next) | CHI v GB (Sun 13:00) | 42.1 | 37 | 26.6 | 27.5: 66% / 32.5: 57% / 37.5: 49% / 42.5: 41% / 47.5: 34% | 26.5 / 21.5 / 31.5 | 48.5 / 57.5 / 42.5 |  |
| Luther Burden III (WR, Top2) | CHI v GB (Sun 13:00) | 54.6 | 48 | 34.3 | 38.5: 62% / 43.5: 56% / 48.5: 49% / 53.5: 43% / 58.5: 38% | 34.5 / 28.5 / 41.5 | 63.5 / 73.5 / 54.5 |  |
| Rome Odunze (WR, Top2) | CHI v GB (Sun 13:00) | 50.3 | 44 | 31.6 | 34.5: 64% / 39.5: 56% / 44.5: 49% / 49.5: 43% / 54.5: 37% | 31.5 / 26.5 / 37.5 | 58.5 / 68.5 / 50.5 |  |
| Dohnte Meyers (WR, Next) | CIN v MIA (Sun 13:00) | 39.9 | 35 | 25.2 | 25.5: 67% / 30.5: 58% / 35.5: 49% / 40.5: 41% / 45.5: 34% | 25.5 / 20.5 / 29.5 | 46.5 / 54.5 / 40.5 |  [lowdata] |
| Ja'Marr Chase (WR, Top2) | CIN v MIA (Sun 13:00) | 75.3 | 66 | 46.9 | 56.5: 59% / 61.5: 54% / 66.5: 49% / 71.5: 45% / 76.5: 41% | 48.5 / 39.5 / 57.5 | 87.5 / 101.5 / 75.5 | QUESTIONABLE/limited (concussion in Wk4) |
| Tee Higgins (WR, Top2) | CIN v MIA (Sun 13:00) | 69.3 | 61 | 43.3 | 51.5: 60% / 56.5: 54% / 61.5: 49% / 66.5: 44% / 71.5: 40% | 44.5 / 36.5 / 52.5 | 80.5 / 93.5 / 69.5 | QUESTIONABLE/limited (adductor) |
| Denzel Boston (WR, Next) | CLE v NYJ (Sun 13:00) | 55.0 | 48 | 34.5 | 38.5: 63% / 43.5: 56% / 48.5: 50% / 53.5: 44% / 58.5: 38% | 35.5 / 28.5 / 41.5 | 63.5 / 74.5 / 55.5 |  [lowdata] |
| Harold Fannin Jr. (TE, Top2) | CLE v NYJ (Sun 13:00) | 40.5 | 35 | 25.6 | 25.5: 68% / 30.5: 59% / 35.5: 50% / 40.5: 42% / 45.5: 35% | 25.5 / 20.5 / 30.5 | 47.5 / 55.5 / 40.5 |  |
| KC Concepcion (WR, Top2) | CLE v NYJ (Sun 13:00) | 44.9 | 39 | 28.3 | 29.5: 66% / 34.5: 57% / 39.5: 50% / 44.5: 42% / 49.5: 36% | 28.5 / 23.5 / 33.5 | 52.5 / 60.5 / 45.5 |  [lowdata] |
| Tucker Kraft (TE, Next) | GB v CHI (Sun 13:00) | 47.2 | 41 | 29.7 | 31.5: 65% / 36.5: 57% / 41.5: 50% / 46.5: 43% / 51.5: 37% | 29.5 / 24.5 / 35.5 | 54.5 / 64.5 / 47.5 |  |
| Christian Watson (WR, Top2) | GB v CHI (Sun 13:00) | 63.8 | 56 | 39.9 | 46.5: 61% / 51.5: 55% / 56.5: 49% / 61.5: 44% / 66.5: 39% | 40.5 / 33.5 / 48.5 | 73.5 / 86.5 / 64.5 |  |
| Matthew Golden (WR, Top2) | GB v CHI (Sun 13:00) | 41.8 | 37 | 26.4 | 27.5: 66% / 32.5: 57% / 37.5: 48% / 42.5: 41% / 47.5: 34% | 26.5 / 21.5 / 31.5 | 48.5 / 56.5 / 42.5 |  |
| Xavier Hutchinson (WR, Next) | HOU v TEN (Sun 13:00) | 32.0 | 28 | 20.4 | 18.5: 71% / 23.5: 60% / 28.5: 49% / 33.5: 39% / 38.5: 31% | 19.5 / 16.5 / 23.5 | 37.5 / 43.5 / 32.5 |  |
| Dalton Schultz (TE, Top2) | HOU v TEN (Sun 13:00) | 44.1 | 39 | 27.8 | 29.5: 65% / 34.5: 56% / 39.5: 49% / 44.5: 41% / 49.5: 35% | 27.5 / 22.5 / 33.5 | 51.5 / 59.5 / 44.5 |  |
| Nico Collins (WR, Top2) | HOU v TEN (Sun 13:00) | 73.2 | 64 | 45.7 | 54.5: 59% / 59.5: 54% / 64.5: 50% / 69.5: 45% / 74.5: 41% | 46.5 / 38.5 / 55.5 | 84.5 / 98.5 / 73.5 |  |
| Josh Downs (WR, Next) | IND v PIT (Sun 13:00) | 43.3 | 38 | 27.4 | 28.5: 66% / 33.5: 57% / 38.5: 49% / 43.5: 42% / 48.5: 35% | 27.5 / 22.5 / 32.5 | 50.5 / 58.5 / 43.5 |  |
| Keenan Allen (WR, Top2) | IND v PIT (Sun 13:00) | 46.1 | 40 | 29.0 | 30.5: 65% / 35.5: 57% / 40.5: 50% / 45.5: 43% / 50.5: 36% | 29.5 / 23.5 / 34.5 | 53.5 / 62.5 / 46.5 |  |
| Tyler Warren (TE, Top2) | IND v PIT (Sun 13:00) | 40.1 | 35 | 25.4 | 25.5: 67% / 30.5: 58% / 35.5: 49% / 40.5: 41% / 45.5: 34% | 25.5 / 20.5 / 30.5 | 46.5 / 54.5 / 40.5 |  |
| Michael Mayer (TE, Next) | LV v NE (Sun 13:00) | 32.9 | 29 | 21.0 | 19.5: 70% / 24.5: 59% / 29.5: 48% / 34.5: 39% / 39.5: 31% | 20.5 / 16.5 / 24.5 | 38.5 / 44.5 / 33.5 |  |
| Brock Bowers (TE, Top2) | LV v NE (Sun 13:00) | 62.0 | 54 | 38.8 | 44.5: 61% / 49.5: 55% / 54.5: 50% / 59.5: 44% / 64.5: 39% | 39.5 / 32.5 / 46.5 | 71.5 / 83.5 / 62.5 |  |
| Tre Tucker (WR, Top2) | LV v NE (Sun 13:00) | 41.2 | 36 | 26.1 | 26.5: 67% / 31.5: 58% / 36.5: 49% / 41.5: 41% / 46.5: 35% | 26.5 / 21.5 / 30.5 | 48.5 / 56.5 / 41.5 |  |
| Greg Dulcich (TE, Next) | MIA v CIN (Sun 13:00) | 34.2 | 30 | 21.8 | 20.5: 70% / 25.5: 59% / 30.5: 49% / 35.5: 40% / 40.5: 32% | 21.5 / 17.5 / 25.5 | 39.5 / 46.5 / 34.5 |  |
| Caleb Douglas (WR, Top2) | MIA v CIN (Sun 13:00) | 47.9 | 42 | 30.2 | 32.5: 64% / 37.5: 56% / 42.5: 49% / 47.5: 42% / 52.5: 36% | 30.5 / 24.5 / 36.5 | 55.5 / 65.5 / 48.5 |  [lowdata] |
| Malik Washington (WR, Top2) | MIA v CIN (Sun 13:00) | 36.7 | 32 | 23.3 | 22.5: 69% / 27.5: 59% / 32.5: 49% / 37.5: 40% / 42.5: 33% | 23.5 / 18.5 / 27.5 | 42.5 / 49.5 / 37.5 |  |
| Jordan Addison (WR, Next) | MIN v NO (Sun 13:00) | 40.7 | 36 | 25.8 | 26.5: 66% / 31.5: 57% / 36.5: 49% / 41.5: 41% / 46.5: 34% | 25.5 / 20.5 / 30.5 | 47.5 / 55.5 / 41.5 |  |
| Justin Jefferson (WR, Top2) | MIN v NO (Sun 13:00) | 59.3 | 52 | 37.2 | 42.5: 61% / 47.5: 55% / 52.5: 49% / 57.5: 44% / 62.5: 39% | 37.5 / 30.5 / 44.5 | 68.5 / 80.5 / 59.5 |  |
| T.J. Hockenson (TE, Top2) | MIN v NO (Sun 13:00) | 39.0 | 34 | 24.7 | 24.5: 68% / 29.5: 58% / 34.5: 49% / 39.5: 41% / 44.5: 34% | 24.5 / 19.5 / 29.5 | 45.5 / 53.5 / 39.5 |  |
| Hunter Henry (TE, Next) | NE v LV (Sun 13:00) | 41.9 | 37 | 26.5 | 27.5: 66% / 32.5: 57% / 37.5: 49% / 42.5: 41% / 47.5: 34% | 26.5 / 21.5 / 31.5 | 48.5 / 56.5 / 42.5 |  |
| Mack Hollins (WR, Top2) | NE v LV (Sun 13:00) | 43.4 | 38 | 27.4 | 28.5: 66% / 33.5: 57% / 38.5: 49% / 43.5: 42% / 48.5: 35% | 27.5 / 22.5 / 32.5 | 50.5 / 58.5 / 43.5 |  |
| Romeo Doubs (WR, Top2) | NE v LV (Sun 13:00) | 46.2 | 40 | 29.1 | 30.5: 66% / 35.5: 58% / 40.5: 50% / 45.5: 43% / 50.5: 36% | 29.5 / 23.5 / 34.5 | 53.5 / 62.5 / 46.5 |  |
| Juwan Johnson (TE, Next) | NO v MIN (Sun 13:00) | 47.7 | 42 | 30.0 | 32.5: 64% / 37.5: 56% / 42.5: 49% / 47.5: 42% / 52.5: 36% | 30.5 / 24.5 / 35.5 | 55.5 / 64.5 / 48.5 |  |
| Chris Olave (WR, Top2) | NO v MIN (Sun 13:00) | 76.5 | 67 | 47.7 | 57.5: 59% / 62.5: 54% / 67.5: 50% / 72.5: 45% / 77.5: 41% | 49.5 / 40.5 / 58.5 | 88.5 / 103.5 / 76.5 |  |
| Devaughn Vele (WR, Top2) | NO v MIN (Sun 13:00) | 40.3 | 35 | 25.5 | 25.5: 68% / 30.5: 58% / 35.5: 49% / 40.5: 41% / 45.5: 34% | 25.5 / 20.5 / 30.5 | 46.5 / 54.5 / 40.5 |  |
| Theo Johnson (TE, Next) | NYG v WAS (Sun 13:00) | 32.0 | 28 | 20.4 | 18.5: 71% / 23.5: 60% / 28.5: 49% / 33.5: 39% / 38.5: 31% | 19.5 / 16.5 / 23.5 | 37.5 / 43.5 / 32.5 |  |
| Isaiah Likely (TE, Top2) | NYG v WAS (Sun 13:00) | 35.9 | 31 | 22.8 | 21.5: 70% / 26.5: 60% / 31.5: 50% / 36.5: 41% / 41.5: 33% | 22.5 / 18.5 / 26.5 | 41.5 / 49.5 / 36.5 |  |
| Malik Nabers (WR, Top2) | NYG v WAS (Sun 13:00) | 64.5 | 56 | 40.3 | 46.5: 61% / 51.5: 55% / 56.5: 50% / 61.5: 45% / 66.5: 40% | 41.5 / 33.5 / 48.5 | 74.5 / 87.5 / 64.5 |  |
| Mason Taylor (TE, Next) | NYJ v CLE (Sun 13:00) | 29.0 | 25 | 18.5 | 15.5: 75% / 20.5: 62% / 25.5: 49% / 30.5: 39% / 35.5: 30% | 18.5 / 14.5 / 21.5 | 33.5 / 39.5 / 29.5 |  |
| Adonai Mitchell (WR, Top2) | NYJ v CLE (Sun 13:00) | 34.3 | 30 | 21.8 | 20.5: 70% / 25.5: 59% / 30.5: 49% / 35.5: 40% / 40.5: 32% | 21.5 / 17.5 / 25.5 | 40.5 / 46.5 / 34.5 |  |
| Garrett Wilson (WR, Top2) | NYJ v CLE (Sun 13:00) | 57.2 | 50 | 35.9 | 40.5: 62% / 45.5: 56% / 50.5: 50% / 55.5: 44% / 60.5: 38% | 36.5 / 29.5 / 43.5 | 66.5 / 77.5 / 57.5 |  |
| Roman Wilson (WR, Next) | PIT v IND (Sun 13:00) | 36.8 | 32 | 23.3 | 22.5: 69% / 27.5: 59% / 32.5: 49% / 37.5: 41% / 42.5: 33% | 23.5 / 18.5 / 27.5 | 42.5 / 50.5 / 37.5 |  |
| DK Metcalf (WR, Top2) | PIT v IND (Sun 13:00) | 60.0 | 52 | 37.5 | 42.5: 62% / 47.5: 56% / 52.5: 50% / 57.5: 44% / 62.5: 39% | 38.5 / 31.5 / 45.5 | 69.5 / 81.5 / 60.5 |  |
| Michael Pittman (WR, Top2) | PIT v IND (Sun 13:00) | 42.4 | 37 | 26.8 | 27.5: 66% / 32.5: 58% / 37.5: 49% / 42.5: 42% / 47.5: 35% | 26.5 / 21.5 / 31.5 | 49.5 / 57.5 / 42.5 |  |
| Elic Ayomanor (WR, Next) | TEN v HOU (Sun 13:00) | 31.3 | 27 | 20.0 | 17.5: 73% / 22.5: 61% / 27.5: 50% / 32.5: 40% / 37.5: 31% | 19.5 / 15.5 / 23.5 | 36.5 / 42.5 / 31.5 |  |
| Carnell Tate (WR, Top2) | TEN v HOU (Sun 13:00) | 60.9 | 53 | 38.1 | 43.5: 62% / 48.5: 56% / 53.5: 50% / 58.5: 44% / 63.5: 39% | 38.5 / 31.5 / 46.5 | 70.5 / 82.5 / 61.5 |  [lowdata] |
| Wan'Dale Robinson (WR, Top2) | TEN v HOU (Sun 13:00) | 44.5 | 39 | 28.1 | 29.5: 65% / 34.5: 57% / 39.5: 49% / 44.5: 42% / 49.5: 35% | 28.5 / 22.5 / 33.5 | 51.5 / 60.5 / 44.5 |  |
| Chig Okonkwo (TE, Next) | WAS v NYG (Sun 13:00) | 31.3 | 27 | 19.9 | 17.5: 73% / 22.5: 61% / 27.5: 50% / 32.5: 39% / 37.5: 31% | 19.5 / 15.5 / 23.5 | 36.5 / 42.5 / 31.5 |  |
| Antonio Williams (WR, Top2) | WAS v NYG (Sun 13:00) | 35.6 | 31 | 22.6 | 21.5: 70% / 26.5: 59% / 31.5: 49% / 36.5: 40% / 41.5: 33% | 22.5 / 18.5 / 26.5 | 41.5 / 48.5 / 35.5 |  [lowdata] |
| Terry McLaurin (WR, Top2) | WAS v NYG (Sun 13:00) | 52.4 | 46 | 32.9 | 36.5: 63% / 41.5: 56% / 46.5: 49% / 51.5: 43% / 56.5: 37% | 33.5 / 27.5 / 39.5 | 60.5 / 71.5 / 52.5 | Likely to play (hamstring, returned to practice Fri) |
| Evan Engram (TE, Next) | DEN v LAC (Sun 16:05) | 29.8 | 26 | 19.0 | 16.5: 73% / 21.5: 61% / 26.5: 49% / 31.5: 38% / 36.5: 30% | 18.5 / 14.5 / 22.5 | 34.5 / 40.5 / 30.5 |  |
| Courtland Sutton (WR, Top2) | DEN v LAC (Sun 16:05) | 47.7 | 42 | 30.0 | 32.5: 64% / 37.5: 56% / 42.5: 49% / 47.5: 42% / 52.5: 36% | 30.5 / 24.5 / 35.5 | 55.5 / 64.5 / 47.5 |  |
| Jaylen Waddle (WR, Top2) | DEN v LAC (Sun 16:05) | 47.3 | 41 | 29.8 | 31.5: 65% / 36.5: 57% / 41.5: 50% / 46.5: 43% / 51.5: 37% | 29.5 / 24.5 / 35.5 | 54.5 / 64.5 / 47.5 |  |
| Tre Harris (WR, Next) | LAC v DEN (Sun 16:05) | 35.4 | 31 | 22.5 | 21.5: 69% / 26.5: 59% / 31.5: 49% / 36.5: 40% / 41.5: 32% | 22.5 / 17.5 / 26.5 | 41.5 / 48.5 / 35.5 |  |
| Ladd McConkey (WR, Top2) | LAC v DEN (Sun 16:05) | 45.6 | 40 | 28.8 | 30.5: 65% / 35.5: 57% / 40.5: 49% / 45.5: 42% / 50.5: 36% | 28.5 / 23.5 / 34.5 | 53.5 / 61.5 / 45.5 |  |
| Quentin Johnston (WR, Top2) | LAC v DEN (Sun 16:05) | 46.4 | 41 | 29.2 | 31.5: 64% / 36.5: 56% / 41.5: 49% / 46.5: 42% / 51.5: 35% | 29.5 / 23.5 / 34.5 | 53.5 / 63.5 / 46.5 |  |
| Marvin Harrison Jr. (WR, Next) | ARI v DET (Sun 16:25) | 46.8 | 41 | 29.5 | 31.5: 65% / 36.5: 57% / 41.5: 49% / 46.5: 42% / 51.5: 36% | 29.5 / 24.5 / 35.5 | 54.5 / 63.5 / 47.5 |  |
| Michael Wilson (WR, Top2) | ARI v DET (Sun 16:25) | 69.4 | 61 | 43.3 | 51.5: 60% / 56.5: 54% / 61.5: 49% / 66.5: 44% / 71.5: 40% | 44.5 / 36.5 / 52.5 | 80.5 / 93.5 / 69.5 |  |
| Trey McBride (TE, Top2) | ARI v DET (Sun 16:25) | 77.3 | 68 | 48.2 | 58.5: 59% / 63.5: 54% / 68.5: 49% / 73.5: 45% / 78.5: 41% | 49.5 / 40.5 / 58.5 | 89.5 / 104.5 / 77.5 |  |
| Jameson Williams (WR, Next) | DET v ARI (Sun 16:25) | 67.6 | 59 | 42.2 | 49.5: 60% / 54.5: 55% / 59.5: 50% / 64.5: 45% / 69.5: 40% | 43.5 / 35.5 / 51.5 | 78.5 / 91.5 / 67.5 |  |
| Amon-Ra St. Brown (WR, Top2) | DET v ARI (Sun 16:25) | 85.7 | 75 | 53.3 | 65.5: 58% / 70.5: 54% / 75.5: 50% / 80.5: 46% / 85.5: 42% | 55.5 / 45.5 / 65.5 | 99.5 / 115.5 / 85.5 |  |
| Sam LaPorta (TE, Top2) | DET v ARI (Sun 16:25) | 58.2 | 51 | 36.5 | 41.5: 62% / 46.5: 55% / 51.5: 49% / 56.5: 44% / 61.5: 38% | 37.5 / 30.5 / 43.5 | 67.5 / 78.5 / 58.5 |  |
| Rashid Shaheed (WR, Next) | SEA v SF (Sun 16:25) | 33.2 | 29 | 21.2 | 19.5: 71% / 24.5: 60% / 29.5: 49% / 34.5: 40% / 39.5: 31% | 20.5 / 16.5 / 24.5 | 38.5 / 45.5 / 33.5 |  |
| AJ Barner (TE, Top2) | SEA v SF (Sun 16:25) | 31.8 | 28 | 20.3 | 18.5: 71% / 23.5: 60% / 28.5: 49% / 33.5: 39% / 38.5: 30% | 19.5 / 16.5 / 23.5 | 37.5 / 43.5 / 32.5 |  |
| Jaxon Smith-Njigba (WR, Top2) | SEA v SF (Sun 16:25) | 92.3 | 81 | 57.4 | 71.5: 57% / 76.5: 53% / 81.5: 50% / 86.5: 46% / 91.5: 42% | 59.5 / 48.5 / 70.5 | 106.5 / 124.5 / 92.5 |  |
| Deebo Samuel Sr. (WR, Next) | SF v SEA (Sun 16:25) | 42.1 | 37 | 26.6 | 27.5: 66% / 32.5: 57% / 37.5: 49% / 42.5: 41% / 47.5: 35% | 26.5 / 21.5 / 31.5 | 49.5 / 57.5 / 42.5 |  |
| George Kittle (TE, Top2) | SF v SEA (Sun 16:25) | 56.9 | 50 | 35.7 | 40.5: 62% / 45.5: 55% / 50.5: 49% / 55.5: 43% / 60.5: 38% | 36.5 / 29.5 / 42.5 | 65.5 / 77.5 / 57.5 |  |
| Mike Evans (WR, Top2) | SF v SEA (Sun 16:25) | 55.2 | 48 | 34.6 | 38.5: 63% / 43.5: 56% / 48.5: 50% / 53.5: 44% / 58.5: 38% | 35.5 / 28.5 / 41.5 | 64.5 / 74.5 / 55.5 |  |
| Jahan Dotson (WR, Next) | ATL v BAL (Sun 20:20) | 26.2 | 23 | 16.8 | 13.5: 76% / 18.5: 62% / 23.5: 48% / 28.5: 37% / 33.5: 27% | 16.5 / 13.5 / 19.5 | 30.5 / 35.5 / 26.5 |  |
| Drake London (WR, Top2) | ATL v BAL (Sun 20:20) | 78.9 | 69 | 49.2 | 59.5: 59% / 64.5: 54% / 69.5: 50% / 74.5: 45% / 79.5: 41% | 50.5 / 41.5 / 59.5 | 91.5 / 106.5 / 79.5 |  |
| Kyle Pitts (TE, Top2) | ATL v BAL (Sun 20:20) | 43.1 | 38 | 27.2 | 28.5: 66% / 33.5: 57% / 38.5: 49% / 43.5: 41% / 48.5: 35% | 27.5 / 22.5 / 32.5 | 50.5 / 58.5 / 43.5 |  |
| Rashod Bateman (WR, Next) | BAL v ATL (Sun 20:20) | 33.5 | 29 | 21.3 | 19.5: 71% / 24.5: 60% / 29.5: 50% / 34.5: 40% / 39.5: 32% | 20.5 / 16.5 / 24.5 | 39.5 / 45.5 / 33.5 |  |
| Mark Andrews (TE, Top2) | BAL v ATL (Sun 20:20) | 34.1 | 30 | 21.7 | 20.5: 70% / 25.5: 59% / 30.5: 48% / 35.5: 39% / 40.5: 31% | 21.5 / 17.5 / 25.5 | 39.5 / 46.5 / 34.5 |  |
| Zay Flowers (WR, Top2) | BAL v ATL (Sun 20:20) | 78.1 | 68 | 48.7 | 58.5: 59% / 63.5: 54% / 68.5: 50% / 73.5: 46% / 78.5: 42% | 50.5 / 41.5 / 59.5 | 90.5 / 105.5 / 78.5 |  |

### Receptions (top-2 WR/TE; 3rd = next up)

| Player | Game (day, kick ET) | Mean | Med | SD | P(over) at lines | More <= (3pk/2pk/-110) | Less >= (3pk/2pk/-110) | Status |
|---|---|---|---|---|---|---|---|---|
| Keon Coleman (WR, Next) | BUF v LA (Mon 20:15) | 3.5 | 3 | 2.1 | 1.5: 84% / 2.5: 65% / 3.5: 45% / 4.5: 28% / 5.5: 16% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| DJ Moore (WR, Top2) | BUF v LA (Mon 20:15) | 3.3 | 3 | 2.0 | 1.5: 82% / 2.5: 62% / 3.5: 42% / 4.5: 25% / 5.5: 14% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 3.5 |  |
| Khalil Shakir (WR, Top2) | BUF v LA (Mon 20:15) | 4.7 | 4 | 2.4 | 2.5: 81% / 3.5: 65% / 4.5: 48% / 5.5: 33% / 6.5: 21% | 2.5 / 2.5 / 3.5 | 5.5 / 6.5 / 5.5 |  |
| Tyler Higbee (TE, Next) | LA v BUF (Mon 20:15) | 3.9 | 4 | 2.2 | 2.5: 72% / 3.5: 53% / 4.5: 35% / 5.5: 22% / 6.5: 12% | 2.5 / 1.5 / 2.5 | 5.5 / 5.5 / 4.5 |  |
| Davante Adams (WR, Top2) | LA v BUF (Mon 20:15) | 4.8 | 5 | 2.5 | 3.5: 67% / 4.5: 50% / 5.5: 35% / 6.5: 23% / 7.5: 14% | 3.5 / 2.5 / 3.5 | 6.5 / 6.5 / 5.5 |  |
| Puka Nacua (WR, Top2) | LA v BUF (Mon 20:15) | 7.2 | 7 | 3.2 | 5.5: 68% / 6.5: 55% / 7.5: 43% / 8.5: 31% / 9.5: 22% | 5.5 / 4.5 / 5.5 | 8.5 / 9.5 / 8.5 |  |
| Brenton Strange (TE, Next) | JAX v PHI (Sun 09:30) | 3.6 | 3 | 2.1 | 1.5: 84% / 2.5: 66% / 3.5: 46% / 4.5: 29% / 5.5: 17% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| Jakobi Meyers (WR, Top2) | JAX v PHI (Sun 09:30) | 3.9 | 4 | 2.2 | 2.5: 71% / 3.5: 52% / 4.5: 35% / 5.5: 21% / 6.5: 12% | 2.5 / 1.5 / 2.5 | 5.5 / 5.5 / 4.5 |  |
| Parker Washington (WR, Top2) | JAX v PHI (Sun 09:30) | 4.1 | 4 | 2.2 | 2.5: 74% / 3.5: 55% / 4.5: 38% / 5.5: 24% / 6.5: 14% | 2.5 / 1.5 / 2.5 | 5.5 / 5.5 / 4.5 |  |
| Dontayvion Wicks (WR, Next) | PHI v JAX (Sun 09:30) | 2.9 | 3 | 1.8 | 1.5: 75% / 2.5: 53% / 3.5: 32% / 4.5: 17% / 5.5: 9% | 1.5 / 0.5 / 1.5 | 3.5 / 4.5 / 3.5 |  |
| Dallas Goedert (TE, Top2) | PHI v JAX (Sun 09:30) | 3.5 | 3 | 2.0 | 1.5: 84% / 2.5: 65% / 3.5: 45% / 4.5: 28% / 5.5: 16% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 | Back from MCL sprain, no designation |
| Zach Ertz (TE, Top2) | PHI v JAX (Sun 09:30) | 3.4 | 3 | 2.0 | 1.5: 82% / 2.5: 63% / 3.5: 43% / 4.5: 26% / 5.5: 15% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| Colston Loveland (TE, Next) | CHI v GB (Sun 13:00) | 3.9 | 4 | 2.2 | 2.5: 72% / 3.5: 53% / 4.5: 36% / 5.5: 22% / 6.5: 12% | 2.5 / 1.5 / 2.5 | 5.5 / 5.5 / 4.5 |  |
| Luther Burden III (WR, Top2) | CHI v GB (Sun 13:00) | 4.6 | 4 | 2.4 | 2.5: 80% / 3.5: 64% / 4.5: 47% / 5.5: 32% / 6.5: 20% | 2.5 / 2.5 / 3.5 | 5.5 / 6.5 / 5.5 |  |
| Rome Odunze (WR, Top2) | CHI v GB (Sun 13:00) | 3.6 | 3 | 2.1 | 1.5: 85% / 2.5: 67% / 3.5: 47% / 4.5: 30% / 5.5: 17% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| Dohnte Meyers (WR, Next) | CIN v MIA (Sun 13:00) | 3.4 | 3 | 2.0 | 1.5: 83% / 2.5: 64% / 3.5: 44% / 4.5: 27% / 5.5: 15% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  [lowdata] |
| Ja'Marr Chase (WR, Top2) | CIN v MIA (Sun 13:00) | 6.1 | 6 | 2.9 | 4.5: 69% / 5.5: 55% / 6.5: 41% / 7.5: 29% / 8.5: 20% | 4.5 / 3.5 / 4.5 | 7.5 / 8.5 / 6.5 | QUESTIONABLE/limited (concussion in Wk4) |
| Tee Higgins (WR, Top2) | CIN v MIA (Sun 13:00) | 4.9 | 5 | 2.5 | 3.5: 69% / 4.5: 53% / 5.5: 37% / 6.5: 25% / 7.5: 15% | 3.5 / 2.5 / 3.5 | 6.5 / 7.5 / 5.5 | QUESTIONABLE/limited (adductor) |
| Denzel Boston (WR, Next) | CLE v NYJ (Sun 13:00) | 3.3 | 3 | 2.0 | 1.5: 82% / 2.5: 63% / 3.5: 42% / 4.5: 26% / 5.5: 14% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  [lowdata] |
| Harold Fannin Jr. (TE, Top2) | CLE v NYJ (Sun 13:00) | 4.0 | 4 | 2.2 | 2.5: 72% / 3.5: 54% / 4.5: 36% / 5.5: 22% / 6.5: 13% | 2.5 / 1.5 / 2.5 | 5.5 / 5.5 / 4.5 |  |
| KC Concepcion (WR, Top2) | CLE v NYJ (Sun 13:00) | 4.4 | 4 | 2.3 | 2.5: 78% / 3.5: 60% / 4.5: 43% / 5.5: 28% / 6.5: 17% | 2.5 / 2.5 / 3.5 | 5.5 / 6.5 / 5.5 |  [lowdata] |
| Tucker Kraft (TE, Next) | GB v CHI (Sun 13:00) | 3.8 | 4 | 2.2 | 2.5: 70% / 3.5: 51% / 4.5: 33% / 5.5: 20% / 6.5: 11% | 2.5 / 1.5 / 2.5 | 5.5 / 5.5 / 4.5 |  |
| Christian Watson (WR, Top2) | GB v CHI (Sun 13:00) | 4.3 | 4 | 2.3 | 2.5: 76% / 3.5: 59% / 4.5: 42% / 5.5: 27% / 6.5: 16% | 2.5 / 2.5 / 3.5 | 5.5 / 6.5 / 4.5 |  |
| Matthew Golden (WR, Top2) | GB v CHI (Sun 13:00) | 3.2 | 3 | 2.0 | 1.5: 80% / 2.5: 60% / 3.5: 40% / 4.5: 23% / 5.5: 12% | 1.5 / 1.5 / 2.5 | 4.5 / 4.5 / 3.5 |  |
| Xavier Hutchinson (WR, Next) | HOU v TEN (Sun 13:00) | 2.7 | 2 | 1.8 | 0.5: 92% / 1.5: 73% / 2.5: 49% / 3.5: 29% / 4.5: 15% | 1.5 / 0.5 / 1.5 | 3.5 / 4.5 / 3.5 |  |
| Dalton Schultz (TE, Top2) | HOU v TEN (Sun 13:00) | 4.2 | 4 | 2.3 | 2.5: 76% / 3.5: 58% / 4.5: 41% / 5.5: 26% / 6.5: 16% | 2.5 / 2.5 / 3.5 | 5.5 / 6.5 / 4.5 |  |
| Nico Collins (WR, Top2) | HOU v TEN (Sun 13:00) | 4.8 | 5 | 2.5 | 3.5: 67% / 4.5: 51% / 5.5: 36% / 6.5: 23% / 7.5: 14% | 3.5 / 2.5 / 3.5 | 6.5 / 6.5 / 5.5 |  |
| Josh Downs (WR, Next) | IND v PIT (Sun 13:00) | 3.8 | 4 | 2.2 | 2.5: 70% / 3.5: 51% / 4.5: 33% / 5.5: 20% / 6.5: 11% | 2.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| Keenan Allen (WR, Top2) | IND v PIT (Sun 13:00) | 4.5 | 4 | 2.4 | 2.5: 79% / 3.5: 63% / 4.5: 45% / 5.5: 30% / 6.5: 19% | 2.5 / 2.5 / 3.5 | 5.5 / 6.5 / 5.5 |  |
| Tyler Warren (TE, Top2) | IND v PIT (Sun 13:00) | 4.5 | 4 | 2.4 | 2.5: 80% / 3.5: 63% / 4.5: 46% / 5.5: 31% / 6.5: 20% | 2.5 / 2.5 / 3.5 | 5.5 / 6.5 / 5.5 |  |
| Michael Mayer (TE, Next) | LV v NE (Sun 13:00) | 3.8 | 4 | 2.2 | 2.5: 70% / 3.5: 51% / 4.5: 34% / 5.5: 20% / 6.5: 11% | 2.5 / 1.5 / 2.5 | 5.5 / 5.5 / 4.5 |  |
| Brock Bowers (TE, Top2) | LV v NE (Sun 13:00) | 5.7 | 5 | 2.8 | 3.5: 78% / 4.5: 63% / 5.5: 49% / 6.5: 35% / 7.5: 24% | 3.5 / 3.5 / 4.5 | 7.5 / 7.5 / 6.5 |  |
| Tre Tucker (WR, Top2) | LV v NE (Sun 13:00) | 3.5 | 3 | 2.0 | 1.5: 83% / 2.5: 65% / 3.5: 45% / 4.5: 28% / 5.5: 16% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| Greg Dulcich (TE, Next) | MIA v CIN (Sun 13:00) | 3.0 | 3 | 1.9 | 1.5: 78% / 2.5: 57% / 3.5: 36% / 4.5: 21% / 5.5: 11% | 1.5 / 1.5 / 1.5 | 4.5 / 4.5 / 3.5 |  |
| Caleb Douglas (WR, Top2) | MIA v CIN (Sun 13:00) | 3.5 | 3 | 2.1 | 1.5: 84% / 2.5: 66% / 3.5: 46% / 4.5: 29% / 5.5: 16% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  [lowdata] |
| Malik Washington (WR, Top2) | MIA v CIN (Sun 13:00) | 3.7 | 3 | 2.1 | 1.5: 86% / 2.5: 68% / 3.5: 49% / 4.5: 31% / 5.5: 18% | 2.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| Jordan Addison (WR, Next) | MIN v NO (Sun 13:00) | 2.9 | 3 | 1.9 | 1.5: 77% / 2.5: 54% / 3.5: 34% / 4.5: 19% / 5.5: 9% | 1.5 / 1.5 / 1.5 | 4.5 / 4.5 / 3.5 |  |
| Justin Jefferson (WR, Top2) | MIN v NO (Sun 13:00) | 4.5 | 4 | 2.4 | 2.5: 79% / 3.5: 63% / 4.5: 46% / 5.5: 31% / 6.5: 19% | 2.5 / 2.5 / 3.5 | 5.5 / 6.5 / 5.5 |  |
| T.J. Hockenson (TE, Top2) | MIN v NO (Sun 13:00) | 4.1 | 4 | 2.3 | 2.5: 75% / 3.5: 57% / 4.5: 39% / 5.5: 25% / 6.5: 14% | 2.5 / 1.5 / 2.5 | 5.5 / 6.5 / 4.5 |  |
| Hunter Henry (TE, Next) | NE v LV (Sun 13:00) | 3.5 | 3 | 2.1 | 1.5: 84% / 2.5: 66% / 3.5: 46% / 4.5: 29% / 5.5: 16% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| Mack Hollins (WR, Top2) | NE v LV (Sun 13:00) | 3.7 | 3 | 2.1 | 1.5: 86% / 2.5: 68% / 3.5: 49% / 4.5: 31% / 5.5: 18% | 2.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| Romeo Doubs (WR, Top2) | NE v LV (Sun 13:00) | 3.4 | 3 | 2.0 | 1.5: 83% / 2.5: 63% / 3.5: 43% / 4.5: 26% / 5.5: 15% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| Juwan Johnson (TE, Next) | NO v MIN (Sun 13:00) | 4.2 | 4 | 2.3 | 2.5: 76% / 3.5: 58% / 4.5: 41% / 5.5: 26% / 6.5: 15% | 2.5 / 1.5 / 3.5 | 5.5 / 6.5 / 4.5 |  |
| Chris Olave (WR, Top2) | NO v MIN (Sun 13:00) | 6.1 | 6 | 2.9 | 4.5: 69% / 5.5: 55% / 6.5: 41% / 7.5: 29% / 8.5: 19% | 4.5 / 3.5 / 4.5 | 7.5 / 8.5 / 6.5 |  |
| Devaughn Vele (WR, Top2) | NO v MIN (Sun 13:00) | 3.7 | 3 | 2.1 | 1.5: 86% / 2.5: 69% / 3.5: 49% / 4.5: 32% / 5.5: 19% | 2.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| Theo Johnson (TE, Next) | NYG v WAS (Sun 13:00) | 2.5 | 2 | 1.7 | 0.5: 90% / 1.5: 69% / 2.5: 45% / 3.5: 25% / 4.5: 12% | 1.5 / 0.5 / 1.5 | 3.5 / 4.5 / 3.5 |  |
| Isaiah Likely (TE, Top2) | NYG v WAS (Sun 13:00) | 3.7 | 3 | 2.1 | 1.5: 86% / 2.5: 68% / 3.5: 49% / 4.5: 31% / 5.5: 18% | 2.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| Malik Nabers (WR, Top2) | NYG v WAS (Sun 13:00) | 5.0 | 5 | 2.5 | 3.5: 69% / 4.5: 53% / 5.5: 38% / 6.5: 25% / 7.5: 16% | 3.5 / 2.5 / 3.5 | 6.5 / 7.5 / 5.5 |  |
| Mason Taylor (TE, Next) | NYJ v CLE (Sun 13:00) | 3.2 | 3 | 2.0 | 1.5: 80% / 2.5: 60% / 3.5: 39% / 4.5: 23% / 5.5: 12% | 1.5 / 1.5 / 2.5 | 4.5 / 4.5 / 3.5 |  |
| Adonai Mitchell (WR, Top2) | NYJ v CLE (Sun 13:00) | 3.0 | 3 | 1.9 | 1.5: 77% / 2.5: 55% / 3.5: 34% / 4.5: 19% / 5.5: 10% | 1.5 / 1.5 / 1.5 | 4.5 / 4.5 / 3.5 |  |
| Garrett Wilson (WR, Top2) | NYJ v CLE (Sun 13:00) | 4.9 | 5 | 2.5 | 3.5: 69% / 4.5: 53% / 5.5: 37% / 6.5: 25% / 7.5: 15% | 3.5 / 2.5 / 3.5 | 6.5 / 7.5 / 5.5 |  |
| Roman Wilson (WR, Next) | PIT v IND (Sun 13:00) | 2.8 | 3 | 1.8 | 1.5: 75% / 2.5: 52% / 3.5: 32% / 4.5: 17% / 5.5: 8% | 1.5 / 0.5 / 1.5 | 3.5 / 4.5 / 3.5 |  |
| DK Metcalf (WR, Top2) | PIT v IND (Sun 13:00) | 4.3 | 4 | 2.3 | 2.5: 77% / 3.5: 60% / 4.5: 42% / 5.5: 28% / 6.5: 17% | 2.5 / 2.5 / 3.5 | 5.5 / 6.5 / 5.5 |  |
| Michael Pittman (WR, Top2) | PIT v IND (Sun 13:00) | 3.5 | 3 | 2.1 | 1.5: 84% / 2.5: 66% / 3.5: 46% / 4.5: 29% / 5.5: 17% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| Elic Ayomanor (WR, Next) | TEN v HOU (Sun 13:00) | 2.3 | 2 | 1.6 | 0.5: 88% / 1.5: 64% / 2.5: 39% / 3.5: 20% / 4.5: 9% | 0.5 / 0.5 / 1.5 | 3.5 / 3.5 / 2.5 |  |
| Carnell Tate (WR, Top2) | TEN v HOU (Sun 13:00) | 5.0 | 5 | 2.5 | 3.5: 69% / 4.5: 53% / 5.5: 38% / 6.5: 25% / 7.5: 16% | 3.5 / 2.5 / 3.5 | 6.5 / 7.5 / 5.5 |  [lowdata] |
| Wan'Dale Robinson (WR, Top2) | TEN v HOU (Sun 13:00) | 4.4 | 4 | 2.3 | 2.5: 78% / 3.5: 61% / 4.5: 43% / 5.5: 28% / 6.5: 17% | 2.5 / 2.5 / 3.5 | 5.5 / 6.5 / 5.5 |  |
| Chig Okonkwo (TE, Next) | WAS v NYG (Sun 13:00) | 3.1 | 3 | 1.9 | 1.5: 79% / 2.5: 58% / 3.5: 38% / 4.5: 22% / 5.5: 11% | 1.5 / 1.5 / 2.5 | 4.5 / 4.5 / 3.5 |  |
| Antonio Williams (WR, Top2) | WAS v NYG (Sun 13:00) | 3.2 | 3 | 2.0 | 1.5: 81% / 2.5: 60% / 3.5: 40% / 4.5: 24% / 5.5: 13% | 1.5 / 1.5 / 2.5 | 4.5 / 4.5 / 3.5 |  [lowdata] |
| Terry McLaurin (WR, Top2) | WAS v NYG (Sun 13:00) | 3.7 | 3 | 2.1 | 1.5: 86% / 2.5: 69% / 3.5: 50% / 4.5: 32% / 5.5: 19% | 2.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 | Likely to play (hamstring, returned to practice Fri) |
| Evan Engram (TE, Next) | DEN v LAC (Sun 16:05) | 2.6 | 2 | 1.7 | 0.5: 91% / 1.5: 72% / 2.5: 48% / 3.5: 28% / 4.5: 14% | 1.5 / 0.5 / 1.5 | 3.5 / 4.5 / 3.5 |  |
| Courtland Sutton (WR, Top2) | DEN v LAC (Sun 16:05) | 3.6 | 3 | 2.1 | 1.5: 85% / 2.5: 67% / 3.5: 47% / 4.5: 30% / 5.5: 17% | 2.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| Jaylen Waddle (WR, Top2) | DEN v LAC (Sun 16:05) | 3.6 | 3 | 2.1 | 1.5: 85% / 2.5: 67% / 3.5: 47% / 4.5: 30% / 5.5: 17% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| Tre Harris (WR, Next) | LAC v DEN (Sun 16:05) | 2.9 | 3 | 1.8 | 1.5: 76% / 2.5: 54% / 3.5: 33% / 4.5: 18% / 5.5: 9% | 1.5 / 1.5 / 1.5 | 3.5 / 4.5 / 3.5 |  |
| Ladd McConkey (WR, Top2) | LAC v DEN (Sun 16:05) | 3.3 | 3 | 2.0 | 1.5: 81% / 2.5: 61% / 3.5: 40% / 4.5: 24% / 5.5: 13% | 1.5 / 1.5 / 2.5 | 4.5 / 4.5 / 3.5 |  |
| Quentin Johnston (WR, Top2) | LAC v DEN (Sun 16:05) | 3.3 | 3 | 2.0 | 1.5: 82% / 2.5: 63% / 3.5: 42% / 4.5: 26% / 5.5: 14% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| Marvin Harrison Jr. (WR, Next) | ARI v DET (Sun 16:25) | 3.1 | 3 | 1.9 | 1.5: 79% / 2.5: 58% / 3.5: 37% / 4.5: 21% / 5.5: 11% | 1.5 / 1.5 / 1.5 | 4.5 / 4.5 / 3.5 |  |
| Michael Wilson (WR, Top2) | ARI v DET (Sun 16:25) | 5.8 | 5 | 2.8 | 3.5: 78% / 4.5: 64% / 5.5: 50% / 6.5: 36% / 7.5: 25% | 3.5 / 3.5 / 4.5 | 7.5 / 8.5 / 6.5 |  |
| Trey McBride (TE, Top2) | ARI v DET (Sun 16:25) | 7.9 | 8 | 3.4 | 6.5: 63% / 7.5: 51% / 8.5: 39% / 9.5: 29% / 10.5: 21% | 5.5 / 4.5 / 6.5 | 9.5 / 10.5 / 8.5 |  |
| Jameson Williams (WR, Next) | DET v ARI (Sun 16:25) | 4.4 | 4 | 2.4 | 2.5: 78% / 3.5: 61% / 4.5: 44% / 5.5: 29% / 6.5: 18% | 2.5 / 2.5 / 3.5 | 5.5 / 6.5 / 5.5 |  |
| Amon-Ra St. Brown (WR, Top2) | DET v ARI (Sun 16:25) | 7.1 | 7 | 3.2 | 5.5: 66% / 6.5: 53% / 7.5: 41% / 8.5: 30% / 9.5: 21% | 4.5 / 4.5 / 5.5 | 8.5 / 9.5 / 7.5 |  |
| Sam LaPorta (TE, Top2) | DET v ARI (Sun 16:25) | 4.9 | 5 | 2.5 | 3.5: 69% / 4.5: 53% / 5.5: 37% / 6.5: 25% / 7.5: 15% | 3.5 / 2.5 / 3.5 | 6.5 / 7.5 / 5.5 |  |
| Rashid Shaheed (WR, Next) | SEA v SF (Sun 16:25) | 2.6 | 2 | 1.7 | 0.5: 91% / 1.5: 72% / 2.5: 48% / 3.5: 28% / 4.5: 14% | 1.5 / 0.5 / 1.5 | 3.5 / 4.5 / 3.5 |  |
| AJ Barner (TE, Top2) | SEA v SF (Sun 16:25) | 3.1 | 3 | 1.9 | 1.5: 78% / 2.5: 57% / 3.5: 36% / 4.5: 21% / 5.5: 11% | 1.5 / 1.5 / 1.5 | 4.5 / 4.5 / 3.5 |  |
| Jaxon Smith-Njigba (WR, Top2) | SEA v SF (Sun 16:25) | 6.7 | 6 | 3.1 | 4.5: 75% / 5.5: 62% / 6.5: 48% / 7.5: 36% / 8.5: 25% | 4.5 / 3.5 / 5.5 | 8.5 / 9.5 / 7.5 |  |
| Deebo Samuel Sr. (WR, Next) | SF v SEA (Sun 16:25) | 3.6 | 3 | 2.1 | 1.5: 85% / 2.5: 67% / 3.5: 47% / 4.5: 30% / 5.5: 17% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| George Kittle (TE, Top2) | SF v SEA (Sun 16:25) | 4.5 | 4 | 2.4 | 2.5: 79% / 3.5: 62% / 4.5: 45% / 5.5: 30% / 6.5: 19% | 2.5 / 2.5 / 3.5 | 5.5 / 6.5 / 5.5 |  |
| Mike Evans (WR, Top2) | SF v SEA (Sun 16:25) | 4.4 | 4 | 2.4 | 2.5: 78% / 3.5: 61% / 4.5: 44% / 5.5: 29% / 6.5: 18% | 2.5 / 2.5 / 3.5 | 5.5 / 6.5 / 5.5 |  |
| Jahan Dotson (WR, Next) | ATL v BAL (Sun 20:20) | 2.1 | 2 | 1.6 | 0.5: 87% / 1.5: 61% / 2.5: 36% / 3.5: 18% / 4.5: 8% | 0.5 / 0.5 / 1.5 | 3.5 / 3.5 / 2.5 |  |
| Drake London (WR, Top2) | ATL v BAL (Sun 20:20) | 5.1 | 5 | 2.6 | 3.5: 72% / 4.5: 56% / 5.5: 40% / 6.5: 27% / 7.5: 17% | 3.5 / 2.5 / 3.5 | 6.5 / 7.5 / 5.5 |  |
| Kyle Pitts (TE, Top2) | ATL v BAL (Sun 20:20) | 3.5 | 3 | 2.1 | 1.5: 84% / 2.5: 66% / 3.5: 46% / 4.5: 29% / 5.5: 16% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| Rashod Bateman (WR, Next) | BAL v ATL (Sun 20:20) | 2.5 | 2 | 1.7 | 0.5: 91% / 1.5: 70% / 2.5: 46% / 3.5: 26% / 4.5: 13% | 1.5 / 0.5 / 1.5 | 3.5 / 4.5 / 3.5 |  |
| Mark Andrews (TE, Top2) | BAL v ATL (Sun 20:20) | 3.6 | 3 | 2.1 | 1.5: 85% / 2.5: 67% / 3.5: 47% / 4.5: 30% / 5.5: 17% | 1.5 / 1.5 / 2.5 | 4.5 / 5.5 / 4.5 |  |
| Zay Flowers (WR, Top2) | BAL v ATL (Sun 20:20) | 5.2 | 5 | 2.6 | 3.5: 72% / 4.5: 56% / 5.5: 41% / 6.5: 28% / 7.5: 18% | 3.5 / 2.5 / 3.5 | 6.5 / 7.5 / 5.5 |  |

## 4. Status / news used (public, search-snippet level, verify before betting)

* Lamar Jackson ruled OUT (ankle) - Tyler Huntley starts for BAL at ATL (Fox Sports / AJC Oct 9).
* PHI at JAX (London): DeVonta Smith OUT, Saquon Barkley OUT (hamstrings); Dallas Goedert back; Dontayvion Wicks no designation (Inquirer / PhillyVoice / RotoBaller Oct 9). Bigsby becomes lead back - projection understates volume.
* WAS: Jayden Daniels expected to start after elbow dislocation (backup Mariota MCL); Stefon Diggs OUT; Terry McLaurin trending to play.
* MIA: De'Von Achane reported out for the season (ACL) per one low-reliability snippet - excluded; Ollie Gordon II listed as lead back (volume understated).
* CIN: Ja'Marr Chase (concussion in Wk4) and Tee Higgins (adductor) limited - status unresolved; CIN -7/-7.5, total ~42.5-43.5.
* LV: Ashton Jeanty questionable (ankle/foot). NE: A.J. Brown on reserve list - excluded.
* All injury items are from search snippets dated Oct 7-9; Sunday inactives were not yet available at generation time.

## 5. Sources (search snippets; pages themselves could not be fetched)

* Hurts lines & PHI/JAX: https://www.inquirer.com/eagles/eagles-jaguars-week-5-nfl-odds-prop-bets-20261008.html ; https://www.phillyvoice.com/eagles-jaguars-week-5-betting-odds-money-lines-points-spread-jalen-hurts-trevor-lawrence-london/
* Stroud / Ward lines: https://www.sportsbettingdime.com/?p=840997 ; https://www.rotoballer.com/?p=1961726
* Goff 280.5 (StackedFantasy): https://www.stackedfantasy.com/nfl/news/insights/1016778 ; projection https://www.dimers.com/nfl/news/jared-goff-projected-fantasy-stats-nfl-week-5-2026-ac
* Daniels 210.5: https://www.legalsportsreport.com/nfl/nfl-player-prop-odds-week-5-props-for-weekend-matchups-mnf/ (snippet mislabeled the opponent; treat as low reliability)
* Wilson over 70: https://www.fantasylife.com/articles/betting/nfl-player-props-week-5 ; St. Brown/Olave 80/70: https://www.squawka.com (editorial picks)
* Chase Brown 65.5: https://www.fantasyalarm.com/articles/nfl/predictions/bengals-vs-dolphins-predictions-picks-odds-nfl-week-5-10-11-2026/196620
* Lamar out: https://www.thefantasyfootballers.com/news/641531/lamar-jackson-officially-ruled-out-for-week-5/
* Data: https://github.com/nflverse/nflverse-data/releases (stats_player_week_YYYY.csv, games.csv)

## 6. Reproduce

`cd /tmp/claude-0/-home-user-fantastic-octo-computing-machine/fd837da0-fc17-5f70-a6ad-c31478ee2717/scratchpad/nfl/props` then run (python = scratchpad/oklahoma/.venv): `backtest.py` (validation) -> `project.py` (fit + candidates) -> `DROP="Jayden Daniels:2026" OUT_SUFFIX=_daniels project.py` (Daniels adj.) -> `final.py` (exclusions, edges) -> `report.py`. Files: `projections.csv` (mean/median/SD/alpha + cut-offs), `projection_lines.csv` (P(over) grid), `edge_check_all_sides.csv`, `backtest_results.txt`.