# UFC Fight Night: Allen vs Duncan (2026-10-10) - quick model report

**Data**: Greco1899/scrape_ufc_stats (ufcstats.com scrape, GitHub raw). **Data cutoff (latest event in files): 2026-10-03** (UFC 332: Silva vs. Wang). The repo's own README says a full refresh was done 2025-11-22 and a daily job refreshes new fights; the files I pulled already contain all events through 2026-10-03, so there is no lag for tonight's ten fighters (each fighter's last fight in the data is listed in `data_flags`). All ten fighters were found in the data (Kai Kamaka III matched as 'Kai Kamaka'; Loopy Godinez found directly; Lupita alias also mapped). Any fight after 2026-10-03 and before tonight (none expected) would be missing.

## 1. Win probability

Setup: Elo over all UFC fights (K and a new-fighter boost tuned on pre-2023 fights only: K=60, boost x1.5). Antisymmetric logistic regression (no intercept, trained on both fighter orders so there is no corner bias) on Elo diff + age, reach, height, log UFC experience, days since last fight, shrunk career rates (sig strikes landed/min, absorbed/min, takedowns landed/15, takedown defense, sub attempts/15), last-3 win rate and last-3 sig-strike differential. Every feature is point-in-time (only fights on strictly earlier dates; cards are predicted before any card result is applied). Trained on 2011-01-01 to 2022-12-31 (5313 fights), L2 strength chosen on a 2021-22 time-split (C=0.01). **Holdout: 2023-01-01 to 2026-10-03, n=1979 decisive fights** (draws/NC excluded).

| model | log loss | Brier | accuracy | n |
|---|---|---|---|---|
| Full model (LR) | 0.641 | 0.225 | 0.634 | 1979 |
| Elo only (raw expectation) | 0.678 | 0.243 | 0.563 | 1979 |
| Elo only (calibrated LR on Elo diff) | 0.678 | 0.242 | 0.563 | 1979 |
| 50% baseline | 0.693 | 0.250 | 0.500 | 1979 |


Log-loss gain of the full model vs raw Elo: 0.0374 (bootstrap 95% CI 0.0290 to 0.0465); vs 50%: 0.0524 (CI 0.0422 to 0.0628). **The model beats both Elo and the 50% baseline on the holdout; Elo alone beats 50% only modestly (log loss 0.6780 vs 0.6931).** No betting-market odds were available, so I cannot say whether it beats the market; a typical closing-line log loss is lower than this.

Holdout by year (stability check):

| year | n | model_ll | elo_ll | base_ll | model_acc | elo_acc |
|---|---|---|---|---|---|---|
| 2023 | 513 | 0.649 | 0.682 | 0.693 | 0.616 | 0.556 |
| 2024 | 513 | 0.642 | 0.676 | 0.693 | 0.618 | 0.556 |
| 2025 | 526 | 0.633 | 0.672 | 0.693 | 0.652 | 0.578 |
| 2026 | 427 | 0.639 | 0.682 | 0.693 | 0.651 | 0.564 |


Calibration, full model, 5 equal-count bins on P(fighter A wins) (A/B order is arbitrary in the source files, so this is mostly a lopsidedness test):

| n | mean_pred | observed |
|---|---|---|
| 396 | 0.345 | 0.328 |
| 396 | 0.455 | 0.490 |
| 395 | 0.525 | 0.549 |
| 396 | 0.594 | 0.664 |
| 396 | 0.699 | 0.758 |


Calibration, favourite-oriented (P(favourite wins), 5 bins):

| n | mean_pred | observed |
|---|---|---|
| 396 | 0.516 | 0.523 |
| 396 | 0.552 | 0.551 |
| 395 | 0.590 | 0.623 |
| 396 | 0.637 | 0.684 |
| 396 | 0.722 | 0.778 |


Calibration, raw Elo, 5 bins:

| n | mean_pred | observed |
|---|---|---|
| 396 | 0.409 | 0.467 |
| 396 | 0.491 | 0.528 |
| 395 | 0.537 | 0.537 |
| 396 | 0.585 | 0.593 |
| 396 | 0.666 | 0.664 |


The model is slightly under-confident at the extremes (e.g. top bin predicted 0.70, observed 0.76). Logistic coefficients per 1 SD of each feature (positive favours fighter A): elo +0.21, age -0.30, reach +0.07, height -0.02, exp +0.07, days -0.07, sl_pm +0.11, sa_pm -0.14, td15 +0.10, tdd +0.07, sub15 -0.00, l3_win -0.04, l3_diff +0.11.

Tonight's win probabilities come from the same model refit on all data through the cutoff (same hyperparameters).

## 2. Method / duration

Each fighter's KO-for, KO-against, sub-for, sub-against rates (per fight, 3-round-equivalent: a finish after round 3 in a 5-round fight counts as 'went 3 rounds') are shrunk toward the point-in-time weight-class x gender base rate (prior strength n0=50 fights, fighter-signal multiplier alpha=4.0; tuned on 2021-22). Fight P(KO), P(sub) = sum over both fighters; P(distance) = remainder. 5-round bouts: P(survive rounds 4-5 | survived 3) = 0.802 from 5-round fights 2018 onward (n reaching round 4 = 243), and fight time is sampled from empirical finish-time quantiles. Per-fighter p_ko_for/p_sub_for come from a 2x3 (winner x method) table reconciled by iterative proportional fitting to the model win probability and the fight-level method totals.

Holdout (n=1968 fights, 3-round-equivalent outcome DEC/KO/SUB):

| model | multiclass log loss | P(distance) log loss | P(distance) Brier | KO Brier | Sub Brier |
|---|---|---|---|---|---|
| fighter+division | 0.970 | 0.667 | 0.237 | 0.204 | 0.142 |
| division base only | 1.002 | 0.685 | 0.246 | 0.211 | 0.146 |
| global base only | 1.016 | 0.694 | 0.250 | 0.218 | 0.145 |


Constant P(distance) log loss: 0.6931. Fighter-level info helps (0.667 vs 0.685 division-only vs 0.694 global) but the gain is modest.

Calibration of P(distance), 3-round-equivalent, 5 bins:

| n | mean_pred | observed |
|---|---|---|
| 394 | 0.343 | 0.360 |
| 393 | 0.442 | 0.412 |
| 394 | 0.507 | 0.525 |
| 393 | 0.562 | 0.552 |
| 394 | 0.657 | 0.673 |


Actual-format P(distance) (3- and 5-round): mean predicted 0.491 vs observed 0.496; 3-round fights 0.503 vs 0.499; **5-round fights (n=195) 0.385 predicted vs 0.472 observed** - the 5-round extension used pre-2023 survival (0.77) and the 2023+ survival rate was 0.84, so P(distance) for the 5-round main event is probably biased low. Time check: mean_pred_E_time=10.885, actual_mean_time=11.046, pred_P_le5=0.265, obs_P_le5=0.258, pred_P_le10=0.415, obs_P_le10=0.417, mean_pred_median_time=13.453.

Base-rate validation by weight class and gender on the holdout (obs = observed 3-round-equivalent rate, pred = fighter+division model, base = division base rate only; F_ = women):

| divg | n | obs_dec | pred_dec | base_dec | obs_ko | pred_ko | base_ko | obs_sub | pred_sub | base_sub |
|---|---|---|---|---|---|---|---|---|---|---|
| F_Bantamweight | 75 | 0.640 | 0.629 | 0.598 | 0.133 | 0.209 | 0.238 | 0.227 | 0.162 | 0.163 |
| F_Featherweight | 5 | 1.000 | 0.594 | 0.505 | 0.000 | 0.267 | 0.303 | 0.000 | 0.139 | 0.192 |
| F_Flyweight | 105 | 0.714 | 0.637 | 0.610 | 0.124 | 0.179 | 0.188 | 0.162 | 0.184 | 0.202 |
| F_Strawweight | 131 | 0.634 | 0.643 | 0.650 | 0.168 | 0.157 | 0.154 | 0.198 | 0.200 | 0.196 |
| M_Bantamweight | 218 | 0.615 | 0.544 | 0.530 | 0.220 | 0.272 | 0.269 | 0.165 | 0.184 | 0.201 |
| M_Featherweight | 237 | 0.460 | 0.544 | 0.553 | 0.363 | 0.294 | 0.280 | 0.177 | 0.162 | 0.167 |
| M_Flyweight | 151 | 0.517 | 0.535 | 0.552 | 0.252 | 0.250 | 0.246 | 0.232 | 0.214 | 0.202 |
| M_Heavyweight | 138 | 0.457 | 0.367 | 0.343 | 0.420 | 0.494 | 0.516 | 0.123 | 0.139 | 0.141 |
| M_Light Heavyweight | 138 | 0.355 | 0.384 | 0.399 | 0.486 | 0.446 | 0.434 | 0.159 | 0.170 | 0.167 |
| M_Lightweight | 272 | 0.445 | 0.480 | 0.494 | 0.390 | 0.311 | 0.289 | 0.165 | 0.208 | 0.217 |
| M_Middleweight | 242 | 0.430 | 0.417 | 0.413 | 0.393 | 0.374 | 0.377 | 0.178 | 0.209 | 0.211 |
| M_Other | 30 | 0.633 | 0.485 | 0.471 | 0.167 | 0.287 | 0.284 | 0.200 | 0.228 | 0.245 |
| M_Welterweight | 226 | 0.465 | 0.484 | 0.488 | 0.358 | 0.330 | 0.326 | 0.177 | 0.187 | 0.186 |


Small divisions (F_Featherweight n=5, M_Other n=30) are noisy. Overall base rates track well; the model over-predicts KO in M_Heavyweight/F_Bantamweight and under-predicts it in M_Featherweight/M_Lightweight, i.e. division base rates drift year to year.

## 3. Stat projections (sig strikes, takedowns, fight time)

Method: sig strikes ~ negative binomial with mean = division mean x exp(b0 + b1 log(own landed/min ratio) + b2 log(opponent absorbed/min ratio)) x minutes^gamma, rolling rates shrunk to division means (career weights, prior 30 min; decay and prior tuned on 2021-22). Fitted dispersion alpha=0.315 (variance = mu + alpha mu^2; pre-2023 fit), gamma=0.80 (strikes per minute fall in longer fights). Takedowns ~ NB with own TD/min, opponent TDs absorbed/min and opponent TD defense; alpha=0.78, gamma=0.90. The count distribution is mixed exactly over the fight-time distribution from section 2 (equivalent to simulating the duration). Tonight's projections are refit on all data through the cutoff and multiplied by a trailing-24-month league-drift scale (sig strikes x0.93, takedowns x1.05) because the pre-2023 model over-predicted 2024-26 strikes by 7-11%. That scale is not out-of-sample validated.

**Sig strikes - holdout (4026 fighter-fights, full chain incl. predicted duration, pre-2023 fit, no drift scale):** conditional NLL given actual minutes 4.373 vs division-mean-only 4.439 (model uses opponent/fighter info usefully). P(count > projected median) predicted 0.494 vs observed 0.491; P(count >= median) predicted 0.506 vs observed 0.502 - so P(over the projected-median line) is about 50% as intended. Mean absolute error of the median: 25.36 (division-mean-only 26.69). Interval coverage: p25-p75 0.508 (nominal 0.50), p10-p90 0.807 (nominal 0.80; 0.126 fell below p10 and 0.067 above p90).

Calibration of P(over line) at lines placed at offsets from each fighter's own projected median:

| offset | mean_line | mean_pred_over | obs_over | logloss | brier |
|---|---|---|---|---|---|
| -30 | 9.260 | 0.905 | 0.897 | 0.317 | 0.090 |
| -20 | 18.294 | 0.776 | 0.760 | 0.548 | 0.182 |
| -10 | 28.266 | 0.626 | 0.616 | 0.669 | 0.238 |
| -5 | 33.266 | 0.558 | 0.550 | 0.690 | 0.248 |
| 0 | 38.266 | 0.494 | 0.491 | 0.693 | 0.250 |
| 5 | 43.266 | 0.435 | 0.430 | 0.681 | 0.244 |
| 10 | 48.266 | 0.382 | 0.374 | 0.655 | 0.231 |
| 20 | 58.266 | 0.291 | 0.283 | 0.586 | 0.199 |
| 30 | 68.266 | 0.219 | 0.203 | 0.492 | 0.157 |


Calibration at fixed lines:

| line | mean_pred_over | obs_over |
|---|---|---|
| 15.500 | 0.777 | 0.752 |
| 25.500 | 0.632 | 0.623 |
| 35.500 | 0.506 | 0.502 |
| 45.500 | 0.399 | 0.391 |
| 55.500 | 0.311 | 0.311 |
| 70.500 | 0.210 | 0.199 |
| 90.500 | 0.122 | 0.107 |
| 110.500 | 0.070 | 0.055 |


Pooled reliability (all offset lines, 8 bins):

| n | mean_pred | observed |
|---|---|---|
| 4482 | 0.214 | 0.184 |
| 4482 | 0.316 | 0.307 |
| 4482 | 0.402 | 0.396 |
| 4482 | 0.465 | 0.470 |
| 4482 | 0.525 | 0.541 |
| 4482 | 0.598 | 0.591 |
| 4482 | 0.727 | 0.712 |
| 4482 | 0.917 | 0.891 |


The model slightly over-predicts high counts (e.g. P(over 110.5) 0.070 predicted vs 0.055 observed) and the pre-2023 fit over-predicts the conditional mean (46.6 vs 43.6) because strike volume dropped in 2025-26; hence the recency scale for tonight.

**Takedowns - holdout:** mean predicted 0.947 vs observed 1.036 per fighter. P(TD>=1): predicted 0.442 vs observed 0.425; log loss 0.6264 vs division-mean-only 0.6769 vs constant 0.6819. P(TD>=2): predicted 0.224 vs observed 0.247; log loss 0.5133 vs 0.5555 vs 0.5587.

P(TD>=1) calibration (5 bins):

| n | mean_pred | observed |
|---|---|---|
| 797 | 0.256 | 0.208 |
| 797 | 0.367 | 0.309 |
| 796 | 0.447 | 0.426 |
| 797 | 0.519 | 0.516 |
| 797 | 0.620 | 0.668 |


P(TD>=2) calibration (5 bins):

| n | mean_pred | observed |
|---|---|---|
| 797 | 0.074 | 0.102 |
| 797 | 0.146 | 0.149 |
| 796 | 0.213 | 0.235 |
| 798 | 0.284 | 0.284 |
| 796 | 0.402 | 0.464 |


Takedown probabilities are under-dispersed: low-probability fighters are over-predicted (0.26 predicted vs 0.21 observed) and high-probability fighters under-predicted (0.62 vs 0.67); P(TD>=2) is slightly low overall. Treat TD edges as directional, not precise.

## 4. Tonight's projections (per fighter)


**Brendan Allen vs Christian Leroy Duncan** (M Middleweight, 5 rounds) - fight P(KO/TKO) 0.297, P(sub) 0.227, P(distance) 0.382


| fighter | win_prob | elo_only_win_prob | p_distance | p_ko_for | p_sub_for | fight_time_median_min | sig_strikes_median | sig_strikes_p25 | sig_strikes_p75 | td_mean | p_td_ge1 | p_td_ge2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Brendan Allen | 0.509 | 0.629 | 0.382 | 0.051 | 0.215 | 13.550 | 30 | 13 | 58 | 1.963 | 0.600 | 0.394 |
| Christian Leroy Duncan | 0.490 | 0.371 | 0.382 | 0.246 | 0.012 | 13.550 | 44 | 19 | 84 | 0.749 | 0.393 | 0.180 |


Brendan Allen: data_cutoff=2026-10-03; ufc_fights_in_data=19; last_fight=2026-06-06 (126d ago); 5_round_main_event(rounds4-5 survival from 2018+ history); Christian Leroy Duncan: data_cutoff=2026-10-03; ufc_fights_in_data=10; last_fight=2026-07-18 (84d ago); 5_round_main_event(rounds4-5 survival from 2018+ history)


**Matheus Camilo vs Jai Herbert** (M Lightweight, 3 rounds) - fight P(KO/TKO) 0.337, P(sub) 0.189, P(distance) 0.474


| fighter | win_prob | elo_only_win_prob | p_distance | p_ko_for | p_sub_for | fight_time_median_min | sig_strikes_median | sig_strikes_p25 | sig_strikes_p75 | td_mean | p_td_ge1 | p_td_ge2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Matheus Camilo | 0.718 | 0.556 | 0.474 | 0.224 | 0.114 | 13.550 | 24 | 12 | 43 | 1.617 | 0.586 | 0.363 |
| Jai Herbert | 0.282 | 0.444 | 0.474 | 0.113 | 0.075 | 13.550 | 26 | 13 | 46 | 0.409 | 0.281 | 0.087 |


Matheus Camilo: data_cutoff=2026-10-03; ufc_fights_in_data=3; last_fight=2026-06-27 (105d ago); LOW_SAMPLE(<5 UFC fights; rates heavily shrunk to division means); Jai Herbert: data_cutoff=2026-10-03; ufc_fights_in_data=10; last_fight=2026-04-18 (175d ago)


**Loopy Godinez vs Ketlen Souza** (F Strawweight, 3 rounds) - fight P(KO/TKO) 0.077, P(sub) 0.244, P(distance) 0.678


| fighter | win_prob | elo_only_win_prob | p_distance | p_ko_for | p_sub_for | fight_time_median_min | sig_strikes_median | sig_strikes_p25 | sig_strikes_p75 | td_mean | p_td_ge1 | p_td_ge2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Loopy Godinez | 0.638 | 0.574 | 0.678 | 0.023 | 0.160 | 15.000 | 43 | 23 | 69 | 2.457 | 0.696 | 0.494 |
| Ketlen Souza | 0.362 | 0.426 | 0.678 | 0.054 | 0.084 | 15.000 | 40 | 21 | 65 | 0.634 | 0.382 | 0.151 |


Loopy Godinez: data_cutoff=2026-10-03; ufc_fights_in_data=16; last_fight=2026-04-11 (182d ago); Ketlen Souza: data_cutoff=2026-10-03; ufc_fights_in_data=7; last_fight=2026-06-06 (126d ago)


**Andre Fili vs Kai Kamaka III** (M Featherweight, 3 rounds) - fight P(KO/TKO) 0.312, P(sub) 0.096, P(distance) 0.592


| fighter | win_prob | elo_only_win_prob | p_distance | p_ko_for | p_sub_for | fight_time_median_min | sig_strikes_median | sig_strikes_p25 | sig_strikes_p75 | td_mean | p_td_ge1 | p_td_ge2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Andre Fili | 0.557 | 0.605 | 0.592 | 0.201 | 0.009 | 15.000 | 47 | 24 | 78 | 1.567 | 0.590 | 0.362 |
| Kai Kamaka III | 0.443 | 0.395 | 0.592 | 0.112 | 0.086 | 15.000 | 50 | 26 | 84 | 0.687 | 0.396 | 0.166 |


Andre Fili: data_cutoff=2026-10-03; ufc_fights_in_data=27; last_fight=2026-06-20 (112d ago); Kai Kamaka III: data_cutoff=2026-10-03; ufc_fights_in_data=6; last_fight=2026-07-11 (91d ago); matched_as_Kai Kamaka


**Malcolm Wellmaker vs Otari Tanzilovi** (M Bantamweight, 3 rounds) - fight P(KO/TKO) 0.288, P(sub) 0.197, P(distance) 0.516


| fighter | win_prob | elo_only_win_prob | p_distance | p_ko_for | p_sub_for | fight_time_median_min | sig_strikes_median | sig_strikes_p25 | sig_strikes_p75 | td_mean | p_td_ge1 | p_td_ge2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Malcolm Wellmaker | 0.416 | 0.554 | 0.516 | 0.164 | 0.068 | 15.000 | 37 | 18 | 64 | 0.299 | 0.224 | 0.055 |
| Otari Tanzilovi | 0.584 | 0.446 | 0.516 | 0.124 | 0.128 | 15.000 | 33 | 16 | 57 | 3.329 | 0.736 | 0.557 |


Malcolm Wellmaker: data_cutoff=2026-10-03; ufc_fights_in_data=4; last_fight=2026-05-16 (147d ago); LOW_SAMPLE(<5 UFC fights; rates heavily shrunk to division means); Otari Tanzilovi: data_cutoff=2026-10-03; ufc_fights_in_data=1; last_fight=2026-06-20 (112d ago); LOW_SAMPLE(<5 UFC fights; rates heavily shrunk to division means); few_finish_history


Full per-line P(sig strikes over X.5) for X=10..150 step 5 is in `projections.csv`. `fight_time_median_min`: when P(distance) is below 50% the median is a finish time (on a 30-point quantile grid, so identical values across fights are a discretization artifact); `fight_time_mean_min` is also given.

## 5. Limitations

- Win model is trained on fighter-name-keyed data. Ten names collide in the bio table (e.g. two Bruno Silva, two Jean Silva); their histories are merged. None are tonight's fighters.
- 27 fights from 3 events (Road to UFC 4.6, Lopes vs. Silva, Grasso vs. Shevchenko 2) are missing from the event table; their dates are imputed from neighbouring events in the file (approximate), which can slightly misorder Elo history for those fighters.
- No injury, weight-cut, camp, odds, short-notice, style-matchup or opponent-quality adjustments. Sig-strike rates are not adjusted for opponent strength beyond the opponent's absorbed rate. Fighters with <5 UFC fights (Camilo 3, Wellmaker 4, Tanzilovi 1 in the data) are mostly division averages plus Elo, which, for a 1-fight Elo, is weak.
- Age gets a large weight in the win model (younger fighters favoured). It drives Camilo (25.8) over Herbert (38.4) to 72% versus 56% from Elo alone. That is a genuine historical pattern in the sample but a blunt instrument for a single fight.
- Win probability and method are modeled separately (reconciled with IPF), not jointly. Strikes and takedowns are modeled independently of who wins and of each other; a wrestler's takedowns are not tied to his own strike volume, and ground-and-pound/control time is not modelled.
- 5-round P(distance): holdout under-prediction (see section 2); the main-event number may be low by up to ~9 points. Fight-time median is only as good as the empirical finish-time distribution (not conditioned on weight class or fighters).
- Sig-strike lines: pre-2023 model drifted high on recent fights; the trailing-24-month scale for tonight is an unvalidated correction. Takedown probabilities are miscalibrated at the extremes. Count lines near 50% are the best-supported; far-tail lines (above ~100 strikes) are over-predicted by ~1-1.5 points.
- A `research/` folder in the working directory contained five qualitative matchup notes that I did not write and did not use as model input.
- Everything is statistical estimation from a single scraped data source; treat all probabilities as model estimates, not advice.
