# Matheus Camilo vs Jai Herbert - fight research

UFC Fight Night: Allen vs. Duncan (aka UFC Vegas 122), Meta APEX, Enterprise/Las Vegas, Sat Oct 10, 2026. Camilo vs Herbert is the co-main, lightweight, 3 x 5 min. Main event is Allen (27-7) vs Duncan (15-2), middleweight, 5 rounds.

Co-main / card: https://combat-edge.com/news/ufc-fight-night-allen-vs-duncan-preview/ , https://cagesidepress.com/2026/09/01/brendan-allen-vs-christian-leroy-duncan-tops-ufc-vegas-122/

## Method and caveats (read first)

- Direct page fetches failed in this environment (WebFetch returned `getaddrinfo ENOTFOUND` for every host). Everything below comes from WebSearch result snippets/summaries only. I could not open UFCStats, Tapology, Sherdog or sportsbook pages.
- Search summaries are machine-generated and aggregator stats conflict between sites. Where they conflict I show both values and mark "unverified".
- Date flag: the task says the fight is "tonight, Oct 10". The environment/search clock reads Oct 11, and the search tool repeatedly treated the fight as already past. I searched for a result and found none (only pre-fight previews). If the fight has in fact finished, official results are not in this search index.
- Not found at all: weigh-in results, fighter-prop lines (Dabble/PrizePicks/Underdog), named striking/S&C coaches for either fighter, a direct "fight goes the distance" price, publicly reported injuries.

## Odds you were shown vs. what I found

- User's app: Camilo 1.52x, Herbert 2.59x. Converted: about -192 / +159. Implied 65.8% / 38.6% (sum 104.4%, ~4.4% vig). No-vig about 63.0% / 37.0% (my arithmetic).
- Opening line reported by several preview sites: Camilo -195, Herbert +165. So the app price (-192/+159) is essentially the opener. Source: https://www.docsports.com/free-picks/ufc/2026/matheus-camilo-vs-jai-herbert-pick-10-10-2026-predictions-ufc-vegas-122-odds.html , https://cagesidepress.com/2026/10/08/jai-herbert-plans-to-use-experience-against-matheus-camilo-at-ufc-vegas-122/
- YouWager.lv: favors Camilo, "moneyline -200 or better", expects TKO. https://blog.youwager.lv/2026/10/08/matheus-camilo-vs-jai-herbert-betting-prediction-october-10-2026/
- Prediction-market read: Polymarket roughly Camilo 64% / Herbert 37%; Statpick says market-implied Camilo about 62% after margin. https://www.sportytrader.com/en/betting-tips/matheus-camilo-jai-herbert-377322/ , https://www.statpick.ai/fights/mma/20453514/jai-herbert-vs-matheus-camilo
- Only two named books/lines seen (not the 2-3 requested): the opener (-195/+165, from DocSports) and BetUS props. A third sportsbook moneyline was not found.

### Method of victory (BetUS, via snippet; price freshness unverified)
https://www.betus.com.pa/sportsbook/martial-arts/props/jai-herbert-vs-matheus-camilo/

| Outcome | Price | Raw implied | Normalized (my math, removes ~19% overround) |
|---|---|---|---|
| Camilo KO/TKO/DQ | +125 | 44.4% | ~37% |
| Camilo decision | +375 | 21.1% | ~18% |
| Camilo submission | +1000 | 9.1% | ~8% |
| Herbert KO/TKO/DQ | +450 | 18.2% | ~15% |
| Herbert decision | +375 | 21.1% | ~18% |
| Herbert submission | +2500 | 3.8% | ~3% |
| Draw | +8000 | 1.2% | ~1% |

- Derived (unverified, my arithmetic): Camilo total normalizes to about 63%, matching the moneyline. Decision (either man) about 35%; any finish about 64%. No direct "goes the distance" line was found.
- Prop lines (Dabble / PrizePicks / Underdog sig strikes, takedowns, fight time): not found.

## 1. Camp and coaching

### Matheus Camilo
- Gym: Xtreme Couture, Las Vegas, NV (UFC.com lists it; ESPN lists Team Xtreme Couture). https://www.ufc.com/athlete/matheus-camilo , https://www.espn.com/mma/fighter/bio/_/id/5170144/matheus-camilo
- Earlier base: Nova Uniao in Brazil; Sherdog's prospect piece credits gym time at Nova Uniao and Xtreme Couture. https://stg-www4-cdn.sherdog.com/news/articles/Sherdog-Prospect-Watch-Matheus-Camilo-196989
- Time in Vegas: one summary says about four years (from a Yahoo piece; exact figure unverified). https://au.sports.yahoo.com/full-circle-moment-matheus-camilo-164511748.html
- Teammates named: Mairon Santos and Nikolas Motta (fellow Brazilians at the gym) - same Yahoo piece.
- Head coach: Camilo's personal head coach is not found. Xtreme Couture's head coach / GM is Eric Nicksick, but no source ties Nicksick to Camilo's corner (unverified). https://www.lowkickmma.com/eric-nicksick/ ; a corner check for UFC 322 found nothing.
- Other XC coaches listed on a gym profile: Dennis Davis, Kyle Griffin (roles not stated). https://www.lowkickmma.com/xtreme-couture/
- Striking coach, grappling/wrestling/BJJ coach, S&C coach: not found.
- Camp change in last 2 years: not found. Nothing suggests one; he has been at XC for years per the above.

### Jai Herbert
- Gym: Renegade Jiu-Jitsu / Team Renegade, Birmingham, UK (UFC.com lists Renegade Jiu-Jitsu). https://www.ufc.com/athlete/jai-herbert , https://sportsgazette.co.uk/?p=21005
- Wikipedia teams: Team Renegade, Team Kaobon (England), MTK Global. https://en.wikipedia.org/wiki/Jai_Herbert
- Head coach: not found. Team Renegade's Wikipedia page names primary trainers and a "decentralized" coaching approach (names in the snippet were unreliable, so not repeated). https://wikipedia.com/wiki/Team_Renegade
- Grappling: BJJ brown belt under Tom Caughey (Wikipedia; Caughey's role unconfirmed by any other source). Tom Breese (ex-UFC) is a coach/partner at Renegade and has taught there; several sources say Herbert trained at Renegade with Breese mainly for jiu-jitsu and wrestling. https://www.expressandstar.com/sport/sports-reporter-v-professional-fighter-inside-an-mma-class-at-team-renegade-5872758 , https://www.mmaplus.co.uk/round-up/ufc/breese-relishing-new-middleweight/
- Striking: an older interview named Kirkwood Walker and Joby Clayton (Firewalker) as striking coaches. Date of that interview and whether still current: unverified. https://www.fightersonlymag.com/?p=10730
- S&C coach: not found.
- Camp change in last 2 years: not found. (An older interview mentioned considering a camp in Holland; no evidence he went.)

## 2. Gym / coach reputation

- Xtreme Couture: Nicksick has been head coach/GM since rising through the gym after joining in 2006; MMAjunkie Coach of the Year 2020; coached Francis Ngannou and Sean Strickland; also tied to Aljamain Sterling and Dan Ige. https://www.lowkickmma.com/eric-nicksick/ , https://www.streetinsider.com/Press+Releases/Alta+Global+Group+Partners+with+Legendary+MMA+Coach+Eric+Nicksick/23328900.html . Known as a top all-around MMA camp. Specific cardio/pace or wrestling/striking identity: not found. Recent results of other XC fighters: not found.
- Team Renegade: Birmingham gym that is the home of Leon Edwards; identity is jiu-jitsu-first (the club is "Renegade Jiu-Jitsu"). https://www.ufc.com/news/team-renegade-hopes-breed-champs-positively-impact-community-leon-edwards . Teammates seen: Tom Breese, Will Jones (class write-up). Recent results of the camp's fighters: not found.

## 3. Martial-arts base and physicals

| | Camilo | Herbert |
|---|---|---|
| Age / DOB | 25, born Jan 2, 2001 | 38, born May 13, 1988 |
| Height | 5'10" (178 cm) | 6'1" (73 in) |
| Reach | 69" | 77" |
| Stance | Orthodox | Orthodox |

Sources: Camilo physicals https://www.ufcalendar.com/fighters/matheus-camilo , https://bjjmetrics.com/ufc/fighter/72f890c5d421e705 (summary says sources agree on measurements). Herbert https://en.wikipedia.org/wiki/Jai_Herbert , https://www.ufc.com/athlete/jai-herbert (UFC page may lag by a year on age). Herbert's 6'1" conflicts with the "5'10"" figure in one query; sources list 6'1".

- Camilo: BJJ brown belt per Combat Edge (https://combat-edge.com/fighter/matheus-camilo-3019/ ); lineage not found. Wrestling credentials, striking/kickboxing background, amateur career: not found. Nova Uniao background (Brazilian MMA/BJJ-heavy lineage; I am inferring nothing beyond the gym name). Pro career includes Shooto Brazil and Fury FC. https://www.espn.com/mma/fighter/history/_/id/5170144/matheus-camilo
- Herbert: listed style Muay Thai; BJJ brown belt (Caughey). Former Cage Warriors lightweight champion (won title June 29, 2019 at CW 106 vs Jack Grant, one defense, vacated to sign with the UFC in 2020). Spent 14 years as a scaffolder while fighting. Fighters Only says he fit in boxing, kickboxing, Muay Thai, BJJ sessions around a full-time job; a formal kickboxing record was not found. https://en.wikipedia.org/wiki/Jai_Herbert , https://www.fightersonlymag.com/?p=10377 , https://stg-www4-cdn.sherdog.com/news/articles/5-Things-You-Might-Not-Know-About-Jai-Herbert-185432

## 4. Record and form

### Camilo
- Pro: 11-3 (UFC.com still shows 10-3; one aggregator says "4 career losses, all submissions", which doesn't fit 11-3 - treat as unverified). UFC: 2-1. Seven career finishes. https://www.lowkickmma.com/matheus-camilo-ko-nazim-sadykhov-ufc-baku/ , https://www.ufcalendar.com/fighters/matheus-camilo
- Days since last fight: 105 (Jun 27 -> Oct 10, my count).
- Last fights, most recent first:
  1. W Nazim Sadykhov, TKO (punches), R1 1:31, Jun 27 2026, UFC Baku. Counter right hand as Sadykhov stepped in; crowd protested the stoppage as early. https://www.lowkickmma.com/matheus-camilo-ko-nazim-sadykhov-ufc-baku/ , https://cagesidepress.com/2026/06/27/matheus-camilo-drops-nazim-sadykhov-silences-crowd-at-ufc-baku/
  2. W Viacheslav Borshchev, UD (30-27, 30-27, 29-28), Nov 15 2025, UFC 322 (MSG). 5 of 10 takedowns, 3:22 control vs 0:24; mount and arm-triangle attempts. ESPN's grade called it workmanlike. https://www.ufcalendar.com/events/ufc-2025-11-15/matheus-camilo-vs-viacheslav-borshchev , https://africa.espn.com/mma/story/_/id/46998777/ufc-322-fight-grades-valentina-shevchenko-islam-makhachev-too-good-exciting
  3. L Gabe Green, rear-naked choke (UFC.com/UFCalendar; RotoWire says face crank), R2 3:43, May 17 2025, UFC Vegas 106 (debut, -186 to -225 favorite). R1 Camilo took Green down but was dropped to a knee by a check hook; R2 he locked a triangle, Green slammed out, took the back and finished. https://cagesidepress.com/2025/05/17/ufc-vegas-106-returning-gabe-green-spoils-matheus-camilos-debut
  4. W Dorian Ramos, triangle armbar, Fury FC 83, Sept 2023 (date per snippet). https://www.espn.com/mma/fighter/history/_/id/5170144/matheus-camilo
  5. Not found (fight between Sept 2023 and May 2025).
- Withdrawn from UFC 321 (Oct 25, 2025, vs Abdul-Kareem Al-Selwady) per a RotoWire note; reason not found. https://www.rotowire.com/mma/player.php?id=2640
- Earlier losses: Aric Mercado, guillotine, Fury FC 57, Feb 2022 (R1 per ESPN, R2 per UFCalendar); Derick Borges, submission R1 4:03, Shooto Brazil 98, Nov 2019. https://africa.espn.com/mma/fighter/history/_/id/5170145/aric-mercado
- Pattern: wins by takedown-heavy control, submissions, and one counter-KO; all listed losses are submissions; no KO/TKO loss found.

### Herbert
- Pro: 14-6-1 (10 KO/TKO wins, 1 submission). UFC: about 5-5-1 (roster.watch showed 4-5-1 before the Nallo win, so 5-5-1 after; that page was flagged as out of date, so unverified). https://www.roster.watch/fighters/jaiherbert.html https://www.ufc.com/athlete/jai-herbert
- Days since last fight: 175 (Apr 18 -> Oct 10, my count).
- Last five UFC fights, most recent first:
  1. W Mandel Nallo, TKO (punches/GnP), R1 2:05, Apr 18 2026, UFC Winnipeg. Dropped twice by a right hook inside the first minute, then dropped Nallo with a right hand and finished; Nallo survived a leg-lock threat. https://cagesidepress.com/2026/04/18/jai-herbert-stuns-mandel-nallo-with-comeback-tko-at-ufc-winnipeg/ , https://agentmma.com/news/42955-jai-herbert-knocks-out-mandel-nallo-in-wild-first-round-finish
  2. L Chris Padilla, split decision, Mar 22 2025. https://africa.espn.com/mma/fighter/history/_/id/4078246/jai-herbert
  3. W Rolando Bedoya, decision, Aug 3 2024, UFC Abu Dhabi (dropped Bedoya early). https://cagesidepress.com/2024/08/03/ufc-abu-dhabi-jai-herbert-vs-rolando-bedoya
  4. L Fares Ziam, UD, Jul 22 2023.
  5. D Ludovit Klein, draw, Mar 18 2023, UFC 286.
- Earlier: W Kyle Nelson UD Jul 2022 (29-28 x3; Nelson out-struck him, Herbert had more control); L Ilia Topuria KO R2 1:07, Mar 19 2022; L Renato Moicano RNC R2 4:34, Jun 2021; W Khama Worthy TKO R1, Oct 2021. https://www.expressandstar.com/sport/2022/03/21/wolverhamptons-jai-herbert-suffers-knockout-ufc-defeat , https://cagesidepress.com/2022/07/23/sufc-london-jai-herbert-spoils-kyle-nelsons-lightweight-debut , https://cagesidepress.com/2021/10/23/ufc-vegas-41-results-jai-herbert-finishes-khama-worthy-in-a-little-over-two-minutes
- Also reported (unverified, one fighter-record listing): TKO loss to Francisco Trinaldo, July 2020; BAMMA loss to Rhys McKee, Dec 2016. SportyTrader says Herbert "has lost three fights by knockout", which lines up with Topuria + Trinaldo + McKee.
- Pattern: wins mostly by early knockout (10 KO wins) or close decisions; losses by KO to a top striker, one submission (Moicano), and decisions. Fights have gone to decision five of his last seven. He had lost four of ten before the Nallo win. Chin: dropped twice by Nallo and KO'd by Topuria; he recovers but does get hurt.

## 5. UFC career stats (aggregators; they disagree)

| Stat | Camilo | Herbert |
|---|---|---|
| Sig. strikes landed/min | 2.22 (UFCalendar); 2.19 (BJJMetrics/AgentMMA) | 3.19 (AgentMMA/DocSports preview); 3.07 (another source) |
| Striking accuracy | 43% | about 40% (one source) |
| Sig. strikes absorbed/min | 3.05 (UFCalendar); 3.25 (BJJMetrics/AgentMMA) | 3.26 - 3.34 |
| Striking defense | 66% (UFCalendar/DocSports); 64% (BJJMetrics) | 52% |
| Takedowns/15 min | 4.16 (UFCalendar); 4.4 - 4.43 (others) | not found (opponent TD data absent) |
| Takedown accuracy | 53% | 21% (BJJMetrics/DocSports) |
| Takedown defense | not reliable ("0%" on one site = tiny sample, unverified) | 66% on one site; another site shows no figure (unverified) |
| Sub attempts/15 | not found | not found |
| Finish rate (pro) | 7 of 11 wins (about 64%) | 11 of 14 wins (about 79%: 10 KO + 1 sub) |

Sources: https://www.ufcalendar.com/fighters/matheus-camilo , https://bjjmetrics.com/ufc/fighter/72f890c5d421e705 , https://agentmma.com/fighters/4461-matheus-camilo , https://bjjmetrics.com/ufc/fighter/4c88a1db5a46c6a4 , https://agentmma.com/ru/fighters/3847-jai-herbert , https://www.docsports.com/free-picks/ufc/2026/matheus-camilo-vs-jai-herbert-pick-10-10-2026-predictions-ufc-vegas-122-odds.html , https://www.ufc.com/athlete/jai-herbert

## 6. Fight week

- Weigh-ins (Fri Oct 9): results not found for either man; no missed-weight report found for this card; no missed-weight history for either found. Official numbers: UFC.com / ESPN weigh-in page.
- Short notice / replacement: none found. Bout was "targeted for Oct 10" well in advance. https://agentmma.com/news/87567-matheus-camilo-vs-jai-herbert-targeted-for-oct-10
- Injuries: none publicly reported in what I could see.
- Camilo quotes: "I come for violence, I come for a finish." "If he makes a mistake, he's going down." Plans to press Herbert in the smaller APEX cage (25 ft vs 30 ft standard), sees Herbert as vulnerable on the ground and when opponents close distance; respects Herbert's striking. (A summary also says he "sometimes struggles on the ground" - ambiguous/garbled, unverified.) https://mmasucka.com/news/matheus-camilo-sees-openings-in-jai-herberts-game-ahead-of-ufc-fight/ , https://mmasucka.com/news/matheus-camilo-sees-apex-cage-as-advantage-against-jai-herbert/
- Herbert quotes: experience is his edge over the younger Camilo; calls Camilo good all-around ("he can box, he can wrestle"); APEX cage "a bit smaller, but more intense"; wants to remind the "talented young fighter" there are levels; not fixated on co-main billing. https://cagesidepress.com/2026/10/08/jai-herbert-plans-to-use-experience-against-matheus-camilo-at-ufc-vegas-122/
- Preview consensus: most previews pick Camilo; one model projects Camilo by decision, another (59%) favors Camilo. https://ats.io/matchup/ufc/jai-herbert-vs-matheus-camilo-prediction-10-10-2026/

## 7. Matchup analysis (my opinion, built on the thin data above)

Range control. Herbert has 8" of reach and 3" of height, a Muay Thai base, and out-lands Camilo on volume (about 3.2 vs 2.2 SLpM). He wants distance, jabs/front kicks, and the right hand. The 25-ft APEX shrinks his room to circle, and Camilo is a pressure fighter who looks for takedowns against the fence. Herbert's weak point is that he is hit often (52% defense, ~3.3 absorbed/min), which suits an opponent who counters well: Camilo's R1 finish came off a timed right hand as Sadykhov stepped in.

Wrestling vs takedown defense. Camilo's one clear edge: 4+ takedowns per 15 at 53% and strong control time against Borshchev (3:22 vs 0:24). Herbert's takedown defense is unclear (66% on one site, no figure on another) and his own takedown offense is poor (21%). Control time is how Camilo wins rounds even when out-struck. The risk for Camilo is the transition game: Green swept a triangle attempt into back control and a choke, and Mercado caught him in a guillotine, so Camilo's submission hunting from the top has cost him. Herbert is a brown belt and threatened a leg lock on Nallo, but only 1 of his 14 wins is a submission, so the sub-on-Camilo path is thin (BetUS +2500).

Power and chin. Herbert has 10 KO wins and genuine one-shot power, but has been finished by Topuria (R2) and was dropped twice in a minute by an unproven Nallo; he is 38 and 175 days off. Camilo has no KO/TKO loss on record and finished a fighter by counter, though he was dropped by a check hook in R1 of the Green fight and his UFC sample is small (under 6 rounds before Baku, my estimate from Green R1-R2 plus 3 rounds vs Borshchev). Herbert's best chance to land clean is an early right hand as Camilo walks in.

Cardio in round 3. No direct cardio data was found for either man. Herbert has gone to decision five of his last seven, so he can go 15 minutes, though age and the long layoff are question marks. Camilo goes forward and wrestles, which is cardio-heavy, but he went the full 3 rounds with 10 takedown attempts against Borshchev. Treat cardio as roughly even with a mild lean to the younger man.

Likely game plans (inferred, since no coach commentary was found). Camilo: pressure behind feints, trap Herbert on the fence, shoot or hit single-leg/double-leg from the clinch, look for a counter right, keep hips heavy on top and avoid the scrambles where Green beat him. Herbert: long jab and kicks, circle off the fence, sprawl-and-strike, stay on the outside, check low takedowns with knees and underhooks, and try for an early finish when Camilo steps in.

Lean: Camilo, by decision with grappling control, or by TKO if Herbert's defense breaks. My estimate is roughly 62-65%, close to the 63% no-vig market price, so I see little pricing edge on Camilo at -192. Herbert's real path (about 35-38%): (1) an early or mid-fight knockout, most likely R1-R2 on a right hand or body/head combination as Camilo closes (Herbert KO/TKO about 15% normalized), or (2) stuff early takedowns, keep it standing in the middle of the cage, and out-point a lower-volume Camilo over 15 minutes (Herbert decision about 18% normalized). A Herbert submission is unlikely. If Camilo can get Herbert down and hold him there in two of three rounds, the fight goes his way; if the first takedown attempts fail and Herbert lands the right hand clean, the underdog price is live. Confidence in this lean is moderate; the stat sources conflict and key inputs (takedown defense, coaches, cardio, weigh-in) are missing.
