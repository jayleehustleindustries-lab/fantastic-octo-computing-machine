# NFL slate, market and situational check - Sunday Oct 11 / Monday Oct 12, 2026

Generated 2026-10-11 ~13:30 UTC. Scripts: `backtest.py`, `build_report.py` (same folder). Data: nflverse `games.csv`.

## READ FIRST
1. **Label mismatch.** The task said "Week 6", but in `games.csv` today's games (Sun Oct 11 + MNF Oct 12) are **season 2026, week 5**. Week 6 is Oct 15-19 (TNF SEA@DEN Oct 15, Sunday slate Oct 18, MNF WAS@SF). All analysis below is for the games actually being played today. KC and CAR are on bye; TB@DAL (Thu) already finished TB 24, DAL 16 (DAL was a -9.5 favorite).
2. **Lines come from two places that disagree.** `games.csv` gives one line per game with an unknown timestamp. It looks later than the web snippets for most games (totals/spreads trend the same way) but is **stale for CHI@GB** (CSV CHI -1.5, DraftKings reported -3 after Williams news). Web numbers are search-snippet summaries (all page fetches failed with DNS errors), mix snapshot times, and some results were visibly from older seasons and were discarded. No book was logged into or scraped.
3. **Result: zero picks.** No spot clears the bar once blended with the market (see decision math). Details below.

## Slate (CSV line; spread shown as favorite -pts)
Times are UTC (ET + 4). Rest = away/home days. ML % is no-vig.

| Kickoff | Game | Spread | Total | Moneyline | Rest | Site | QBs (CSV, projected) |
|---|---|---|---|---|---|---|---|
| Sun 13:30Z | PHI @ JAX | JAX -7.5 | 41.5 | PHI +300 / JAX -380 (24%/76% no-vig) | 7/7 | Tottenham Hotspur Stadium, London (JAX 'home') | Jalen Hurts / Trevor Lawrence |
| Sun 17:00Z | CHI @ GB | CHI -1.5 | 47.5 | CHI -125 / GB +105 (53%/47% no-vig) | 7/7 | Lambeau Field | Tyson Bagent / Jordan Love |
| Sun 17:00Z | CIN @ MIA | CIN -7 | 43.5 | CIN -345 / MIA +275 (74%/26% no-vig) | 7/7 | Hard Rock Stadium | Joe Burrow / Malik Willis |
| Sun 17:00Z | LV @ NE | NE -3.5 | 45.5 | LV +154 / NE -185 (38%/62% no-vig) | 7/7 | Gillette Stadium | Kirk Cousins / Drake Maye |
| Sun 17:00Z | MIN @ NO | MIN -1.5 | 41.5 | MIN -130 / NO +110 (54%/46% no-vig) | 7/6 | Caesars Superdome (dome) | Kyler Murray / Tyler Shough |
| Sun 17:00Z | CLE @ NYJ | NYJ -2.5 | 39.5 | CLE +114 / NYJ -135 (45%/55% no-vig) | 10/7 | MetLife Stadium | Deshaun Watson / Geno Smith |
| Sun 17:00Z | IND @ PIT | PIT -3 | 43.5 | IND +124 / PIT -148 (43%/57% no-vig) | 7/10 | Acrisure Stadium | Daniel Jones / Aaron Rodgers |
| Sun 17:00Z | HOU @ TEN | HOU -7 | 37.5 | HOU -345 / TEN +275 (74%/26% no-vig) | 7/7 | Nissan Stadium | C.J. Stroud / Cam Ward |
| Sun 17:00Z | NYG @ WAS | WAS -3.5 | 41.5 | NYG +154 / WAS -185 (38%/62% no-vig) | 7/7 | Northwest Stadium | Jameis Winston / Jayden Daniels |
| Sun 20:05Z | DEN @ LAC | DEN -3.5 | 41.5 | DEN -185 / LAC +154 (62%/38% no-vig) | 7/7 | SoFi Stadium (dome) | Bo Nix / Justin Herbert |
| Sun 20:25Z | DET @ ARI | DET -5.5 | 54.5 | DET -258 / ARI +210 (69%/31% no-vig) | 7/7 | State Farm Stadium (retractable) | Jared Goff / Jacoby Brissett |
| Sun 20:25Z | SF @ SEA | SEA -3 | 46.5 | SF +140 / SEA -166 (40%/60% no-vig) | 7/7 | Lumen Field | Brock Purdy / Drew Lock |
| Mon 00:20Z | BAL @ ATL | ATL -3 | 43.5 | BAL +145 / ATL -175 (39%/61% no-vig) | 7/6 | Mercedes-Benz Stadium (retractable) | Tyler Huntley / Michael Penix Jr. |
| Tue 00:15Z | BUF @ LA | LA -3.5 | 54.5 | BUF +154 / LA -185 (38%/62% no-vig) | 8/8 | SoFi Stadium (dome) | Josh Allen / Matthew Stafford |

## Per-game market, injury, weather notes (web snippets; verify before betting)
**PHI @ JAX** (Sun 13:30Z)
- Web lines (snippets): FD/DK JAX -7.5 tot 41.5 (Inquirer); older snaps JAX -4.5 (SI), PHI +4.5 tot 43.5 (NE Times) => line moved ~3 pts on injury news
- Injuries: PHI: Barkley OUT, D.Smith OUT (hamstrings, Fri final per Inquirer); Goedert hurt (status not found); L.Johnson retired, Jurgens traded to BAL. JAX: none found
- Weather: not found (London, outdoors)

**CHI @ GB** (Sun 17:00Z)
- Web lines (snippets): DK CHI -3 (-155) after move from -1.5 (SI, pre-Friday practice) vs CSV CHI -1.5 => CSV stale here
- Injuries: CHI: Caleb Williams (Gr2 hamstring) QUESTIONABLE, limited Fri; Bagent expected to start (Ben Johnson). GB: none found
- Weather: not found (outdoors)

**CIN @ MIA** (Sun 17:00Z)
- Web lines (snippets): Consensus CIN -7 (OddsShopper Oct 7), CIN -6.5/tot 42.5 (Legion Oct 8); VegasInsider 8.5/46.5 (older); ML -292..-335
- Injuries: CIN: Chase (concussion) Q, Higgins (groin/neck) Q - both full practice Fri; Dugger OUT. MIA: Achane out for season (ACL)
- Weather: not found (outdoors)

**LV @ NE** (Sun 17:00Z)
- Web lines (snippets): DK NE -3.5 (-110), ML -192/+160, tot 45.5 (SI)
- Injuries: NE: C.Davis III OUT (neck, DNP), Hollins DNP (calf), Stevenson Q (knee); A.J.Brown IR, Landry PUP. LV: none found
- Weather: Boston Globe 10/9 (low reliability, mentions a 2020 storm): cloudy, 60s, breeze 10-15 mph esp. 2nd half; Gillette mostly sheltered

**MIN @ NO** (Sun 17:00Z)
- Web lines (snippets): DK MIN -1.5 (-115), ML -130/+110, tot 42.5 (SI)
- Injuries: MIN: Darrisaw (concussion) OUT, Demmings OUT, Jefferson (ankle) Q, Addison (hamstring) Q. NO: Elliss OUT, Jennings OUT; Kamara, Blackmon, Styles Q; Shough (hand) full
- Weather: dome - n/a

**CLE @ NYJ** (Sun 17:00Z)
- Web lines (snippets): DK NYJ -1.5 (-112)/CLE +1.5 (-108) (SI); NBC NYJ -2.5; FD tot 40.5, SI 39.5; ML NYJ -130/CLE +110
- Injuries: CLE: Wallace Q, E.Jenkins Q, T.Jenkins Q, M.Graham Q. NYJ: Brownlee Q, McGregor OUT
- Weather: not found (outdoors)

**IND @ PIT** (Sun 17:00Z)
- Web lines (snippets): DK PIT -2.5 (-115), tot 44.5, ML -135/+114 (Oct 7 snap) -> CSV PIT -3/43.5 (moved toward PIT/under)
- Injuries: IND Oct 9: Bortolini (C) DNP ankle, Carlies DNP, Davis-Gaither DNP, Dulin DNP, Key DNP (out 3-4 wks); Allen/Taylor/Ward limited (rest). PIT: Dowdle Q (team attribution unclear). Final designations not found
- Weather: not found (outdoors)

**HOU @ TEN** (Sun 17:00Z)
- Web lines (snippets): SI: HOU -7 (-105) tot 39.5 ML -345; other SI: HOU -7.5, tot 37.5, ML -360 (moved from -6.5)
- Injuries: HOU: Al-Shaair Q, Crumedy Q, J.Smith Q, K.Murray Q; Tank Dell IR; Stroud 2026 status not found (CSV lists him as projected starter). TEN: Slater, Carmona IR
- Weather: not found (outdoors)

**NYG @ WAS** (Sun 17:00Z)
- Web lines (snippets): WAS -3.5 (opened -3), NYG +3.5 (-105/-112), ML -175..-180/+145..+150; tot 43.5 (most), 42.5 (one), down from 48.5 open => CSV 41.5 even lower
- Injuries: WAS: J.Daniels (elbow) expected to start/probable, Mariota MCL DNP; McLaurin, Diggs, Omenihu DNP Thu (final not found). NYG: Dart OUT; Nabers, A.Thomas limited
- Weather: not found (outdoors)

**DEN @ LAC** (Sun 20:05Z)
- Web lines (snippets): DEN -3.5 (-105)/LAC +3.5 (-115) FD, ML -184/+154; tot 42.5 (FD,SI) / 43.5 (FantasyAlarm)
- Injuries: DEN: Surtain II OUT (ankle, per Predictem), Moss Q (ribs), Sanders Q, Tillman Q. LAC: McConkey Q (foot); LAC 0-4 (0-3-1 ATS)
- Weather: dome - n/a

**DET @ ARI** (Sun 20:25Z)
- Web lines (snippets): DK DET -4.5 (-105)/ARI +4.5 (-115), tot 54.5, ML -218/+180 (older snap) -> CSV DET -5.5, ML -258/+210
- Injuries: ARI: LT Paris Johnson Jr. out for season (biceps); Baker, I.Adams DNP Wed; Love limited Wed; Brissett status not found. DET: Mays IR; Goff no injury found
- Weather: roof/indoors likely - not confirmed

**SF @ SEA** (Sun 20:25Z)
- Web lines (snippets): DK SEA -3 (+100)/SF +3 (-120), tot 46.5-47.5; opened SEA -2.5 -> -3 (Predictem); AN tot 46
- Injuries: SF: Bosa OUT; Juszczyk, Sigle doubtful (SI snap). SEA: L.Williams Q; QB UNRESOLVED - CSV lists Drew Lock, previews name Darnold (Q on Legion list); search returned only a Jan-2026 playoff story
- Weather: not found (outdoors)

**BAL @ ATL** (Mon 00:20Z)
- Web lines (snippets): SI/DK ATL -3 (-108)/BAL +3 (-112), tot 43.5, ML ATL -162; Covers ATL -2.5/45.5; FantasyAlarm ATL ML -185/tot 42.5. Lookahead was BAL -6 => ~9 pt swing
- Injuries: BAL: Lamar Jackson OUT (ankle) - Huntley starts; Humphrey DNP; Hendrickson unclear. ATL: Za'Darius Smith DNP/Q; Matthews, Ebukam, Deablo limited (Thu). ATL on 6 days rest (MNF)
- Weather: roof - n/a

**BUF @ LA** (Tue 00:15Z)
- Web lines (snippets): DK LA -2.5 (-118)/BUF +2.5 (-102), ML +124/-148, tot 54.5 (SI)/52.5 (Action) -> CSV LA -3.5, ML +154/-185 (line moved through 3)
- Injuries: BUF: D.J. Moore (WR) Q-doubtful side, Benford Q, Ed Oliver Q (knee), Sanders Q, Alford Q. LA: J.Watson Q, Mumpfield Q
- Weather: dome - n/a

Weather overall: no reliable 2026 wind forecast was found for any outdoor game (search kept returning 2017-2025 articles). Wind totals angle therefore cannot be applied to today.

## Line movement / book discrepancies spotted (from snippets, snapshot times unknown)
- BAL@ATL: BAL -6 lookahead to ATL -3 after Lamar Jackson ruled out (~9 pt swing; ATL -2.5 at Covers, -3 at DK). Fully repriced.
- PHI@JAX: roughly 3 pts of movement toward JAX on Barkley/D.Smith out and offensive line losses (JAX -4.5 earlier, now -7.5).
- BUF@LA: LA -2.5 (DK) to -3.5 (CSV), crossing the key number 3; ML -148 to -185.
- NYG@WAS: total 48.5 open to 43.5 to 42.5 (one book) to 41.5 (CSV): 2-pt book-to-book spread, almost certainly timing. WAS -3 to -3.5.
- CHI@GB: CSV CHI -1.5 vs DK CHI -3 (-155). Williams questionable - the single biggest unresolved QB uncertainty on the card besides SEA.
- SF@SEA: DK shows SEA -3 at +100 and SF +3 at -120 (juice shaded to the dog side); other snapshots SEA -2.5 and totals 46 to 47.5.
- IND@PIT: DK PIT -2.5 to CSV PIT -3, total 44.5 to 43.5.
- DEN@LAC / HOU@TEN / MIN@NO: totals differ by 1-2 pts across sources (42.5 vs 43.5; 37.5 vs 39.5; 41.5 vs 42.5). Key totals 41, 44, 47 are not at stake in any confirmed current line.
- DET@ARI: DET -4.5 (-218) older snapshot to -5.5 (-258) CSV.

## Situational backtest (nflverse closing lines, REG season 2015-2025, n = 2,895 games with lines)
Rule: a spot must have n >= 100, hit rate clearly above 52.4% (-110 break-even), survive a multiple-testing check, and be stable across 2015-20 vs 2021-25. 44 spots were tested, so about 2 would hit p < 0.05 by luck alone.

| Spot | n | Hit rate | z | p (2-sided) | Bonferroni p (44 tests) | 2015-20 | 2021-25 |
|---|---|---|---|---|---|---|---|
| Outdoor wind>=12 -> UNDER | 430 | 0.574 | 3.09 | 0.002 | 0.088 | 0.560 (n=241) | 0.593 (n=189) |
| Division games: bet road dog | 619 | 0.540 | 1.97 | 0.0489 | 1.0 | 0.537 (n=337) | 0.543 (n=282) |
| Home favs (any) -> bet HOME | 1710 | 0.477 | -1.93 | 0.053 | 1.0 | 0.467 (n=929) | 0.488 (n=781) |
| Outdoor wind<=5 -> UNDER (control) | 602 | 0.464 | -1.79 | 0.0729 | 1.0 | 0.441 (n=367) | 0.498 (n=235) |
| Total <=38 -> OVER | 146 | 0.431 | -1.66 | 0.0979 | 1.0 | 0.500 (n=44) | 0.402 (n=102) |
| Away team rest>=10 -> bet AWAY (any home rest) | 379 | 0.541 | 1.59 | 0.1113 | 1.0 | 0.551 (n=207) | 0.529 (n=172) |
| Away more rest by 3+ days -> bet AWAY | 340 | 0.541 | 1.52 | 0.1289 | 1.0 | 0.539 (n=193) | 0.544 (n=147) |
| Outdoor wind>=15 -> UNDER | 214 | 0.551 | 1.5 | 0.1326 | 1.0 | 0.512 (n=127) | 0.609 (n=87) |

Findings:
- **Nothing survives Bonferroni.** The best, outdoor wind >= 12 mph -> UNDER (247-183, 57.4%, n=430), has raw p about 0.002 but adjusted p about 0.09, the 12 mph cutoff was chosen after looking, and the effect is measured with game-time wind, not a day-before forecast. It is stable (56.0% then 59.3%) and the wind <= 5 control leans over (53.7% over), so it is plausible, but it cannot be applied today without a forecast.
- Home dogs ATS: 50.3% (n=1,059). Home dogs +3 or more: 51.2% (n=748). No edge.
- Road team off 10+ days rest: 54.0% ATS (n=326; 54.1% n=379 any home rest; away with 3+ more rest days 54.1%, n=340). Same direction both halves but z about 1.5, within noise. CLE@NYJ (CLE 10 days rest vs 7) is the only live instance; under the rule this is a lean, not a pick.
- Division road dogs 54.0% (n=619, p=0.049, halves 53.7%/54.3%); within noise after multiple-testing. Live: SF +3 at SEA, NYG +3.5 at WAS.
- Short-week home/away, 6-day-rest-vs-7, big favorites/dogs, high/low totals, domes, week-5 totals, cold: all within noise. 9:30 ET games n=29 and neutral n=49 are too small (reject). Wind >= 20: n=46 (reject).
- Key numbers (closing lines, 2015-2025): P(favorite wins by exactly 3) is 10.5% at -3, 9.3% at -3.5; exactly 7 is 6.1% at -7. Final margin = 3 on 14.7% of all games, 7 on 8.7%. A fav at -3 covers 43.8%, pushes 10.5%, dog covers 45.7%. This means a dog at +3.5 vs +3 is worth roughly +9 percent of ROI: **line shopping across 3 and 7 is the real, verifiable edge, but only if a book is actually off consensus, and none was confirmed.**
- Totals: closing total lines 41.5/43.5/44.5/47 lean under 53-58% in this sample (n 113-157 each) but are not significant individually, and none is confirmed as the current number.
- 2026 YTD (65 games): home 30-30-5 ATS, over/under 32-33, home dogs 12-9. Noise.

## Decision math (Benter blend, w = 0.3, p_market = 0.5 for a -110/pick'em line)
p_blend = 0.3*p_model + 0.7*0.5. A leg only has positive EV when p_model is at least:

| Bet type | Break-even | Required p_model |
|---|---|---|
| Sportsbook -110 side | 52.4% | 57.9% |
| Pick'em 2-pick (3x) | 57.7% | 75.7% |
| Pick'em 3-pick (6x) | 55.0% | 66.7% |
| Pick'em 4-pick (10x) | 56.2% | 70.7% |
| Pick'em 5-pick (20x) | 54.9% | 66.3% |

Best backtested angle (wind >= 12 under, 57.4%): p_blend = 0.3*0.574 + 0.35 = 52.2% vs 52.4% break-even, edge about -0.4%, and that already assumes the wind is certain. Road team off a mini-bye (54.1%): p_blend 51.2%, edge about -2.3%. Division road dog (54.0%): p_blend 51.2%, edge -2.3%. Large injury games (BAL, PHI, WAS total, BUF) were all repriced by 3-9 points before this check, so any edge there is gone; the market is more informative than my data.

## Why zero picks
1. No backtested situational edge clears break-even after blending, and none is multiple-testing-robust.
2. Every big injury I could verify (Jackson, Barkley/D.Smith, Surtain, Bosa, Paris Johnson, Darrisaw) is already in the move: BAL swung ~9, PHI ~3, BUF through the 3.
3. The only concrete value type (half-point at 3/7, +/-2 pts on totals) requires a confirmed off-market price, and snippets from different timestamps cannot confirm one. The apparent total gaps (WAS-NYG 41.5 vs 43.5, DEN-LAC 41.5 vs 43.5) are most likely the line sliding through the week, not live discrepancies.
4. Several decisive facts are unresolved: CHI QB (Williams vs Bagent), SEA QB (Lock vs Darnold, conflicting sources), HOU Stroud status, CIN Chase/Higgins (both questionable, full practice Fri), final PIT/IND lists, and all outdoor forecasts.

## Watch list - act only if verified live in your own book (these are NOT picks)
- If any book still posts NYG +3.5 at better than -110, or WAS -3 elsewhere: hook value is real (about +9 percent ROI per half point across 3), but the consensus is already 3.5.
- SF/SEA: if SF +3.5 appears anywhere vs consensus 3 (breakeven is generous: p(dog covers +3.5) about 56% when market is -3), that is a +EV price shop. SF +3 at -120 is not (about -5.7% EV on the backtested split).
- Totals: if a book is more than 1.5 pts off the CSV number (WAS-NYG under 43.5 vs 41.5; DEN-LAC under 43.5 vs 41.5), that crosses key numbers and is worth taking, since a 2-point gap is worth roughly 6-8 percent of win probability on a total (SD of final total minus closing line is 13.2 pts in this sample; empirically P(total within +2 of the line) is 57-59%).
- CHI@GB: if Williams is ruled out/in at kickoff the line should move 1.5-3 pts; do not bet before the inactive list (about 90 minutes pre-kick).
- CLE +2.5 at NYJ (10 days rest, 54% road mini-bye trend): lean only; p_blend 51.2% < 52.4% break-even.

## Sources (search snippets only; fetches blocked)
- nflverse games.csv: https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv (primary, downloaded)
- SI betting previews (DraftKings numbers) for Lions-Cardinals, Bills-Rams, 49ers-Seahawks, Colts-Steelers, Vikings-Saints, Texans-Titans, Browns-Jets, Broncos-Chargers, Raiders-Patriots, Ravens-Falcons, Eagles-Jaguars, Giants-Commanders (si.com/betting)
- SI: Ravens vs Falcons odds flip after Lamar Jackson injury; Concerning Caleb Williams update; Commanders odds with Jayden Daniels
- Inquirer (Eagles injuries, Oct 8-9, 2026); philadelphiaeagles.com injury report; WCPO and atozsports (Bengals Friday report); neworleanssaints.com / vikings.com (Week 5 injury reports); patriots.com injuries
- OddsShopper, Legion Report, Covers, ClutchPoints, FantasyAlarm (various lines); VegasInsider and ESPN Oct 5 snapshot (older); Boston Globe Oct 9 (weather, low reliability)
- Search results from earlier seasons (2017-2025) were discarded.
