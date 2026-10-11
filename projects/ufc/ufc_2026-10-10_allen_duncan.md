# UFC Fight Night: Allen vs Duncan (Oct 10, 2026), Benter-style card

Method:
- **Fundamental model:** an antisymmetric logistic regression on Elo plus pre-fight differentials, trained on 2011–2022.
- **Holdout test (2023 to Oct 3, 2026; 1,979 fights):**
  - Log loss 0.641 vs 0.678 for Elo alone and 0.693 for a 50% guess.
  - Accuracy 63.4%.
  - It beats Elo in every year, with a 95% CI on the gain of 0.029–0.046.
  - We have no historical odds, so it is **not** tested against the market.
- **Blend:** p = 0.3 × model + 0.7 × the no-vig consensus market (Benter-style; the weight is assumed, not fitted).
- **Dabble legs:** I treat each line as 50/50 and blend the same way. A leg qualifies only if my raw estimate is at least 76% for a 2-pick, 71% for a 4-pick, or 67% for a 3-pick.
- **Sources:** dossier details come from WebSearch snippets only (page fetches failed) and are unverified against the source pages. Full notes with URLs are in `ufc/research/*.md`.
- **Data:** the model data runs to Oct 3, 2026 (Greco1899/scrape_ufc_stats). Low-sample fighters: Tanzilovi (1 UFC fight), Camilo (3) and Wellmaker (4).

## Camps and bases
| Fighter | Gym / coach | Base |
|---|---|---|
| Brendan Allen | Chicago, with Mike Valle (Valle Flow Striking), last 3 camps (ex-Kill Cliff FC). BJJ black belt under Daniel Wanderley. | Submission grappler, 7 UFC submission wins |
| Christian Leroy Duncan | Range Martial Arts Academy, Gloucester UK (coaches not found) | Striker, switch stance. Ex-basketball, IMMAF, Cage Warriors champion. |
| Matheus Camilo | Xtreme Couture, Las Vegas (ex-Nova União) | BJJ brown belt, pressure wrestler |
| Jai Herbert | Team Renegade, Birmingham UK (Tom Breese: BJJ/wrestling) | Muay Thai, ex-Cage Warriors champion |
| Loopy Godinez | WKX, Surrey BC (head coach Jay Jauncey) | Judo, then BJJ purple belt; high-volume takedowns |
| Ketlen Souza | Carioca Academy, Manaus (Cristian "Carioca" Bezerra; 2023 source) | Boxing / Luta Livre |
| Andre Fili | Team Alpha Male, Sacramento (unconfirmed for 2026) | BJJ, high-school wrestling |
| Kai Kamaka III | Xtreme Couture, Las Vegas (ex-808 Fight Factory, Hawaii) | Wrestling |
| Malcolm Wellmaker | American Top Team since May 2026 (ex-Faglier's MMA, Augusta) | Counter-right-hand power striker; 0.0 takedowns per 15 min |
| Otari Tanzilovi | Guram Fight Club, Georgia | Kickboxer who wrestled heavily in his UFC debut |

## Win probabilities
| Fight | Market (no-vig) | Model | Blend | Value check |
|---|---|---|---|---|
| Allen vs Duncan | Allen 54.2% | Allen 50.9% | Allen 53.2% | Allen @1.86: −1%. Duncan @1.97: −8%. **Pass.** |
| Camilo vs Herbert | Camilo 63% | Camilo 71.8% (mostly age-driven) | Camilo 65.6% | Camilo @1.52: 0%. Herbert @2.59: −11%. **Pass.** |
| Godinez vs Souza | Godinez 67% | Godinez 63.8% | Godinez 66.0% | Godinez @1.42: −6%. Souza @+192: −1%. **Pass**, unless Souza is +205 or better. |
| Fili vs Kamaka | Fili 57% | Fili 55.7% | Fili 56.6% | Kamaka @+138: +3%. @+120: −5%. **Only at +135 or better.** |
| Wellmaker vs Tanzilovi | Wellmaker 66% | **Tanzilovi 58.4%** | **Tanzilovi 41.3%** | **Tanzilovi @+183: +17%. @+172: +12%.** |

### The one outlier: Otari Tanzilovi moneyline
- **The evidence for him:**
  - The model and the independent researcher both lean Tanzilovi.
  - Wellmaker's 2 UFC losses were both takedown-driven, with 8 of 13 takedowns completed against him. His takedown defense is about 46%.
  - Tanzilovi averaged 4.5 takedowns per 15 minutes in his UFC debut.
- **The risks:**
  - Small samples on both fighters.
  - Wellmaker moved to American Top Team in May, so his wrestling defense may be better than his record shows.
  - **The line moved toward Wellmaker (-176 to -225)**, which suggests informed money disagrees.
- **Stake:** ¼ Kelly is about 2.3% of bankroll. **Do not bet if the fight has started.**

## Dabble projections (median, and the line needed for a leg)
Strike volume depends on how long the fight lasts, so the ranges are wide.

| Fighter | Sig-strike median | More only if line ≤ | Less only if line ≥ | Takedown mean | P(≥1 takedown) | P(≥2 takedowns) |
|---|---|---|---|---|---|---|
| Allen | 30 | 15.5 | 50.5 | 1.96 | 0.60 | 0.39 |
| Duncan | 44 | 25.5 | 70.5 | 0.75 | 0.39 | 0.18 |
| Camilo | 24 | 10.5 | 40.5 | 1.62 | 0.59 | 0.36 |
| Herbert | 26 | 15.5 | 40.5 | 0.41 | 0.28 | 0.09 |
| Godinez | 43 | 25.5 | 60.5 | 2.46 | 0.70 | 0.49 |
| Souza | 40 | 25.5 | 60.5 | 0.63 | 0.38 | 0.15 |
| Fili | 47 | 30.5 | 70.5 | 1.57 | 0.59 | 0.36 |
| Kamaka | 50 | 30.5 | 75.5 | 0.69 | 0.40 | 0.17 |
| Wellmaker | 37 | 20.5 | 55.5 | 0.30 | 0.22 | 0.06 |
| Tanzilovi | 33 | 20.5 | 50.5 | 3.33 | 0.74 | 0.56 |

**Chance each fight goes the distance:**
- Allen vs Duncan: 0.38. This is likely understated; the holdout showed 0.47 actual on 5-round fights.
- Camilo vs Herbert: 0.47.
- Godinez vs Souza: 0.68.
- Fili vs Kamaka: 0.59.
- Wellmaker vs Tanzilovi: 0.52.

**Legs that can qualify, if Dabble posts these lines.** Raw estimate is the average of the model and the research:

| Leg | Raw estimate | Qualifies for |
|---|---|---|
| Wellmaker takedowns **Less 0.5** | ~0.80 (model 0.78; 0.0 career takedowns per 15 min) | 2-pick |
| Tanzilovi takedowns **More 0.5** | ~0.69 | 3-pick only |
| Godinez takedowns **More 0.5** | ~0.75 | 3- or 4-pick |
| Godinez–Souza fight time **More**, if the line is ≤14.5 min | ~0.68 | 3-pick only |
| Herbert takedowns **Less 0.5** | ~0.72 | 3- or 4-pick |
| Camilo takedowns More 0.5 | ~0.68 | borderline |
| Allen takedowns More 0.5 | ~0.68 | borderline |

Significant-strike lines set near the medians: **no edge**. The fight-length uncertainty is too wide.

**Grade after the card:** results vs these numbers will be logged in `reports/tracking_ledger.csv`.
