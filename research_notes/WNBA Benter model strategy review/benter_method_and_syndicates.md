# Benter's Method, Modern Betting Syndicates, and What Transfers to Small-Stakes WNBA Player Props

Research date: 2026-10-10. Method note: in this session, outbound page fetches (WebFetch and curl) were blocked by the environment's egress proxy, so every finding below comes from search-engine result summaries and snippets. I did not read the primary documents in full (Benter's PDF, the Bloomberg article, Pinnacle articles). Each claim is cited to the URL the search surfaced, and conflicts and secondhand items are flagged.

## Q1. What are the stages of Benter's 1994 paper, how big was the edge, and what was the most important ingredient?

### Takeaway
Benter's system has these parts: (1) a large hand-built database, (2) a fundamental model, a multinomial/conditional logit that rates each horse, (3) a second-stage logit that combines the fundamental model's probabilities with the public's pari-mutuel implied probabilities, and (4) a wagering stage that uses Kelly-style sizing, scaled down to account for estimation error and his own market impact. The paper's central result is that the combined model fits better than either the public odds or the fundamental model alone. The fundamental model is not unbiased independently of the public, so blending with the market is the key step. The size of the edge is documented only in unaudited 1990s press estimates (about 24% average return) and in the 2018 Bloomberg figure of "close to a billion dollars" over his career.

### Cited Findings
- Citation: William Benter (HK Betting Syndicate), "Computer Based Horse Race Handicapping and Wagering Systems: A Report." Reprinted as Ch. 19, pp. 183–198, of *Efficiency of Racetrack Betting Markets* (World Scientific, 2008 edition), edited by Hausch, Lo & Ziemba. The Southampton repository lists the book-section version as Academic Press, 1995, and a 1993 ORSA conference version also exists. — [World Scientific](https://worldscientific.com/doi/abs/10.1142/9789812819192_0019); [Southampton eprints](https://eprints.soton.ac.uk/51684); [Gwern PDF mirror](https://gwern.net/doc/statistics/decision/1994-benter.pdf); [DataGolf PDF mirror](https://datagolf.com/static/blogs/benter_paper.pdf)
- The abstract says the paper covers "data requirements, handicapping model development, wagering strategy, and feasibility." It describes "a logit-based technique and a corresponding heuristic measure of improvement for combining a fundamental handicapping model with the public's implied probability estimates." It reports "significant positive results in five years of actual implementation." — [Gwern PDF](https://gwern.net/doc/statistics/decision/1994-benter.pdf); [Semantic Scholar](https://www.semanticscholar.org/paper/Computer-Based-Horse-Race-Handicapping-and-Wagering-Benter/2ea3ed4fa5ea9645614d76dd0a79201740949566)
- The fundamental model is a multinomial logit following Bolton & Chapman (1986). — [Gwern PDF via search summary](https://gwern.net/doc/statistics/decision/1994-benter.pdf)
- Two-stage structure as summarised in a UCLA dissertation: "In stage one, he uses a conditional logit to calculate the 'strength' of a horse. In the second stage, he combines the strength measure with the public's predicted probability using a second conditional logit function." — [UCLA eScholarship dissertation](https://escholarship.org/content/qt9tm6w0rp/qt9tm6w0rp_noSplash_490c4af635510cf20ca3a62a7156f5d4.pdf)
- Data hygiene in the second stage: the fundamental model is estimated on one part of the training data, and the combining model (model and public probabilities as predictors) on another part. — [GitHub: chris-alex-p/german-horse-racing, analysis_benter_methods.md](https://github.com/chris-alex-p/german-horse-racing/blob/main/notebooks/analysis_benter_methods.md)
- Second-stage functional form, as widely reproduced from the paper (I could not check it against the PDF this session): c_i = exp(α·f_i + β·π_i) / Σ_j exp(α·f_j + β·π_j), where f_i = log(fundamental probability) and π_i = log(public implied probability). α and β are fitted by maximum likelihood on held-out races. — [Gwern PDF](https://gwern.net/doc/statistics/decision/1994-benter.pdf) (not directly verified)
- Benter warns that the fundamental model's probabilities "cannot be considered to be an unbiased estimate independent of the public's estimate." This is why the second-stage correction matters. — [Gwern / DataGolf PDF via search summary](https://datagolf.com/static/blogs/benter_paper.pdf)
- Goodness-of-fit table (pseudo-R²). **The sources conflict:**
  - A forum summary of the 1988–1993 table gives: public estimate ≈ .1218, fundamental model ≈ .1245, combined ≈ .1396. — [PaceAdvantage forum archive](http://www.paceadvantage.com/forum/archive/index.php/t-110306.html)
  - An OCR reading of the PDF gives: public ≈ .1237, fundamental alone ≈ .1016 (out-of-sample), "tipster" model ≈ .1014, fundamental+public ≈ .1327, tipster+public ≈ .1239. The search tool noted the OCR was garbled. — [DataGolf PDF](https://datagolf.com/static/blogs/benter_paper.pdf); [Gwern PDF](https://gwern.net/doc/statistics/decision/1994-benter.pdf)
  - Both readings agree on direction: combined > either alone. A tipster's opinion adds almost nothing on top of the public odds ("the public's estimate is superior").
- Sample size and period also conflict. One summary says 2,313 Hong Kong races from Sept 1988 to June 1993, and another reading of the abstract says Sept 1986 through June 1993. — [Gwern PDF](https://gwern.net/doc/statistics/decision/1994-benter.pdf); [Semantic Scholar](https://www.semanticscholar.org/paper/Computer-Based-Horse-Race-Handicapping-and-Wagering-Benter/2ea3ed4fa5ea9645614d76dd0a79201740949566)
- Staking (secondary source): Benter used Kelly staking "with two important modifications": fractional Kelly to reduce sensitivity to estimation error, and limits that reflect the bettor's own market impact on pari-mutuel odds. — [LinkedIn Pulse: "Cracking the Code: Bill Benter's Horse Racing Model"](https://www.linkedin.com/pulse/cracking-code-bill-benters-horse-racing-model-its-gutse)
- An academic paper on Kelly betting at the races with uncertain probability estimates notes that betting half the Kelly amount is "popular amongst gamblers" and analyses why estimation uncertainty argues for betting less than full Kelly. — [arXiv 1701.02814](https://arxiv.org/pdf/1701.02814)
- Edge magnitude, from 1990s press estimates that are not audited: the system lets Benter's group "average a 24% return," about $37 million a year, betting about $260,000 per race across about 600 Hong Kong races a year. — [Casino.org blog](https://www.casino.org/blog/bill-benter/); [Trade2Win thread quoting the same article](https://www.trade2win.com/threads/making-millions-betting-on-horses.27107/)
- Bloomberg Businessweek (Kit Chellel, May 3, 2018): Benter "wrote an algorithm that couldn't lose at the track. Close to a billion dollars later, he tells his story for the first time." — [Bloomberg](https://www.bloomberg.com/news/features/2018-05-03/the-gambler-who-cracked-the-horse-racing-code)

### Inferences
- The paper's main teaching is that the market is the prior. Benter did not try to replace the public odds. He estimated how much independent information his model added on top of them, using the fitted α and β. A modern WNBA prop modeler can do the same: use the de-vigged sharp sportsbook line as π, use their own projection as f, and let a held-out logit decide the weights.
- A fundamental model that fits worse than the market on its own can still be profitable when combined with it. In the OCR reading, the fundamental model alone (≈.10) is worse than the public (≈.12), yet the combination (≈.13) beats both. A prop model does not need to be better than the book. It needs to carry information the book's price does not.
- The tipster result is a warning for prop bettors who rely on touts, Discord picks, or "expert" consensus. Those signals mostly repeat what the market already knows.

### Gaps
- I could not read Benter's PDF directly. I have not verified the exact pseudo-R² values, the exact sample, his verbatim "feasibility" remarks, or his exact fractional-Kelly multiplier. The two sets of R² figures above conflict.
- I found no primary source for which single ingredient Benter called "most important." The importance of combining with public odds is inferred from the paper's structure and fit table, not from a quoted sentence.
- An annotated walk-through exists ([actamachina.com "Revisiting the Algorithm that Changed Horse Race Betting"](https://actamachina.com/posts/annotated-benter-paper)), but I could not fetch it.

## Q2. How long did it take Benter and Woods to become profitable, how much data and staff did they use, and what failed early?

### Takeaway
The partnership started in Hong Kong around 1984–85 with about $150,000. They lost most of it in the first season, so the bankroll was down to about $30,000 by summer 1986, and the early program produced "bizarre predictions" that Woods had to correct by hand. The partners split. Benter rebuilt his bankroll by counting cards, returned in 1988, won about $600,000 that year and about $3 million the next, and by 2018 had made close to $1 billion. In other words, it took roughly 3–4 years from the first attempt to a robust profit, plus a database and model-development effort a 2019 slide deck estimates at around 5 man-years.

### Cited Findings
- Benter's interest started with Edward Thorp's 1962 blackjack book *Beat the Dealer*. — [Bloomberg (2018)](https://www.bloomberg.com/news/features/2018-05-03/the-gambler-who-cracked-the-horse-racing-code)
- Arrival dates conflict. One account says the two moved to Hong Kong in 1984, and another says Benter joined Woods there in September 1985. — [Paper to Profit substack](https://papertoprofit.substack.com/p/bill-benter-the-math-whiz-who-beat); [PokerTube](https://www.pokertube.com/article/bill-benter-the-man-who-won-nearly-1-billion-betting-horses)
- Early losses: starting budget $150,000; "in their first season betting on the Hong Kong horse races, they lost $120,000 of their bankroll, leaving them with $30,000." Another account says the bankroll was down to $30,000 "by the summer of 1986." — [secondary profiles, e.g. Casino Reviews](https://www.casinoreviews.net/blog/profiles/bill-benter-the-man-who-won-1-billion-dollars-betting-on-horses/); [OnlineGamblingWebsites](https://www.onlinegamblingwebsites.com/blog/bill-benter-the-man-who-won-1-billion-betting-on-horse-racing/)
- What failed early (Bloomberg via search snippet): "the betting program Benter had written spat out bizarre predictions, and Woods, with his yearlong head start studying the Hong Kong tracks, would correct them." — [Bloomberg](https://www.bloomberg.com/news/features/2018-05-03/the-gambler-who-cracked-the-horse-racing-code)
- The partners split over money. One low-quality profile claims Woods wanted a 90% stake, which is unverified. Woods kept betting and won HK$3 million in the 1987–88 season running his own operation. — [Paper to Profit substack](https://papertoprofit.substack.com/p/bill-benter-the-math-whiz-who-beat); [Alan Woods (Wikipedia)](https://en.wikipedia.org/wiki/Alan_Woods_(gambler))
- Benter returned in 1988 after rebuilding his bankroll by counting cards. He "ended up winning $600,000 in 1988 and hit $3 million in profits the following year." — [Bill Benter (Wikipedia)](https://en.wikipedia.org/wiki/Bill_Benter)
- Model-development effort is put at "~5 man-year," alongside a web crawler of about 300K records, in a 2019 HKIE talk on machine learning for HK racing. That figure belongs to the talk's own project, not to Benter. — [Dennis Li, HKIE, Jan 2019](https://hkie.org.hk/Docs/Events_Activities/veneree/2019/Horse%20Racing%20Machine%20Learning%20Public.pdf)
- A dissertation summary says "Benter reports that his team has made significant profits during their 5 year gambling operation" (as of the 1994 paper). — [UCLA eScholarship](https://escholarship.org/content/qt9tm6w0rp/qt9tm6w0rp_noSplash_490c4af635510cf20ca3a62a7156f5d4.pdf)
- Scale example: on Nov 6, 2001, Hong Kong's Triple Trio jackpot was at least HK$100 million, and Benter and associate Paul Coladonato won a $16 million jackpot. — [Bloomberg](https://www.bloomberg.com/news/features/2018-05-03/the-gambler-who-cracked-the-horse-racing-code)
- A widely repeated but unsourced claim (Medium) is that the model had "over 120 factors per horse." The search tool flagged it as low quality. — [Medium](https://medium.com/@stockreporter/billionaire-bill-benter-the-professional-gambler-who-created-a-horse-racing-algorithm-to-predict-54ee78a81979)

### Inferences
- The early failure pattern carries a clear lesson: a raw fundamental model that ignores market information produces confident, bizarre outputs. A human expert patched this by hand at first, and the second-stage blend with public odds later did it systematically. A WNBA prop model that outputs an implausible edge (for example a 65% "over" against a sharp line) is far more likely to be model error than market error.
- Even a strong quantitative team lost about 80% of its bankroll in year one. Small-stakes bettors should expect a long, possibly losing, calibration period and should size so they survive it.

### Gaps
- I could not access the full Bloomberg text. Its details on data entry (staff hand-coding race footage and past performances), staff headcount, computing, and the exact season-by-season P&L are unverified here.
- I found no primary source for the number of variables in Benter's production model.

## Q3. What structural features of Hong Kong pari-mutuel racing made it beatable, and do sports props share them?

### Takeaway
Hong Kong combined (a) very large, liquid pari-mutuel pools, so big bets moved odds relatively little, (b) a pool operator that takes a fixed cut and so has no reason to ban winners, (c) rebates on large losing bets that reduce the effective takeout for high-volume players (formalised after the 2006 reform), and (d) a public whose odds were informative but beatable when combined with a model. The takeout was high: 17.5% on win, place, and quinella, and 25% on exotics. US/online player props share almost none of these features. They are fixed-odds markets run by books or pick'em operators that can limit or ban winners, have low limits, and pay no volume rebates. They share only the "semi-informed, beatable public pricing" feature, and only in thin markets.

### Cited Findings
- HKJC takeout: 17.5% on standard bets (win, place, quinella), 25% on exotic bets, and an overall effective rate of 18.7% in 2005/06 (HKJC presentation, 2007). — [IFHA/ICHA 2007, Chang](https://www.ifhaonline.org/resources/WorldMedia/ICHA_2007/Chang_2007E.pdf)
- After the betting-duty reform, the HKJC could set its own takeout rates and introduce a rebate scheme. Revenue from rebate-eligible pools (Win, Place, Quinella, Quinella Place) grew more than 9%, against 7% overall, and high-value bets (HK$10,000+) increased. — [IFHA/ICHA 2007, Chang](https://www.ifhaonline.org/resources/WorldMedia/ICHA_2007/Chang_2007E.pdf)
- Current HKJC rule: "Any ticket or betline with total losing bet amount of HK$10,000 or above placed on designated pool will be eligible to receive a rebate of prescribed percentage of the total losing bet amount." — [HKJC Rebate guide](https://special.hkjc.com/e-win/en-US/betting-info/racing/beginners-guide/rebate/); [HKJC local rebate example](https://special.hkjc.com/e-win/en-US/betting-info/racing/beginners-guide/rebate-local/)
- June 2020: HKJC announced "higher rebates for Quinella & Quinella Place." — [HKJC Racing News, 2020-06-11](https://racingnews.hkjc.com/english/2020/06/11/forecast-relaunch-to-merge-with-trio-higher-rebates-for-quinella-quinella-place/)
- The Triple Trio pays out 75% of the pool (a 25% take), and the jackpot carries over when there are no winners. — [HKJC Triple Trio](https://www.hkjc.com/english/betting/ticket_3t.asp)
- Pool scale: HKJC turnover was HK$216.5 billion in the 2016–17 season. — [Hong Kong Jockey Club (Wikipedia)](https://en.wikipedia.org/wiki/Hong_Kong_Jockey_Club)
- So many syndicates eventually bet Hong Kong that the market became "efficient." The HKJC "was happy with the syndicates betting on their races because no matter what horse won, they took a cut of the amount bet." — [CDC Gaming Reports commentary](https://cdcgaming.com/commentary/syndicates-algorithms-and-beating-the-horses-in-hong-kong/)
- Props, by contrast: "Prop bets generally have low limits," often a fraction of side/total limits, and "the low limits often keep these markets from becoming sharp." Even the sharpest books (Pinnacle, Bookmaker) "typically hang low limits on NFL player props." Books that see consistent prop winners "reduce your betting limits, ban you from placing prop bets entirely," and pros spread action across multiple accounts. — [WizardOfOdds](https://wizardofodds.com/article/player-props-understanding-the-math-behind-the-lines/); [GamblingSite](https://www.gamblingsite.com/blog/why-sportsbooks-dont-like-props-bets/); [OddsShopper](https://www.oddsshopper.com/articles/betting-101/sports-betting-prop-strategy-finding-player-prop-inefficiencies-y10)
- Practitioner view (commercial sources, not peer reviewed): player-prop markets, "particularly exotic props on secondary players," are less efficient than game lines because books have less data, sharps pay less attention, and pricing models are less refined. Bookmaker hold is also higher where markets are softer. — [WizardOfOdds](https://wizardofodds.com/article/player-props-understanding-the-math-behind-the-lines/); [Establish The Run, Ed Miller](https://establishtherun.com/miller-why-prop-betting-is-profitable/)

### Inferences
- The rebate changes Benter-style economics a great deal. With a 17.5% take and a rebate on losing turnover, a high-volume bettor's effective takeout falls well below the headline figure. A $5 pick'em player gets nothing comparable and faces an effective hold of 25–37.5% at coin-flip probabilities (see Q6). This is the biggest structural feature that does not transfer.
- Pari-mutuel pools have no "limits management" problem: the house does not care who wins. Pick'em operators and sportsbooks do care, and they can restrict winning players. At $5 stakes this rarely binds in practice, but it means the venue's incentives run against the bettor.
- What does transfer is the "informative but imperfect public" premise. WNBA props, especially for secondary players and for rebounds/assists, plausibly resemble the soft, thin pools where Benter-style blending pays most. The same thinness makes the market a noisier prior and closing lines a noisier benchmark.

### Gaps
- I found no source for the rebate percentage that applied in Benter's era (the 1980s–90s). The scheme appears to be a post-2006 reform feature, so Benter's early profits were likely made without rebates, but this is unverified.
- I found no source quantifying the syndicates' share of HK pool turnover.
- I found no peer-reviewed study that measures WNBA (or NBA) player-prop market efficiency. The evidence is practitioner commentary.

## Q4. How do modern syndicates find edge (model vs market, information timing, injury news, limits management)?

### Takeaway
Modern operations follow one recurring pattern:
- Build a model that produces a fair price, bet when the gap to the market ("delta") is big enough, and size by the gap.
- Go where liquidity and limits are high (Asian handicap books for Starlizard, which reaches them through contacts and other people's accounts).
- Manage timing and line movement aggressively (Walters' staged bets and "head fakes").
- Expect edges to decay as books adapt (Voulgaris's pre-2004 edge vanished, and he had to rebuild with a possession-level simulation model).

Account access and limits are a constant operational problem: in the 2025–26 Bloom case, the syndicate used a third party's betting accounts.

### Cited Findings
- **Starlizard (Tony Bloom):** founded 2006. A "data collection company which uses the information to generate statistical models that provide gamblers with an edge in football betting markets, primarily Asian handicaps." It is a consultancy that sells odds to clients and does not take bets, and Bloom is its main client. — [TheJournal.ie (Feb 2016)](https://www.thejournal.ie/tony-bloom-starlizard-2597458-Feb2016/); [Racing Post](https://www.racingpost.com/news/britain/high-court-case-alleges-tony-blooms-betting-empire-makes-600m-a-year-so-what-do-we-know-about-his-starlizard-syndicate-aNlkE7t8daxQ/)
- Starlizard's edge logic, as explained by a secondary source: if the market offers 2.0 (50%) and the model says 55%, that is a 5% edge. The model focuses on likely scorelines because Asian handicaps depend on goal margin. — [The Dark Room](https://thedarkroom.co.uk/the-secrets-behind-tony-blooms-starlizard-betting-consultancy-success/)
- Why Asia: bets of that size "without skewing the odds would be near impossible in Europe, but in Asia – one of the most liquid gambling markets in the world – it can go undetected." Access requires contacts. Margins are "razor thin – it's a volume game." — [TheJournal.ie](https://www.thejournal.ie/tony-bloom-starlizard-2597458-Feb2016/)
- 2025–26 High Court case: former employee Ryan Dudfield claims about $17.5m (£13.1m) and alleges the syndicate makes about £600m a year. Bloom's lawyers call that figure an "irrelevant exaggeration," and the response was made public on Jan 23 (2026). The filing says George Cottrell lent his betting accounts to the syndicate, with the relationship continuing until October 2025 across five accounts in Cottrell's name. — [Casino.org](https://www.casino.org/news/inside-starlizard-high-court-filing-lifts-lid-on-tony-blooms-800m-betting-empire/); [Gambling Insider](https://www.gamblinginsider.com/news/105962/tony-bloom-denies-17-5m-betting-syndicate-claim); [SiGMA](https://sigma.world/news/political-aide-linked-to-premier-league-gambling-operation-dispute/)
- **Billy Walters / Computer Group (1980s onward):** the core concept is a "delta: the difference between the Vegas line and what the bettors conclude the point spread should be. The greater the delta, the more money a gambler like Walters will bet." Bets were staged. Walters would bet $50,000 on a team at −3, then $75,000 more at −3.5. He used "head fakes," mostly to move lines a half-point off key numbers. His stated principle: "you've got to get them to move the line, and secondly, you've got to bet it before someone else takes the numbers." — [ESPN feature (2015)](http://www.espn.com/espn/feature/story/_/id/12280555/how-billy-walters-became-sports-most-successful-controversial-bettor); [Shortform](https://www.shortform.com/blog/the-computer-group-sports-betting/); [CDC Gaming Reports](https://cdcgaming.com/commentary/billy-walterss-bestseller-conjures-the-ghost-of-the-computer-group-and-interference/)
- Walters' memoir says little about how the Computer Group's modeling software worked, though it calls the software the foundation of its success. — [Shortform](https://www.shortform.com/blog/the-computer-group-sports-betting/)
- **Haralabos "Bob" Voulgaris (NBA):** his early edge (reported as exploiting coach tendencies and NBA totals) collapsed around 2004 when books "caught on to his strategies and made adjustments." By about 2005 he concluded "the only way to gain a decent edge was to build a computer model." With a hired quant ("The Whiz") he built "Ewing," which simulated games at the possession / play-by-play level to produce predicted scorelines. — [ESPN Playbook blog](https://www.espn.com/blog/playbook/dollars/post/_/id/2935/meet-the-worlds-top-nba-gambler); [Champion Bets](https://www.championbets.com.au/betting-academy-article/bob-voulgaris); [Nate Silver, *Signal and the Noise* ch. excerpt](http://faculty.bard.edu/hhaggard/teaching/sci127Sp20/notes/SilverSignalExcerpt.pdf)
- Edge decay mechanism: "as rival bettors independently deduce or flat out copy the edges of a profitable bettor the betting line moves back towards plumb and the edge is no longer there." Low-quality source. — [Medium](https://medium.com/@ericcloverwadel/when-profitable-sports-bettor-haralabos-bob-voulgaris-lost-his-edge-he-nearly-lost-all-of-the-87283f095133)
- Voulgaris later moved from pro bettor to a Dallas Mavericks front-office role. The search returned only the article title, so the date was not verified here. — [Trademate Sports on Medium](https://tradematesports.medium.com/nbas-greatest-ever-bettor-haralabos-voulgaris-from-pro-bettor-to-maverick-s-director-10-people-7f142bbf95dd)
- **Market structure (Miller & Davidow, *The Logic of Sports Betting*, 2019):** "market maker" books take all bettors at high limits and discover price, while "retail" books copy market-maker lines. If a retail book strays, a bettor can buy the bet at the retail book and sell it back to the market maker at a guaranteed profit. Per a summary, the book argues that adding more props and derivatives "paradoxically weakens the entire offering" for books. — [Scribd copy](https://www.scribd.com/document/558620857/The-Logic-of-Sports-Betting); [SoBrief summary](https://sobrief.com/books/the-logic-of-sports-betting); [Bettably review](https://bettably.com/blog/the-logic-of-sports-betting-review)
- Props and limits, from practitioner sources: $500 prop bets reportedly "fly under the radar at many of the bigger U.S. books," but books limit or ban consistent prop winners, and pros use multiple accounts. — [OddsShopper](https://www.oddsshopper.com/articles/betting-101/sports-betting-prop-strategy-finding-player-prop-inefficiencies-y10); [GamblingSite](https://www.gamblingsite.com/blog/why-sportsbooks-dont-like-props-bets/)

### Inferences
- Across Benter, Walters, Starlizard, and Voulgaris, "edge" is always defined relative to the market price, never as standalone prediction accuracy. Sizing scales with the gap, and execution (where, when, and through which accounts) is as important as the model.
- Information timing matters most in NBA/WNBA props. Injury and rest news shifts minutes and usage for teammates, and lines that have not yet moved, especially on pick'em apps that update slower than market-making sportsbooks, are the prop equivalent of Walters' "bet it before someone else takes the numbers." This is inferred from the general pattern. I found no source measuring pick'em line staleness for the WNBA.
- Edges decay. Voulgaris's experience implies that any WNBA prop edge based on a simple, observable pattern (for example back-to-backs or a naive usage bump when a star sits) should be expected to shrink as books and pick'em operators adapt. Models need ongoing out-of-sample monitoring.

### Gaps
- I found no results at all on "Priomha." I could not verify what it is or how it operates, and the brief's reference to it remains unconfirmed.
- I found no first-hand Voulgaris interview text on player projections or on how Ewing combined model output with market lines.
- I found no source on how syndicates specifically handle injury-news timing in props.

## Q5. What is the consensus best metric of skill (closing line value), and why?

### Takeaway
The practitioner consensus, articulated most influentially by Joseph Buchdahl in articles for Pinnacle, is that beating the de-vigged closing price of a sharp, high-limit market is the best short-run measure of skill. The closing price embeds all information and money up to the start, so it is the best available estimate of true probability, and Buchdahl's data show a near one-to-one relationship between the size of the beat and long-run yield. CLV converges far faster than ROI. The caveats: it holds on average rather than for every bet, it needs the margin removed, and it is only as good as the closing market is efficient. Thin prop markets are exactly where closing lines are least efficient.

### Cited Findings
- Buchdahl's July 2016 Pinnacle study measured how well opening/closing price ratios predict yield. A "coefficient of proportionality" of 1 means perfect proportionality, and he found close to that for soccer. A secondary source puts the sample at about 87,960 odds pairs over four seasons of major European leagues. That figure is unverified. — [Pinnacle: "How to solve a problem like efficiency" Part 1](https://www.pinnacle.com/betting-resources/en/educational/how-to-solve-a-problem-like-efficiency-part-one/rn8j5rnqj2p8t68p); [Sports Trading Network, Part 2](https://www.sportstradingnetwork.com/article/how-to-solve-a-problem-like-efficiency-part-two/); [Pyckio blog](https://blog.pyckio.com/en/eg-pinnacle-closing-odds/)
- The rule of thumb: "beat the closing line by 10% and you should expect to make a profit over turnover of 10% over the long run." — [Pinnacle: "Using the closing line to test your skill in betting"](https://www.pinnacle.com/en/betting-articles/betting-strategy/using-closing-line-to-test-betting-skill/7e6jwjm5ykejuwkq)
- The rationale: the close is "the most accurate line, since all available information, opinions, and money bet have been factored in." Pinnacle is preferred as the benchmark partly because it accepts winning bettors at high limits. — [TheStatsAPI CLV explainer](https://thestatsapi.com/odds-api/clv); [SportsAPIs.dev](https://sportsapis.dev/pinnacle-api)
- Statistical efficiency: a bettor with a consistent 5% CLV edge "might only need 50 bets to demonstrate significance," whereas results alone can take several thousand bets. A forum framing: "ROI will only be accurate after thousands of plays." — [Pinnacle Odds Dropper on Buchdahl](https://www.pinnacleoddsdropper.com/blog/closing-line-value--clv-demystified-by-expert-joseph-buchdahl); [SportsbookReview forum](https://www.sportsbookreview.com/forum/handicapper-think-tank/1362020-useful-metrics-to-determine-skill)
- The margin caveat: expected return is roughly CLV minus the margin built into the closing price, so +2% CLV against a 2% margin is not winning. Compare against no-vig ("NVP") closing prices. — [Pinnacle Odds Dropper](https://www.pinnacleoddsdropper.com/blog/what-is-closing-line-value)
- Limits of the hypothesis: closing prices are efficient on average, not for every individual price, and some profitable bettors fail to beat the close (a tennis analysis). Buchdahl notes "until bookmakers show us the data on profit/losses versus closing line value we'll never fully settle the question." — [Sports Trading Network (tennis)](https://www.sportstradingnetwork.com/article/do-pinnacle-closing-prices-in-tennis-tell-the-full-story-can-you-win-in-the-long-run-without-beating-them/); [Pinnacle](https://www.pinnacle.com/en/betting-articles/betting-strategy/using-closing-line-to-test-betting-skill/7e6jwjm5ykejuwkq)
- Data-access note (2025): one vendor says Pinnacle's official API closed to the general public on July 23, 2025, with third-party providers still offering Pinnacle data. — [SportsAPIs.dev](https://sportsapis.dev/pinnacle-api)
- CLV is only meaningful where the closing market is sharp. A commercial article argues it is "the gold standard" but only on a few platforms. — [The Spread](https://www.thespread.com/?p=550721)

### Inferences
- For WNBA props, the closing price is a weaker truth benchmark than for NBA sides and totals, because of low limits, thin sharp attention, and late injury news. Prop CLV is still the fastest available skill signal, but it will be noisier and should be measured against a de-vigged consensus of several books (or the sharpest available prop book), not a single retail book.
- Pick'em apps post a fixed number (for example "Over 7.5 rebounds") at a fixed payout table rather than a price. The workable proxy is "line CLV": did the sportsbook consensus line or price move toward your side between entry and tip-off? For example, if you took Over 7.5 and sharp books closed at 8.5, or at 7.5 with the over price moving from −110 to −135, you beat the close. Converting closing sportsbook odds into a fair probability for your exact pick'em line gives a per-leg expected win rate you can compare with the break-even rates in Q6.
- Benter's paper and the CLV literature say the same thing in different words. The market's closing estimate is the best single predictor, and skill is measured by information not yet in it.

### Gaps
- I found no study measuring how efficient WNBA (or NBA) player-prop closing lines are, or how well prop CLV predicts prop ROI.
- I could not access Buchdahl's original articles. The 87,960-pair sample and the slope values are secondhand.

## Q6. Which parts of Benter's approach transfer to small-stakes WNBA player-prop pick'em betting, and which do not?

### Takeaway
What transfers:
- The method: market as prior, a held-out second-stage blend, calibration, disciplined (fractional) Kelly sizing, and CLV-style tracking.
- The attitude: years of data work, and the expectation of early losses.

What does not transfer:
- Benter's economics (huge liquid pools, rebates, an operator that does not care who wins, and scale that amortises fixed costs).

Pick'em payout tables impose effective holds of 25–37.5% at coin-flip probabilities, so per-leg break-evens run about 55–58.5%, against 52.4% at −110. Small per-leg calibration errors compound across legs, which makes Benter-style shrinkage toward the market more important, not less.

### Cited Findings
- 2026 Power Play break-even per leg (formula (1/payout)^(1/picks)), from affiliate and tool sites; check the current paytable in-app:
  - 2-pick at 3x: 57.7%
  - 3-pick at 5x (PrizePicks): 58.5%
  - 3-pick at 6x (Underdog): ≈55.0–55.1%
  - 4-pick at 10x: 56.2%
  - 5-pick at 20x: 54.9%
  - 6-pick: conflicting figures. One source pairs "40x" with a 58.5% break-even, which is internally inconsistent: 40x implies ≈54.1%, and 58.5% implies about 25x. Another gives 37.5x, which implies ≈54.6–54.7%. Check the in-app paytable.
  - Sources: [OddsReference pick'em comparison](https://oddsreference.com/dfs/pickem/pickem-platform-comparison); [OddsReference calculator](https://oddsreference.com/tools/pickem-payout-calculator); [SickFade calculator](https://sickfade.com/calculators/pickem); [Upside.tools pricing](https://upside.tools/research/prizepicks-vs-underdog-pricing); [Betting-Forum thread](https://www.betting-forum.com/threads/prizepicks-betting-strategy-the-2-pick-trap-vs-5-pick-edge-break-even-math-explained.46905/)
- Flex plays: a PrizePicks 4-pick Flex reportedly pays 6x for 4/4 and 1.5x for 3/4. An Underdog 4-pick flex at 7.2x is converted to about −107 per leg, or roughly 51.7% break-even. The figures depend on the consolation structure and are hard to compare. — [OddsReference](https://oddsreference.com/compare/dfs); [PropsBot](https://propsbot.ai/prizepicks-vs-underdog/)
- Pick'em sources are July–August 2026 affiliate pages. Payouts change. — [SmartStake: How to beat PrizePicks](https://www.smartstake.app/learn/how-to-beat-prizepicks)
- Benter's two-stage blend, fractional Kelly, and the finding that the combination beats either input are covered in Q1. — [Gwern PDF](https://gwern.net/doc/statistics/decision/1994-benter.pdf); [arXiv 1701.02814](https://arxiv.org/pdf/1701.02814)

### Inferences
These are my own calculations and reasoning from the cited payout tables and sources.

**House edge and EV**
- At a true 50% per leg, pick'em payouts imply these house edges:
  - 2-pick 3x: 25%
  - 3-pick 6x (Underdog): 25%
  - 3-pick 5x: 37.5%
  - 4-pick 10x: 37.5%
  - 5-pick 20x: 37.5%

  That is comparable to or worse than HK's 17.5–25% take, with no rebate.
- EV at a given true per-leg hit probability (independent legs):

  | Slip | p = 0.55 | p = 0.57 | p = 0.60 |
  |---|---|---|---|
  | 2-pick 3x | −9.2% | −2.5% | +8.0% |
  | 3-pick 5x | −16.8% | −7.4% | +8.0% |
  | 3-pick 6x | −0.2% | +11.1% | +29.6% |
  | 4-pick 10x | −8.5% | +5.6% | +29.6% |
  | 5-pick 20x | +0.7% | +20.3% | +55.5% |

- Leverage cuts both ways. A two-point overestimate of per-leg probability (a model that thinks 57% when the truth is 55%) turns a "+20% EV" 5-pick into break-even. That is the same overconfidence Benter's second-stage logit corrects. Shrink model probabilities toward the de-vigged market before building slips.

**Kelly sizing**
- Full-Kelly fractions per slip (as a share of bankroll):

  | Slip | p = 0.57 | p = 0.60 |
  |---|---|---|
  | 5-pick 20x | ≈1.07% | ≈2.9% |
  | 4-pick 10x | ≈0.62% | ≈3.3% |
  | 2-pick 3x | 0 (negative EV) | 4.0% |

- So a flat $5 slip is "full Kelly" for a 5-pick at 57% per leg only with a bankroll of about $470. At quarter Kelly, the prudent choice given estimation error, it implies about $1,900. At a true 55% per leg the Kelly stake for a 5-pick is ≈0.03%, which effectively means no bet.

**What transfers**
- **Market-as-prior blending.** Use de-vigged sharp sportsbook prop odds (or a multi-book consensus) as π, use your projection as f, and fit α and β on held-out WNBA games. The fitted β/α ratio tells you how much your model actually adds beyond the market.
- **Out-of-sample discipline.** Keep separate fit and holdout periods, as Benter did.
- **Fractional Kelly**, or at least bankroll sizing consistent with Kelly.
- **Line-CLV logging** as the primary skill metric. ROI on $5 slips will take thousands of entries to separate from luck.
- **Information timing.** Re-run projections after injury and rest news and before pick'em apps update.

**What does not transfer**
- **Pool size and liquidity.** Benter's profits came from scaling a small percentage edge over very large pools. At $5 a slip, absolute profit is capped regardless of edge.
- **Rebates.** None exist on pick'em apps.
- **Operator neutrality.** Pick'em operators are the counterparty and adjust lines and payout tables.
- **Benter-scale data.** He used thousands of races with roughly 10–14 runners each, while a WNBA season yields far fewer independent player-games per player.
- **The full cost structure** that justified about 5 man-years of development.

**Correlation**
- Pick'em payouts price legs as if independent. Positively correlated legs on the same side (for example a player's points and PRA, or teammates in a projected high-pace game) raise the true joint probability. Model errors that are common to several legs (a wrong minutes projection, say) make outcomes riskier than the independent-leg math suggests. Operators reportedly restrict obviously correlated combinations, but that is unverified here.

### Gaps
- I found no current, primary (operator-published) paytables. All payout figures come from affiliate sites dated July–August 2026, and the 6-pick numbers conflict.
- I found no source on whether pick'em operators limit or ban consistently winning small-stakes players, or on how quickly their WNBA lines lag sharp sportsbooks after injury news.
- I found no academic or primary-source measurement of WNBA prop market efficiency, limits, or hold. Practitioner sources discuss NFL and MLB props more than WNBA.
