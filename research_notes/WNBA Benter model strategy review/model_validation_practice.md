# Validating a Sports-Betting Prediction Model Before Staking Real Money (best practice, math, pitfalls)

> Research method note (2026-10-10): direct page fetches were blocked in this environment. The egress proxy denied or failed DNS for pinnacle.com, football-data.co.uk and gwern.net, so I could not read the primary Pinnacle/Buchdahl articles or the Benter PDF in full. Findings below come from search-engine extracts of those pages plus secondary summaries, and each one is marked that way. Numbers tagged **[computed]** are my own calculations (normal approximation to the binomial, exact binomial tails, Beta posteriors, Monte Carlo with 20,000 paths). The formulas are given so they can be re-derived. They are math, not sourced claims.

---

## 1. How many bets does it take to tell a 55% hitter from break-even (52.4% at -110; 57.7% per leg on a 3x two-leg slip)?

### Takeaway
At -110 a real 55% bettor has only a +5% ROI edge, while the standard deviation per bet is about 0.95 units. Separating that from the 52.38% break-even takes about 1,000 bets just to reach one-sided p<0.05. Detecting a true 55% bettor with 80% power takes about 2,250 bets. For a 3x two-leg slip, per-leg break-even is 57.7%, so a 55% leg hitter loses about 9% per slip. Even a 60% leg hitter needs roughly 850–2,000 slips (1,300–2,900 legs) before results alone separate them from break-even.

### Cited Findings
- **Break-even math [computed]:** -110 pays 100/110, so break-even p = 110/210 = **52.38%**. A two-leg slip paying 3x total (decimal 3.0) breaks even when p_leg² = 1/3, so p_leg = √(1/3) = **57.74%** per leg, assuming independent legs.
- **Edge size at 55%, -110 [computed]:** EV per 1u bet = 0.55 × 0.9091 − 0.45 = **+0.050u (5% ROI)**. Per-bet SD of return = **0.95u**, so each bet carries about 19× more noise than signal.
- **Sample size so that an *observed* 55% is significant vs 52.38% [computed]:** n = z²·p₀(1−p₀)/(0.55−p₀)²:
  - one-sided p=0.05 (z=1.645): **≈984 bets**
  - two-sided p=0.05 (z=1.96): **≈1,397 bets**
  - one-sided p=0.01: **≈1,967 bets**
  - z=3: **≈3,273 bets**
- **Sample size to *detect* a true 55% bettor (power analysis) [computed]:** n = [z_α√(p₀q₀) + z_β√(p₁q₁)]²/(p₁−p₀)²:
  - α=0.05 one-sided, 80% power: **≈2,242 bets**
  - 90% power: **≈3,104 bets**
  - α=0.01, 80% power: **≈3,642 bets**
- **The same answer using the ROI t-test [computed]:** n = (z·σ/edge)² with σ≈0.95 and edge 0.05 gives **977 (one-sided)** or **1,387 (two-sided)** bets. The two methods agree.
- **How often a no-skill bettor looks like a 55% hitter [computed, exact binomial]:** P(hit ≥55% | true p = 52.38%) is **35.6% at n=50, 26.7% at n=100, 20.4% at n=250, 13.0% at n=500, 5.2% at n=1,000, 1.0% at n=2,000**.
- **How often a true 55% bettor is still at or below break-even [computed]:** **30.7% after 100 bets, 18.7% after 250, 11.3% after 500, 4.6% after 1,000.** Early stop/go decisions made on hit rate alone are close to coin-flips.
- **Bayesian view [computed]:** with a flat Beta(1,1) prior and an observed 55% hit rate, the posterior P(p > 52.38%) is **0.70 at n=100, 0.80 at n=250, 0.88 at n=500, 0.95 at n=1,000, 0.99 at n=2,000**.
- **3x two-leg slip economics [computed]:** slip ROI = 3·p_leg² − 1. That gives **55% leg → −9.25%**, 57.7% → about 0%, **60% → +8.0%**, **62% → +15.3%**, **65% → +26.75%**.
- **Slip sample sizes [computed]** (one-sided α=0.05; first figure is for an observed rate, second is for 80% power):
  - true leg 60% vs 57.74%: **846 / 1,956 slips** (1,287 / 2,924 legs if tested leg-by-leg under independence)
  - true leg 62%: **231 / 538 slips** (363 / 820 legs)
  - true leg 65%: **76 / 178 slips** (125 / 279 legs)
- **Practitioner benchmarks:**
  - Pinnacle's article estimates that a bettor at typical odds around 5.0 "might take 2,500 bets" before results can be told apart from luck. The [computed] figure for a 5% edge at odds 5.0 (SD ≈ 2.04u per bet) is ≈4,300–6,100 bets. — [Pinnacle: Using the closing line to test your skill in betting](https://www.pinnacle.com/betting-resources/en/betting-strategy/using-the-closing-line-to-test-your-skill-in-betting/7e6jwjm5ykejuwkq) (via search extract; article date not visible)
  - Pinnacle's Bayes-factor article says about **3,500 bets** are needed to reach a Bayes factor of 100. — [Pinnacle: Are you a skilled bettor? (Bayes factor)](https://www.pinnacle.com/betting-resources/en/educational/part-two-using-bayes-factor-to-assess-betting-skill/nf52l4mwxxv7785g) (via search extract)
  - Buchdahl, as summarized by secondary sites, says results-only proof takes "several thousand" or "2,000 to 3,000" bets. — [PinnacleOddsDropper: CLV demystified by Joseph Buchdahl](https://www.pinnacleoddsdropper.com/blog/closing-line-value--clv-demystified-by-expert-joseph-buchdahl) (secondary)
  - Rebel Betting's example: 100 bets at average odds 2.0 with a 5% yield leaves about a one-in-three chance the result is pure luck. The same page has an internal inconsistency in its p-value note. — [RebelBetting: Your tipster is a scam](https://www.rebelbetting.com/your-tipster-is-a-scam) (vendor)

### Inferences
- A single WNBA season will not validate a 55% prop model on hit rate alone. A season gives a few hundred bets at most for a selective bettor, and the binomial sample needed is about 1,000–2,250+. One season can at best reject an obviously bad model.
- The two-leg 3x slip roughly doubles the bar: the required per-leg accuracy is 57.7% rather than 52.4%. A model honestly expected to hit about 55% per leg has negative EV on 3x slips. The slip format only makes sense if real leg accuracy is at least about 60%, which is a very strong claim for any market.
- Leg-level testing assumes independent legs. Same-game or same-player legs are positively correlated, which raises the slip hit rate but also variance, and reduces the effective sample. Count slips, not legs, when legs are correlated.
- Required n scales as 1/edge². Halving the true edge (5% → 2.5% ROI) quadruples the bets needed. Realistic edges in liquid markets are small, which is why pros lean on CLV (Section 2).

### Gaps
- I found no peer-reviewed source stating a canonical "N bets" rule. Published figures (2,500; 3,500; "several thousand") are practitioner estimates tied to specific assumptions about odds and edge.
- The independence assumption for slip legs is untested here. The effect of real same-game correlation on DFS-style pick'em props was not quantified.

---

## 2. Why do pros prefer CLV to win/loss record, and how many bets until CLV is informative?

### Takeaway
CLV is measured as how much better your price was than the no-vig closing price. It is much less noisy per bet than P&L: the SD is about 0.1 for CLV versus about 1.0 for even-money P&L, according to Buchdahl via secondary summaries. A consistent 2–5% CLV becomes statistically distinguishable from zero in roughly **30–100 bets**, compared with **thousands** of bets on results. CLV is only as good as the closing line it is measured against. It is weakest in thin, low-limit markets such as player props, and it does not guarantee profit.

### Cited Findings
- **Variance gap:** Buchdahl's summarized argument is that the "typical standard deviation in even-money profits and losses will be about 1.00, the equivalent for CLV will be about 0.1." — [PinnacleOddsDropper: CLV demystified by Joseph Buchdahl](https://www.pinnacleoddsdropper.com/blog/closing-line-value--clv-demystified-by-expert-joseph-buchdahl) (secondary summary; original not fetched)
- **Bet counts:** if someone consistently beats the closing line, it takes "far fewer bets, perhaps as few as just 50" to show statistical significance. In one football example Buchdahl calculated that **65 bets** would have been enough. — [Pinnacle: Using the closing line to test your skill](https://www.pinnacle.com/betting-resources/en/betting-strategy/using-the-closing-line-to-test-your-skill-in-betting/7e6jwjm5ykejuwkq); [Football-Data: Using the closing odds to test a tipster's skill](https://football-data.co.uk/blog/closing_odds.php) (both via search extract)
- **Range quoted by secondary sites:** "2,000 to 3,000 bets for results versus as few as 50 to 100 bets for CLV" at around a 5% consistent edge. Another site suggests 300+ bets minimum for CLV. The thresholds conflict and depend on the assumed edge. — [PinnacleOddsDropper](https://www.pinnacleoddsdropper.com/blog/closing-line-value--clv-demystified-by-expert-joseph-buchdahl) (secondary)
- **CLV sample sizes [computed]** using n = (z·σ_CLV/mean CLV)² with σ_CLV = 0.1:
  - mean CLV 3%: **30 (one-sided) / 43 (two-sided)** bets
  - mean CLV 2%: **68 / 96** bets
  - mean CLV 1%: **271 / 384** bets
  - For comparison, results-based testing of a 2% edge at even money needs **6,765 / 9,604** bets.
- **Evidence that CLV tracks actual yield:** Buchdahl reportedly tested four seasons of Pinnacle closing odds (**87,960 odds pairs**, major European football leagues) and found a near one-to-one relationship between beating the close and long-run yield. — [PinnacleOddsDropper](https://www.pinnacleoddsdropper.com/blog/closing-line-value--clv-demystified-by-expert-joseph-buchdahl) (secondary; unverified)
- **Price moves are not random:** Buchdahl (X post, Nov 2021) says CLV "cannot be random because the standard deviation in price moves is many orders of magnitude smaller than the observed CLV here." — [Joseph Buchdahl on X](https://x.com/12Xpert/status/1461322476173025288)
- **The margin matters:** expected return ≈ CLV minus the margin built into the closing price, so +2% CLV against a 2% margin roughly breaks even. — [PinnacleOddsDropper](https://www.pinnacleoddsdropper.com/blog/closing-line-value--clv-demystified-by-expert-joseph-buchdahl) (secondary)
- **How to compute it:**
  - Remove the vig from the sharp book's (typically Pinnacle's) closing price, then CLV = entry decimal odds × no-vig closing probability − 1.
  - Collapse repeated snapshots of the same pick so it counts once. — [SharpAPI docs: Historical CLV](https://docs.sharpapi.io/en/api-reference/historical-clv/) (vendor docs)
- **Counterpoint — CLV is not a guarantee:** Karl Whelan, an economist at UCD, argues that the popular claim "beating the closing line guarantees long-term success" is wrong: "getting CLV does not guarantee that you will win long-term." He uses NBA moneylines as an efficient market with no favourite-longshot bias, and notes that other markets are more prone to that bias. — [Karl Whelan: The Truth about Closing Line Value](https://www.karlwhelan.com/?p=2595) (blog; only the opening was visible in search)
- **The closing line itself can be biased:** a Substack analysis using Buchdahl's football-data set (193,803 matches; about 31,000 EV bets over 14 seasons) cites a Buchdahl post arguing that **arbitrage bettors can force Pinnacle to move its closing odds in a suboptimal direction**. — [Networked Substack: A view from the Pinnacle](https://networked.substack.com/p/a-view-from-the-pinnacle)
- **Props are a weak reference:**
  - "Thin liquidity means any CLV is, at best, an informed guess."
  - "The more esoteric the prop, the more likely its CLV is meaningless."
  - CLV assumes an efficient close, which is "approximately true for major markets at sharp sportsbooks but less reliable for props, lower-tier leagues, and books with low betting limits."
  - "If you can't find your market on a sharp book like Pinnacle or Circa, then it's probably not a market where CLV matters."
  - Sources: [Unabated: Getting Precise About CLV](https://unabated.com/post/getting-precise-about-closing-line-value) and other results summarized in the same search (practitioner/vendor; the majority view, with some vendors arguing props are *more* exploitable)
- **The academic benchmark:** Pinnacle's close is commonly used as the benchmark in academic market-efficiency studies. The cited *Journal of Sports Sciences* finding appears only as a secondhand claim. — [TheSpread: CLV Is the Gold Standard](https://www.thespread.com/?p=550721) (secondary)

### Inferences
- **Why pros prefer CLV:**
  - It measures *process*, meaning whether you bought below the market's final consensus, rather than outcome noise. With σ about 10× smaller, the bets needed fall by about 100×, because n scales with σ².
  - It is also available for every bet the moment the market closes, so a model can be judged in weeks rather than seasons.
- **For a WNBA player-prop model, CLV is weaker evidence than it is for NFL or NBA sides:**
  - Prop closes are set at low limits, often by books that copy each other.
  - Many props have no Pinnacle or Circa close at all.
  - The SD of prop line moves is plausibly larger than 0.1. If so, n grows with the square (e.g., σ=0.2 means 4× the bets).
  - Prop lines also move in discrete half-point steps on the line and in juice, so CLV needs a conversion from line movement into probability, for example through a player-distribution model.
- **Recommended practice (synthesis):**
  - Record the timestamp, book, line and price at bet time.
  - Capture the closing line and price from the sharpest book available.
  - Devig the close (multiplicative or power method).
  - Track mean CLV with a standard error and a t-statistic, and report CLV alongside P&L, not instead of it.
  - Treat persistent positive CLV *plus* P&L that is not wildly inconsistent with it as the bar.
- If model picks consistently show *negative* CLV, the market is moving against the model. That is strong early evidence the edge is illusory, even if early P&L is positive.

### Gaps
- I could not read Buchdahl's original Pinnacle/Football-Data text, so the 0.1 CLV SD, the 50/65-bet figures and the 87,960-pair regression are reported via search extracts and secondary summaries only.
- I found no published estimate of the CLV SD, or of the CLV-to-yield relationship, for WNBA or NBA player props specifically.
- Whelan's full argument (how favourite-longshot bias breaks the CLV-to-profit link) was not visible in search results.

---

## 3. Known pitfalls: synthetic or stand-in lines, data leakage, garden of forking paths, survivorship in tipster records

### Takeaway
The main failures are:
- **Measuring edge against prices you could not actually have bet.** This includes synthetic lines, flat -110 assumptions, closing lines used as entry prices, and ignoring limits and account restrictions.
- **Temporal leakage.** Features known only at tip-off, or afterwards, get used for bets priced earlier.
- **Silent multiple testing.** Many model variants are tuned on the same holdout seasons, and the "best" variant looks profitable purely by selection.
- **Survivorship.** Only winning records get seen.

Each of these alone can manufacture an apparent 55%+ hit rate out of no skill.

### Cited Findings
**Leakage**
- Kapoor & Narayanan (*Patterns*, 2023) found leakage errors in **17 fields affecting 294 papers** (the arXiv preprint says 329). They propose an **8-type leakage taxonomy that includes "temporal leakage" (L3.1)**. In their civil-war-prediction case study, once leakage was corrected, "the supposed superiority of ML models disappeared": the models did no better than older methods. They recommend "model info sheets" to prevent each leakage type. — [Kapoor & Narayanan, Leakage and the Reproducibility Crisis in ML-based Science (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10499856); [arXiv 2207.07048](https://arxiv.org/abs/2207.07048v1)

**Forking paths and multiple testing**
- Gelman & Loken (2013) show that multiple-comparison problems arise **even without deliberate fishing**: "there can be a large number of potential comparisons when the details of data analysis are highly contingent on data." Researcher degrees of freedom include exclusions, interactions and analysis method. — [Wikipedia: Forking paths problem](https://en.wikipedia.org/wiki/Forking_paths_problem); [FORRT glossary](https://forrt.org/glossary/english/garden_of_forking_paths/)
- Bailey & López de Prado, *The Deflated Sharpe Ratio* (J. Portfolio Mgmt, 2014): "not controlling for the number of trials involved in a particular discovery leads to over-optimistic performance expectations." The DSR corrects for selection bias and non-normality. — [SSRN 2460551](https://papers.ssrn.com/abstract=2460551)
- Bailey, Borwein, López de Prado & Zhu, *The Probability of Backtest Overfitting* (J. Computational Finance, 2015/2017):
  - Defines a selected strategy as overfit if its out-of-sample performance is below the **median** out-of-sample performance of all alternatives tried.
  - Estimates the probability of that with combinatorially symmetric cross-validation (CSCV). An R `pbo` package is on CRAN.
  - Source: [SSRN 2326253](https://papers.ssrn.com/abstract=2326253); [CRAN pbo vignette](https://cran.hafro.is/web/packages/pbo/vignettes/pbo.html)
- **Selection inflation on a reused holdout [computed, Monte Carlo]:** K no-skill variants (true p = 52.38%) are evaluated on the same n-bet holdout and the best one is kept.

  | Holdout n | Variants K | Expected best hit rate | P(best ≥ 55%) |
  |---|---|---|---|
  | 250 | 10 | 57.2% | 90% |
  | 250 | 20 | 58.3% | 99% |
  | 500 | 10 | 55.8% | 75% |
  | 500 | 20 | 56.6% | 94% |
  | 1,000 | 20 | 55.3% | 66% |
  | 1,000 | 50 | 55.9% | 93% |

- **Bonferroni-adjusted sample needs [computed]:** for an observed 55% to stay significant after K tries (one-sided family α=0.05), you need about **1,968 bets at K=5, 2,413 at K=10, 2,865 at K=20, 3,473 at K=50, and 3,937 at K=100**, compared with 984 bets at K=1.

**Survivorship in tipster records**
- Buchdahl's Monte Carlo on Pinnacle (1,000 runs) modelled a marketplace of purely lucky tipsters, each removed once their yield fell below −5%. "The average number of remaining tipsters... was 56, whilst the average aggregate yield from those tipsters was **5.4%**." That apparent profit is generated by the filter alone. — [Pinnacle: The tipster marketplace and the impact of survivorship bias](https://www.pinnacle.com/betting-resources/en/educational/the-tipster-marketplace-and-the-impact-of-survivorship-bias/hgz26fmjeq29gn9g) (via search extract)
- A 2015 Buchdahl analysis of **6,000+ tipsters / 1M+ tips** found **2,138 showed some profit but only about 45** could be "statistically proven to be outside the realm of luck." — [Dutching as a Business blog, Feb 2018](http://dutchingasabusiness.blogspot.com/2018/02) (secondary summary)
- Out-of-sample decay in a verification service (2001–2015, 300+ tipsters verified, about half unprofitable): **120 tipsters arrived with about 24,000 tips at a 17% aggregate yield. On the ~19,000 tips after verification, their yield was about 1%.** — [Trademate Sports: Interview with Joseph Buchdahl](https://www.tradematesports.com/en/blog/interview-betting-expert-joseph-buchdahl)

**Backtests vs realizable prices and limits**
- Kaunitz, Zhong & Kreiner (2017, arXiv 1710.02824) used consensus (average) odds across bookmakers as a probability estimate. Their data covered about 10 years, nearly 0.5M football matches and 32 bookmakers (Jan 2005–Jun 2015). Once their real-money bets succeeded, "the bookies prevented the researchers from betting further." — [MIT Technology Review, 2017-10-19](https://www.technologyreview.com/2017/10/19/67760/the-secret-betting-strategy-that-beats-online-bookmakers/); [arXiv 1710.02824](https://arxiv.org/pdf/1710.02824); [Scottish Daily Express](https://www.scottishdailyexpress.co.uk/news/weird-news/boffins-devise-successful-bookie-bashing-27552631)
- Prop books "with different risk tolerances can close at different prices for reasons unrelated to true probability." One guide recommends tracking ROI against consistent price benchmarks. — search summary of [Unabated](https://unabated.com/post/getting-precise-about-closing-line-value) and related practitioner pages (practitioner)

### Inferences
- **Synthetic or stand-in lines**
  - Backtesting against model-generated lines, a flat -110 assumption, or a single "consensus" line (instead of the actual line and price posted at a real book at the decision time) measures agreement with yourself, not edge.
  - Real prop lines are shaded. Juice varies (e.g., -115/-125 rather than -110), and stale lines are pulled or limited.
  - The edge must be computed against the exact price the bettor could have taken, at the timestamp the model would have fired, with a realistic maximum stake.
  - For pick'em/slip products, the "price" is the payout table (e.g., 3x), and the line is the posted projection. Backtests must use the actual historical projections, not reconstructed ones.
- **Look-ahead and timestamp leakage typical of basketball data**
  - Starting lineups and late scratches are known only shortly before tip, so a model using them is only valid against lines posted *after* that news.
  - Leaky features include:
    - actual minutes played or box-score fields of the same game
    - season averages computed including the target game
    - injury status taken from end-of-day reports
    - rolling features without a one-game lag
    - closing lines used as features for bets priced at the open
  - Every feature should carry an "as-of" timestamp no later than the bet timestamp. Validation should be walk-forward, with no shuffled K-fold across time.
- **Forking paths**
  - Every change made after looking at test-season results (feature tweaks, thresholds, edge cut-offs, which seasons to include, which prop types to keep) is an implicit comparison.
  - Reusing the same 2–3 holdout seasons across dozens of iterations makes the final holdout an in-sample result.
  - Remedies:
    - Keep a log of the number of variants tried.
    - Apply DSR/Bonferroni-style deflation or PBO/CSCV.
    - Lock a final untouched holdout, or better, use live forward paper or small-stakes betting as the true test.
- **Survivorship applies to your own research too:** if only the model versions that "worked" are kept and remembered, the survivor's backtest overstates its edge, exactly like a tipster marketplace.

### Gaps
- I found no academic paper quantifying the bias from synthetic vs real historical prop lines specifically. The inference above is reasoning, not a sourced estimate.
- I found no published source documenting WNBA starting-lineup release timing relative to prop line movement.
- The Kaunitz paper's exact real-money returns and the timeline of the account restrictions were not visible in the search results.

---

## 4. Calibration, proper scoring rules, and blending with market prices (Benter-style); what strong disagreement with the market means

### Takeaway
Select and evaluate models on proper scoring rules (log loss/ignorance first, Brier second) and calibration, not on accuracy. Then treat the market as the strongest single predictor and *blend*: fit a second-stage logistic model that combines the model's log-probabilities with the devigged market's log-probabilities. Benter's work showed that a fundamental model *plus* the public odds beat either one alone. Large, frequent model-vs-market disagreements are usually a sign of missing information or model error rather than edge. The edge comes from the model being **informative and decorrelated** from the market, not from being more accurate than it.

### Cited Findings
- **Calibration beats accuracy for betting**
  - Walsh & Joshi, *Machine Learning with Applications* vol. 16 (2024), trained on several NBA seasons and bet on one test season at published odds.
  - Model selection by **calibration gave ROI ≈ +34.7% versus ≈ −35.2%** for selection by accuracy. In the best case it was **+36.93% vs +5.56%**.
  - Their conclusion is that bettors should select models on calibration, not accuracy.
  - Limits: NBA only, a single test season.
  - A "69.86% higher average returns" figure appears in secondary reviews but was not confirmed in the abstract.
  - Sources: [Univ. of Bath research portal](https://researchportal.bath.ac.uk/en/publications/machine-learning-for-sports-betting-should-model-selection-be-bas/); [Systematic review arXiv 2410.21484](https://arxiv.org/pdf/2410.21484)
- **Which scoring rule:** Wheatcroft (*J. Quantitative Analysis in Sports* 17(4), 2021) found in simulations that the **ignorance score (log loss, −log₂ p of the realized outcome) outperforms both Brier and RPS**, and Brier edges RPS, at identifying the better forecaster. This casts doubt on RPS's "sensitivity to distance" for football. Ignorance is a *local* score. — [arXiv 1908.08980](https://arxiv.org/pdf/1908.08980); [LSE Research Online](https://researchonline.lse.ac.uk/id/eprint/111494)
- **Benter (1994)**, *Computer Based Horse Race Handicapping and Wagering Systems: A Report*, reprinted in *Efficiency of Racetrack Betting Markets* (World Scientific, 2008):
  - Describes "a logit-based technique and a corresponding heuristic measure of improvement" for **combining a fundamental handicapping model with the public's implied probability estimates**.
  - Reports "significant positive results in five years of actual implementation."
  - Sources: [World Scientific abstract](https://worldscientific.com/doi/abs/10.1142/9789812819192_0019); [IDEAS/RePEc](https://ideas.repec.org/h/wsi/wschap/9789812819192_0019.html)
- **Benter's reported out-of-sample pseudo-R² (secondary, unverified against the PDF)** on 2,313 races (Sep 1988–Jun 1993):
  - fundamental model **.1016**
  - tipsters **.1014**
  - public odds alone **.1237**
  - **fundamental + public .1327**
  - tipsters + public .1239
  - The model was worse than the public alone, yet it added value in combination. — [OddsPapi: Combine your model with market odds — Benter's second-stage test](https://oddspapi.io/blog/?p=3174) (secondary blog)
- **Why the market term is needed:** a secondary account says Benter's model omitted information such as trainer intent, horse condition on the day and unpublished trial data. Comparing model estimates directly with outcomes showed systematic error, with actual win frequencies leaning toward the public's estimates. — [BestHub article on Benter](https://www.besthub.dev/articles/how-a-tiny-information-edge-beats-market-smarts-in-hong-kong-horse-racing-e65c050f579b) (secondary, lower quality)
- **Decorrelation from the market:**
  - Hubáček, Šourek & Železný, *Exploiting sports-betting market using machine learning* (Int. J. Forecasting 35(2):783–796, 2019), penalize the model's correlation with bookmaker predictions. This "allows for better profit generation"; their NBA tests covered 2007–2014. — [IDEAS/RePEc](https://ideas.repec.org/a/eee/intfor/v35y2019i2p783-796.html); [CTU page](https://ida.fel.cvut.cz/papers/hubacek2019exploiting.html)
  - Hubáček & Šír, *Beating the market with a bad predictive model* (Int. J. Forecasting 39(2):691–719, 2023; arXiv Oct 2020), show a predictor **less accurate than the market can still profit** if it is decorrelated from the bookmaker. Reducing that correlation tends to increase profitability across common market distributions and strategies. — [arXiv 2010.12508](https://arxiv.org/pdf/2010.12508); [IDEAS](https://ideas.repec.Org/a/eee/intfor/v39y2023i2p691-719.html)
  - Hubáček's 2024 PhD thesis notes the model "lags significantly behind bookmakers' predictions, yet decorrelation still is an effective way to achieve profits." — [CTU thesis PDF](https://dspace.cvut.cz/bitstream/handle/10467/114141/F3-D-2024-Hubacek-Ondrej-hubacek_thesis.pdf)
- **Consensus odds are very informative:** Kaunitz et al. relied on the average of bookmakers' odds as "a remarkably accurate reflection of the real probabilities." — [MIT Technology Review, 2017-10-19](https://www.technologyreview.com/2017/10/19/67760/the-secret-betting-strategy-that-beats-online-bookmakers/)

### Inferences
- **The Benter second stage, standard form.** This is from my knowledge of the paper; I could not fetch the PDF to re-verify the notation.
  - p_combined ∝ exp(α·log p_model + β·log p_market), normalized across outcomes.
  - For a binary over/under this is a logistic regression: logit(p) = α·logit(p_model) + β·logit(p_market) (+ intercept).
  - Fit α and β by maximum likelihood on **out-of-sample** model predictions from walk-forward folds, never on in-sample fits.
- **Reading the fitted weights:**
  - α ≈ 0 means the model adds nothing beyond the market.
  - β near 1 with α small but significantly positive is the realistic, healthy outcome.
  - α > β, or a much lower blended log loss than the market alone, is suspicious and should prompt a leakage audit.
- **Validation checklist for calibration:**
  1. Report log loss and Brier for the model, the devigged market, and the blend on the same events. Use a paired test, e.g., the mean and SE of the per-event log-loss difference (a Diebold–Mariano-style test).
  2. Plot a reliability diagram and compute ECE, or a calibration slope/intercept (logistic recalibration). A slope < 1 indicates overconfidence.
  3. If needed, recalibrate (Platt/isotonic) within the training folds only.
  4. Bet only on the *blended* probability vs the available price.
- **What a large disagreement means:** when a model disagrees with a liquid market by a lot (e.g., 10+ probability points on a player prop), the base rate says the model is usually missing information: injury or minutes news, lineup changes, a stale data feed, or a role change. That is exactly the systematic error Benter found.
  - Practical rule: cap the edge you will act on, or require the blend (which shrinks extreme disagreements toward the market) to still show an edge.
  - Audit the largest disagreements by hand.
  - Track whether large-edge bets show *worse* CLV than small-edge bets. If they do, the extreme edges are errors.
- **Accuracy (hit rate) is the wrong selection metric.** A model that hits 56% on heavily juiced favorites can lose money, while a well-calibrated model with a lower hit rate on plus-money sides can win.

### Gaps
- I could not verify Benter's exact pseudo-R² table or the α/β values from the primary PDF (blocked); the figures come from a secondary blog.
- I found no published Benter-style blend results for WNBA or NBA player props.
- I found no peer-reviewed source on a numeric "disagreement threshold" beyond which model edges should be distrusted.

---

## 5. Staking during validation (flat small stakes, fractional Kelly) and rules for stopping or scaling

### Takeaway
During validation, bet **flat and small** (or paper-trade) so that variance and estimation error cannot ruin the bankroll while evidence accumulates. Scale toward **fractional Kelly (¼–½)** only after CLV and calibration evidence is statistically solid. Estimated edges are biased upward (selection plus estimation error), and full Kelly on an overstated edge has *negative* growth. Half Kelly keeps about 75% of the growth rate with about half the variance.

### Cited Findings
- **Kelly properties:** MacLean, Thorp & Ziemba, *Long-term capital growth: the good and bad properties of the Kelly and fractional Kelly capital growth criteria* (*Quantitative Finance*, 2010):
  - Kelly "maximizes the limiting exponential growth rate of wealth," but recommended bets "can be very large," making it "very risky in the short term."
  - Fractional Kelly (blending Kelly with cash) reduces risk at the cost of lower expected final wealth.
  - Errors in estimated means matter far more than errors in variances, roughly **20:2:1** (Chopra & Ziemba).
  - Simulations show half Kelly is much less likely to fall to very low wealth levels than full Kelly.
  - Sources: [Berkeley-hosted PDF](https://www.stat.berkeley.edu/~aldous/157/Papers/Good_Bad_Kelly.pdf); [Edinburgh chapter](https://www.maths.ed.ac.uk/mckinnon/blackouts/StochOptFinanceAndEnergySpringer/Chap1_KellyZiemba.pdf) (via search abstracts)
- **Shrink Kelly when the edge is estimated:** Baker & McHale, *Optimal Betting Under Parameter Uncertainty: Improving the Kelly Criterion*, *Decision Analysis* 10(3):189–199 (2013):
  - Plugging estimated probabilities into Kelly gives worse out-of-sample than in-sample performance, so **bet size should be shrunk**.
  - Shrunken Kelly beat raw Kelly in simulation and on tennis betting data.
  - The paper gives a "back of envelope" shrinkage rule of thumb, which assumes a beta-distributed probability.
  - Sources: [INFORMS](https://pubsonline.informs.org/doi/fpi/10.1287/deca.2013.0271); [IDEAS](https://ideas.repec.org/a/inm/ordeca/v10y2013i3p189-199.html); [Metel, arXiv 1701.02814](https://arxiv.org/pdf/1701.02814)
- **Half-Kelly rule of thumb:**
  - "Betting half the Kelly amount gives three-quarters of the investment return with much less volatility" (e.g., 10% compound growth becomes 7.5%).
  - "It can be easy to over-estimate the true odds by a factor of two."
  - Half Kelly "sacrifices only about 25% of the long-term growth rate but reduces variance by 50%."
  - In the idealized model, the probability of a full-Kelly bankroll eventually halving is about ½.
  - Sources: [Wikipedia mirror: Kelly criterion](https://wikipedia2007.classicistranieri.com/k/e/l/Kelly_criterion.html); [LuxAlgo: Kelly criterion](https://www.luxalgo.com/library/concept/kelly-criterion/) (secondary)
- **Kelly at -110 [computed]** using f* = (b·p − q)/b with b = 0.9091:
  - p=0.55 gives **f* = 5.5% of bankroll**; p=0.54 gives 3.4%; p=0.53 gives 1.3%.
  - Half Kelly keeps **75.0%** of the full-Kelly log-growth rate at each p, which confirms the 3/4 rule.
- **Cost of overestimating the edge [computed]:** sizing for a believed 55% (f = 5.5%) gives the following growth per bet (expected log-growth):

  | True p | Full Kelly | Half Kelly | Quarter Kelly |
  |---|---|---|---|
  | 0.55 | +0.00138 | +0.00103 | +0.00060 |
  | 0.54 | +0.00032 | **+0.00051** (beats full) | — |
  | 0.53 | **−0.00073** | −0.00002 (≈0) | **+0.00008** |
  | 0.5238 (no skill) | −0.00138 | −0.00035 | −0.00009 |

- **Variance a real 55% bettor must sit through [computed, Monte Carlo]** for 1,000 flat 1u bets at -110 (expected profit +50u):
  - median maximum drawdown **≈21u**; 90th percentile **≈34u**; 99th percentile **≈50u**
  - longest losing streak: median 8, 90th percentile 10
  - P(still at or below break-even) is 18.7% after 250 bets and 11.3% after 500 bets (Section 1).
- **Survivorship as a cautionary base rate:** about 45 of more than 6,000 tipsters were statistically distinguishable from luck, and verified tipsters' yields fell from 17% to about 1% after verification. — [Dutching as a Business, Feb 2018](http://dutchingasabusiness.blogspot.com/2018/02); [Trademate Sports interview](https://www.tradematesports.com/en/blog/interview-betting-expert-joseph-buchdahl)

### Inferences
These rules are a synthesis of the sources above plus the [computed] figures. They are not taken from any single source.

- **Validation stake:**
  - Flat 0.25–1% of a *dedicated* bankroll per bet, or paper trading with exact timestamps and prices.
  - At 1u = 1% of bankroll, a p99 drawdown of about 50u is half the bankroll, so stakes above about 1% flat are too large during validation even for a genuinely +5% bettor.
- **Pre-register the plan before going live:**
  - the model version (frozen)
  - which markets and props are eligible
  - the edge threshold
  - price sources and the closing-line source
  - the sample size at which you will evaluate (e.g., 250 and 500 bets)
- **Primary metric:** mean CLV against a sharp devigged close, with SE and t-stat.
- **Secondary metrics:**
  - log loss and Brier of the blended probability vs the market
  - calibration slope
  - realized ROI with a confidence interval
- **Stop rules:**
  - After about 100–200 bets, mean CLV ≤ 0 with t < −1, or the model's log loss is no better than the devigged market's, means stop and diagnose (leakage, stale data, wrong line source). Do not keep betting.
  - Do **not** stop on P&L alone before about 500 bets, because about 11–19% of real 55% bettors are still underwater at 250–500 bets.
  - Do stop if realized results fall far below expectation, e.g., the cumulative P&L z-score vs the model's own expected EV is below about −2. That signals the model's probabilities are miscalibrated.
- **Scale rules:**
  - Increase stakes only when:
    1. CLV is positive with t ≥ 2–3 over at least a few hundred bets, *and*
    2. P&L is consistent with the CLV-implied EV (not necessarily significant on its own), *and*
    3. calibration on the live sample is acceptable.
  - Then move to ¼ Kelly using the *blended, shrunk* edge, and to ½ Kelly at most after a further independent sample.
  - Never use full Kelly with estimated edges (Baker & McHale; the overestimation table above).
- **Account for correlated exposure:** same-game props, the same player across books, and slips. Size by the combined exposure, not per ticket.
- **Market limits are part of the validation outcome:** if limits or account restrictions arrive (as in Kaunitz et al.), the realizable edge at scale is smaller than the backtest edge.

### Gaps
- I found no authoritative published "stop/scale" protocol for sports bettors. The rules above are synthesized.
- Sequential testing methods (SPRT or alpha-spending for repeated looks at live results) were not covered by any source I could retrieve. Repeatedly peeking at P&L without adjustment inflates false positives, the same forking-paths problem in time.
- Thorp's own sports-betting Kelly writings (e.g., *The Kelly Criterion in Blackjack, Sports Betting and the Stock Market*, 2006) were referenced only indirectly; I did not access the text.
