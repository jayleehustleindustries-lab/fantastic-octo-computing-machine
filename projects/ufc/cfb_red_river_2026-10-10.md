# Red River Rivalry props: Texas vs Oklahoma, 2026-10-10, 2:30 PM ABC

## Read first: knowing people on the team
- I used only the data in your prompt plus general football rules.
- Do not bet on anything you hear privately: injuries, game plan, who's hurt, who's sitting. That counts as insider betting. It is a crime in many states and breaks every app's terms. It also puts the players you know at risk under NCAA rules.
- If you are close to players or staff, check your app's and your state's rules. Some bar people connected to a team from betting on its games.
- Never contact a player about a prop.
- Several states ban college player props outright. Confirm your app offers these legally where you are.

## Method: Benter-style, scaled down to what we have
1. **Fundamental estimate (p_f).** My probability, built from your stats and football logic. **Every p_f is an assumption.** Project Oklahoma has no college football model; it is WNBA only.
2. **Market estimate (p_m).** Taken from the prices with the vig removed:
   - Symmetric 1.87x/1.87x means 50%.
   - Manning TDs at 2.26x/1.48x means 60.4% Lower.
   - Oklahoma team total at -115 means about 51.1%, assuming the other side is -105.
   - Props with no odds shown are treated as standard 1.87x lines (an assumption).
3. **Blend: p = 0.5·p_f + 0.5·p_m.** Benter fit his weights on years of data. We have none, so we lean hard on the market.
4. **Edge and stake.** Edge = p·payout − 1. Full Kelly = edge ÷ (payout − 1). Stake = ¼ Kelly on an assumed bankroll of about **$33** ($38 minus the pending $5 WNBA slip).

**Confidence scale (estimated hit rate):** Low <55%, Medium 55–60%, High >60%.

**Problems in the data you gave me:**
- Texas pass defense appears twice with different numbers: 171.8 YPG (26th) and 122.5 YPG (4th). One of them is probably Oklahoma's. This weakens the Mateer and Manning passing reads.
- I assume Mateer plays for Oklahoma and Smothers for Texas, based on how the context describes them.
- Simmons's 5.5 sacks is one game. Expect him to come back toward normal.

## Popular Picks
| Pick | Lean | Confidence | p (blend) / break-even | Reasoning |
|---|---|---|---|---|
| J. Mateer Pass Yds 187.5 | Lower | Medium | 55% / 53.5%, edge +2.9% | Texas allows far fewer passing yards than 187.5 and Oklahoma's offense ranks 120th. But Oklahoma will likely trail and throw more, so the edge is thin. ¼ Kelly is about $0.27. |
| A. Manning Pass TDs 1.5 | Lower is likely to hit, but **don't bet it at 1.48x** | High (hit rate) | 62% / **67.6%**, edge **−7.9%** | Oklahoma's red-zone defense ranks 2nd and the game should be low scoring, so Lower should hit about 62% of the time. The 1.48x price needs 67.6% to break even, so the market has already priced this in. This is the board's most common correct pick and it is still a losing bet. |
| A. Manning Pass Yds 210.5 | **No edge, pass** | Low | ~50% | The analyst's Lower lean misses something. Oklahoma has the 5th-best run defense and Texas's line is struggling to run, which pushes Texas to throw (Higher). A Texas lead and clock-running would push it the other way (Lower). The two cancel out. |
| H. Smothers Rush Yds 47.5 | Lower | Medium | 56.5% / 53.5%, edge +5.7% | Oklahoma's run defense ranks 5th and Texas's line averaged 2.62 YPC against good defenses. At 3–4.8 YPC, Smothers needs 10–16 carries to reach 47.5. One long run, or carries to run out the clock, would beat this. ¼ Kelly is about $0.54. Best of the four. |

## Outlier Picks
| Pick | Odds/Line | Confidence | Reasoning |
|---|---|---|---|
| **Oklahoma Team Total Under 14.5** | -115 | Medium (57.5%) | Oklahoma scores 11.5 PPG against Power Four teams. Texas allows 13.3 PPG and has an elite red-zone defense. Oklahoma's turnover margin is −6. 14 is a key football score, and Under 14.5 still wins at exactly 14. Edge **+7.6%**, ¼ Kelly about $0.72. Risk: a defensive or return TD by Oklahoma counts toward its total. |
| **J. Mateer Rush Yds Under 14.5** | assumed 1.87x | Medium (57%) | In college football, sack yardage counts against the QB's rushing yards. Texas has an elite pass rush (Simmons) facing a struggling offense, so every sack lowers this number. Edge +6.6%, ¼ Kelly about $0.63. Risk: one long scramble. |
| C. Simmons Sacks Over 0.5 | line not given | Low (~52%, assumption) | Fits the same picture as the Mateer rushing Under. The 5.5-sack game is a one-game outlier. Play only at **+100 or better**. |
| J. Mateer INTs Over 0.5 | line not given | Low (~58%, assumption) | A turnover-prone offense facing an elite pass defense while trailing should throw interceptions. The −6 margin includes fumbles, though. Play only at **-120 or better**. |
| Texas D/ST Anytime TD | +500 | Low (~13%) | A lottery ticket. +500 needs 16.7% to break even; I estimate about 13%. Edge about **−22%**. **Pass.** |

**Correlation:** the five Oklahoma-offense-struggles picks move together. They are Mateer Pass Lower, Mateer Rush Under, Oklahoma Team Total Under, Simmons sacks Over and Mateer INT Over. Linked picks help a pick'em entry only if the app allows combining them. They also mean a single bad read on Oklahoma's offense loses every one of them together.

## Most likely to hit (not the same as best value)
1. Manning TDs Lower: about 62%, but **−EV at 1.48x**.
2. Oklahoma Team Total Under 14.5: about 57.5%.
3. Mateer Rush Under 14.5: about 57%.
4. Smothers Rush Lower 47.5: about 56.5%.
5. Mateer Pass Lower 187.5: about 55%.

## Best Value
**Oklahoma Team Total Under 14.5 at -115, as a straight bet.** It has the biggest edge (+7.6%) and the cleanest pricing.
- **Stake: about $0.72 at ¼ Kelly.** Use the app's minimum and never more than about $2.
- A $5 bet would be about 15% of your bankroll, roughly 1.7x full Kelly even if my estimates are right. That is over-betting.

**If you want a pick'em entry instead:** pair Mateer Rush Under 14.5 with Smothers Rush Lower 47.5.
- It pays only if the entry pays at least about 3.5x (1.87x × 1.87x). Then the EV is about +12.7%.
- On Dabble's fixed 3x 2-pick, the EV is **−3.4%**. Skip it there.

**Bottom line:** these edges come from my assumptions, not a tested model. Treat them as small, uncertain edges and size accordingly.

## After you approve
1. Save this card to `scratchpad/cfb_red_river_2026-10-10.md`. The paused build stays untouched.
2. When you tell me what you placed (exact line, price and stake), add it to `reports/tracking_ledger.csv` as PENDING.
3. Schedule one check-in after the game (about 23:30 UTC) to grade every pick against the box score. If you send closing lines, I'll compute CLV too.
