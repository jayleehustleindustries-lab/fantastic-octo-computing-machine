# Compute plan: the heavy jobs for the desktop

Everything below is built, smoke-tested (`--quick`, 2025-26, tiny slices) and ready. The desktop only has to run it.
Preliminary quick-run readings are marked PRELIMINARY: 2 seasons, small samples, NOT conclusions.

## Desktop setup (10 minutes, needs good Wi-Fi once)
```bash
unzip oklahoma-manus-handoff.zip && cd oklahoma
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
python -m oklahoma.ingest --seasons 2015-2026 --force     # about 55,500 player-games. A partial range now merges, never overwrites.
python -m pytest -q                                       # expect 70 passed (about a minute)
python -m jobs.run_all --quick                            # smoke test, a few minutes
python -m jobs.run_all --workers 8                        # the real run (set workers = CPU cores - 1)
python -m jobs.j06_minutes --seeds 5 --workers 2          # j06 averaged over 5 seeds (run_all runs 1 seed)
python -m oklahoma.backtest --models season_avg,context_glm_plus2,context_glm_plus2s,context_glm_plus2si --out-dir reports/v3 --production-model context_glm_plus2si
python -m jobs.j08_v3_eval                                # the plus2si adoption test, bootstraps included (about a minute)
```
Results land in `reports/jobs/*.csv`; log in `reports/jobs/run.log`. A crash resumes: finished tasks are skipped.
Rerun the ingest each morning after about 10:39 GMT, then project the slate.

## The jobs, ranked by (value to the model) / (cost)
| # | Job | Question it answers | Cost (est., 8 cores) | Gate to adopt |
|---|---|---|---|---|
| 1 | `j06_minutes` quantile GBM | Minutes cause most big misses. Can a minutes model beat min_ewm? | 5-10 min per seed | MAE gain >= 0.30 min in >= 5 of 6 seasons, pooled 10-90 coverage 78-82%, every season 76-84%. **Full run, pregame inputs only (`starter_prev`): PASSES on the 5-seed average, thinly. See "Results" below.** The earlier +0.38 min read the game's own starter flag (known only at tip) and is void. |
| 2 | `j04_threes` | 3PM market (missing today). Does the 3PA-rate model beat rate x minutes? | 2 min | positive nll gain in most seasons. PRELIMINARY: +0.012 to +0.025 nll |
| 3 | `j03_bootstrap` | Are model gains and the overconfidence real, or noise? (game-clustered CIs) | 10-20 min | CI excludes 0. PRELIMINARY: calibration slope points 0.81 [0.71, 0.87]; plus2 vs plus on PRA/rebounds not clearly better |
| 4 | `j02_joint_calibration` | Copula for combo props (P+R, P+A, R+A, PRA) vs independence | 20-40 min | lower log loss in most seasons. PRELIMINARY (400 rows): no gain, needs the full 20k-row run |
| 5 | `j01_ablation` | Which feature groups earn their place? (16 groups x 4 markets x 6 seasons) | 15-30 min | drop groups with delta < 0.0005 in most seasons |
| 6 | `j07_gbm_mean` | Does a nonlinear boosted mean beat the GLM? | 30-60 min | gain > 0.002 nll in most market-seasons. PRELIMINARY: mixed (-0.003, +0.003) |
| 7 | `j05_hyperparams` | Tune half-life, opponent shrink, rotation threshold, train window (108 configs, rebuilds features each) | 1-3 hours | beat default by > 0.001 nll AND most seasons |

Run order is dependency-safe: backtest -> j03, j04, j06 -> j02 (needs backtest rows) -> j01 -> j07 -> j05.

## Strategy: how to spend the compute
1. **Fix the biggest error source first (minutes).** If j06 holds up on the full run, wire quantile minutes into the projector and simulate stat = rate x minutes draws. This also fixes the "model blind to a role cut" problem on the slate.
2. **Add the missing market (3PM)** if j04 holds. It needs a leakage test (done: `test_three_features_use_only_prior_games`; it already caught and fixed one real leak).
3. **Prune before adding.** j01 first, so every later experiment starts from a smaller model. Coach tenure was already pruned this way.
4. **Price combos correctly.** If j02 passes, `project.py` uses the copula for P+R, P+A, R+A instead of independent sums (the module `oklahoma/joint.py` is ready).
5. **Prove or kill the fancy stuff.** j07 and j05 only get adopted through their gates. Expect small gains: the signal ceiling with box-score data is low.
6. **None of this proves a betting edge.** Real prop-odds history is the only thing that does. That purchase needs the owner's explicit OK (free sample first).

## After the run: decide in this order
Open `reports/jobs/*.csv`. For each job compare to its gate in the table. Bring the CSVs back to a session (paste or attach) and I will make the adopt/reject calls and wire the winners into `project.py`.

## Not built (needs data or approval)
Real-odds blend and CLV backtest (needs purchased odds), automated injury report, wearable/drill inputs (no data), tennis model (design only).

## Results so far (Round 7, 2026-10-10; walk-forward 2021-26, 29,843 player-games per market)

### j06 minutes (pregame inputs only, `starter_prev` instead of the game's own flag)
| | MAE gain vs `min_ewm` (min) | pooled 10-90 coverage | seasons with gain >= 0.30 |
|---|---|---|---|
| seed 0 (the single run reported before) | 0.319 | 0.806 | 5 of 6 (2025: 0.288) |
| average of seeds 0-4 | 0.316 | 0.807 | 5 of 6 (2025: 0.290) |
| individual seeds 0, 1, 2, 3, 4 | 0.319, 0.316, 0.315, 0.318, 0.312 | 0.806, 0.806, 0.809, 0.808, 0.807 | 5, 5, 4, 5, 5 |

Gate verdict on the 5-seed average: passed (every season's coverage is inside 76-84%: 0.778 to 0.837). Seed caveat: 2025 is under 0.30 for every seed
(0.288, 0.292, 0.293, 0.299, 0.279), seed 2 alone also misses 2021 (0.297) and so fails the 5-of-6 rule, and playoff coverage is only 0.767 (n=2,194).
The pass is real but thin and the band is a bit narrow in the playoffs. The seed only changes the early-stopping validation split; the models are otherwise identical.
Files: `reports/jobs/j06_minutes*.csv|json` (5-seed), `*_1seed.*` (the earlier single run), `j06_minutes_seeds.csv` (per seed).
Use in the product: `compare.py` flags `MINUTES_DIFF` when her minutes-model median differs from her recent minutes by 3 or more. It is a flag only, not a model input.

### Plus2O (out-of-sample dispersion alone): REJECTED
Same mean model as plus2, dispersion fit on the last training season. Archived run: `reports/v3_prev_plus2o/`.
Calibration slope did not move toward 1 (points 0.822 -> 0.815, PRA 0.890 -> 0.888) and nll got worse than plus2 in all four markets
(mean nll plus2o - plus2: points +0.0019, PRA +0.0010, rebounds +0.0011, assists +0.0006; better in only 1-2 of 6 seasons).
The class stays in `models.py` so the run can be reproduced.

### Plus2SI (plus2 + `starter_prev` and `starter_prev` x playoffs, in-sample dispersion): ADOPTED as the production model
Gate (plus2si - plus2 mean nll <= -0.0005 in points or PRA with both 95% CIs below 0 and >= 5 of 6 seasons improved; no market worse than +0.0003;
playoff bench over-projection cut by >= 30% in points and PRA) passed. Mean nll plus2si - plus2, 95% CI from 2000 reps resampling games / 2000 reps
resampling player-seasons:

| market | mean | CI games | CI player-seasons | seasons improved |
|---|---|---|---|---|
| points | -0.0036 | [-0.0051, -0.0021] | [-0.0052, -0.0020] | 6 of 6 |
| PRA | -0.0059 | [-0.0079, -0.0040] | [-0.0078, -0.0040] | 6 of 6 |
| rebounds | -0.0031 | [-0.0045, -0.0018] | [-0.0044, -0.0019] | 6 of 6 |
| assists | -0.0031 | [-0.0041, -0.0021] | [-0.0041, -0.0021] | 6 of 6 |

Playoff bench over-projection (mean actual - mu, n=988): plus2 points -0.924 -> plus2si +0.065 (cut 93%); PRA -1.641 -> +0.090 (cut 95%).
Playoff starters (n=1,206): points +0.789 -> +0.025, PRA +1.207 -> -0.125. Versus plus2s (starter terms plus out-of-sample dispersion) plus2si is better in
points (-0.0017, 6 of 6) and not distinguishable in PRA (-0.0009, CI [-0.0021, 0.0003]), so the out-of-sample dispersion adds nothing.
Calibration slopes (1 = calibrated), plus2 -> plus2si: points 0.822 -> 0.841, PRA 0.890 -> 0.909, assists 0.839 -> 0.865, rebounds 0.946 -> 0.919.
**Disclosure:** the starter terms were chosen after looking at these same 2021-26 playoff residuals, so the gain is optimistic; confirm on the 2027 playoffs.
Files: `reports/v3/` (rows, `eval.csv`, `gate.json`, `calibration.json`, `eval.log`).

### Calibration by rule on plus2si's walk-forward rows (fit on seasons < s, score s, s = 2022-26)
Keep a market only if log loss improves in >= 4 of 5 seasons AND the pooled gain is >= 0.001.

| market | seasons improved | pooled gain | applied |
|---|---|---|---|
| points | 5 of 5 | +0.0024 | yes |
| PRA | 4 of 5 | +0.0009 | no (just under 0.001) |
| assists | 3 of 5 | +0.0002 | no |
| rebounds | 3 of 5 | -0.0001 | no |

`reports/calibration.json` now carries `_meta` (model, alpha_method, fit_seasons, n, apply_to = ["points"]) and `calibrate.calibrate()` follows its `apply_to`;
the module constant is only a fallback for older files. The v2 file (points, PRA, assists) is saved as `reports/calibration_v2_backup.json`.
Production backtest rows were regenerated on the current data with all seven default models (plus2si rows are identical to `reports/v3/`); the previous
file is `reports/backtest_rows_v2_backup.parquet`.
