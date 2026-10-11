# Oklahoma: handoff notes

For whoever picks this up next (a person or an agent such as Manus).

## What this is

A WNBA player-prop research model following Bill Benter's published method
(1994, "Computer Based Horse Race Handicapping and Wagering Systems: A Report"):

1. **Fundamental model**: predict each player's stat distribution from public,
   pregame data. **Built** (`oklahoma/models.py`, `context_glm`).
2. **Market blend**: combine the model's probability with the de-vigged market
   probability, with weights fit on history. **Built and tested on simulated
   lines (`oklahoma/benter.py`). Needs real historical prop lines to run.**
3. **Bet sizing**: fractional Kelly on the blended edge. **Built, same status.**

Research and backtest only. Nothing places bets.

## Set up the repo

```bash
unzip oklahoma.zip && cd oklahoma
git init -b main && git add -A && git commit -m "Phase 1"
# create an empty private GitHub repo named "oklahoma", then:
git remote add origin https://github.com/<your-account>/oklahoma.git
git push -u origin main
```

(Or clone from `oklahoma.bundle`: `git clone oklahoma.bundle oklahoma`.)

## Run it

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m oklahoma.ingest --seasons 2015-2026   # free ESPN box scores via sportsdataverse
python -m oklahoma.backtest                     # walk-forward 2021-2026
python -m pytest -q                             # 70 tests, incl. the leakage tests (about a minute)
```

## Phase 1 result (2021-2026, ~30k player-games)

| Model | NLL vs season average (lower = better) | Brier (coin flip = 0.25) |
|---|---|---|
| context_glm | -0.035 | 0.240 |
| rate_x_minutes | -0.018 | 0.244 |
| season_avg | 0 | 0.248 |
| last10 | +0.005 | 0.251 |

`context_glm` beats the baselines in every test season, but the over/under scores
are against a **stand-in line** (`line_proxy`), not real sportsbook lines. No
betting edge has been shown yet.

## Rules that must survive any changes

- **No leakage.** Features may only use games that tipped before the row's game.
  `tests/test_pipeline.py::test_features_use_only_prior_games` enforces this;
  keep it passing and add new features to `PREGAME_COLS`.
- **Walk-forward only.** Never train on the season being scored.
- **Public, official data only.** Box scores, official injury reports, schedules,
  bios, licensed odds APIs. No scraping of personal social media, no tracking of
  players' private lives, no scraping sportsbook sites against their terms.
- **No fabricated lines.** If odds data is missing, the row is skipped.

## Owner's working rule ("CEO agent logic")

Default answer on this project is **yes: proceed without asking**, except for three
things that always need the owner's explicit OK:
1. Spending money (data purchases, bets, paid plans).
2. Deleting data or anything else irreversible.
3. Security changes (policies, grants, keys, extensions).

## Round 2 (done)

Points, assists, PRA; teammates out; defense by position; schedule load; return
from absence; hot streak; Benter stages 2-3. `context_glm_plus` beats
`context_glm` in all 4 markets in all 6 test seasons (2021-2026).
Not done: travel distance.

## Round 3 (done)

- All-Star / exhibition games removed from the data (222 rows).
- Coach tenure feature from `oklahoma/reference/coaches.csv` (Wikipedia "List of
  WNBA head coaches", mid-season changes placed by games-coached arithmetic;
  three 2026 coaches marked UNKNOWN (new coach)). Ablation: no measurable effect
  (+/-0.0003 nll), so it is computed but kept out of the model.
- Supabase security review: see supabase/PENDING_security_fixes.sql.

## Round 4 (done, 2026-10-04)

- Two new stats: **usage** (shot attempts + 0.44*free throws + turnovers per minute)
  and **game pace** (both teams' recent combined scores vs league). `context_glm_plus2`
  beats `context_glm_plus` in 23 of 24 market-seasons; biggest gain on points.
  It is now the projection model (`oklahoma/project.py`).
- Slate projector: `python -m oklahoma.project --date YYYY-MM-DD [--out ...] [--add ...]`.
- Team win probability from summed player points (2022-26): Brier 0.230-0.238 vs
  0.248 home-only, ~60% accuracy. Weak; markets are better. Use only as a cross-check.
- Free market data: Gemini prediction markets (game moneylines + champion) logged to
  Supabase `public.market_prices`. Routine "Gemini WNBA price snapshot" runs
  11:47 and 17:47 ET daily; **needs Gemini + Supabase connectors attached in the
  claude.ai routines UI** (created without them).
- `reports/tracking_ledger.csv`: model vs market, stake, result. Log every bet.

## Round 5 (2026-10-04/05)

- **Spread fix:** negative-binomial dispersion is now fit per fifth of predicted mean
  (`Model.alpha_for`). One pooled value made stars' distributions far too wide
  (A'ja Wilson fair points line was ~2-4 too low). Points nll improved ~0.085.
  CORRECTION: the remaining flaw is NOT stars' overs being under-predicted. Calibration shows
  the model is overconfident in lopsided probabilities (slope ~0.8). Fixed by `oklahoma/calibrate.py`
  (p' = sigmoid(a + b*logit(p)), fit per market in the backtest, saved to `reports/calibration.json`,
  applied to points and PRA only; Round 7 replaced that list with a per-file rule). `project.py` now outputs `p_over_cal`; use it, not `p_over_fair`.
- **Semifinal Game 1 results (Oct 4):** ATL 92, NY 82; GS 71, LV 60. Graded once the mirror
  refreshed: slight over-projection (bias points -1.1, assists -0.5, PRA -1.5), 72.8% of results
  inside the 10-90% range (target 80%, n=34, noisy). Big misses were minutes/injury driven
  (Gray 11 min, Hayes 11, Loyd 17). Playoff bias in the backtest is ~0. Bets: 1 of 3 props won
  (Fiebich/Jones unders were overconfident calls); GS and ATL moneylines won. See the ledger. Game 2s: ATL-NY Oct 7 7:30 PM ET, GS-LV Oct 7 9:30 PM ET.
- **Injuries that invalidate the baseline projections:** Allisha Gray (ATL) left Game 1
  with a hand injury; Jewell Loyd (LV) left with a left leg injury (ruled out after 3rd-qtr
  start); Veronica Burton (GS) left in the 3rd and did not return. Use `--out` / re-check the
  official injury report before projecting Game 2.
- Results are filled in `reports/tracking_ledger.csv`.
- **Gemini price script:** `python -m oklahoma.gemini_prices [--show]` appends to `data/market_prices.csv`.
  No API key (public read-only). The default endpoint URL is UNVERIFIED (blocked in the dev
  container); override with `GEMINI_EVENTS_URL` / `--url`. Parser tested on real listing data.
  Replaces the connector-dependent routine.

## Round 6 (2026-10-09): compute jobs

- `jobs/` holds 7 heavy jobs + `run_all.py` (resumable). See `COMPUTE_PLAN.md`. `oklahoma/joint.py` (copula) and `oklahoma/threes.py` (3PM model) are new. 16 tests pass.
- Ingest now merges partial `--seasons` instead of overwriting (earlier `--seasons 2026` wiped the dataset). Data carries `threes_made`/`threes_attempted`.
- Leakage test caught a real bug in the first 3PM feature code (whole-data league 3P%); fixed.

## Round 7 (2026-10-10): production model, calibration rule, line comparison

**Disclosure (read before trusting the numbers below).** The `starter_prev` terms behind `context_glm_plus2si` were chosen after looking
at the 2021-26 playoff residuals by previous-game starter (bench players over-projected, starters under-projected). The walk-forward backtest never
scores a row with a model trained on it, but it scores the same seasons that motivated the terms, so the gain is optimistic. Confirm it on the
2027 playoffs (a forward, untouched sample) before leaning on it; until then treat the playoff role effect as plausible, not proven.

What changed (numbers and tables are in `COMPUTE_PLAN.md`, "Results so far"):
- **Production model is now `context_glm_plus2si`** (`models.PRODUCTION_MODEL`; `project.py`, `compare.py` and `backtest.py` default to it): plus2 plus
  `starter_prev` and `starter_prev` x playoffs, in-sample dispersion. It beat plus2 in all four markets and all six seasons (points -0.0036, PRA -0.0059 mean nll,
  both bootstrap clusterings exclude 0) and cut the playoff bench over-projection by 93% (points) and 95% (PRA). `plus2o` (out-of-sample dispersion alone)
  was rejected; `plus2s` (= plus2si with out-of-sample dispersion) is no better. Both classes stay for reproducibility.
- **`features.starter_prev`**: did she start her previous game. The game's own `starter` flag is only known at tip, so no model or the minutes model reads it.
- **Calibration by rule** (`calibrate.fit_by_rule`): fit on seasons < s, score s (2022-26); keep a market only if log loss improves in >= 4 of 5 seasons and the
  pooled gain is >= 0.001. Result for plus2si: **points only** (PRA 4 of 5 but +0.0009; assists 3 of 5; rebounds 3 of 5). `calibrate.calibrate()` now follows the
  `apply_to` list inside `reports/calibration.json` (`_meta`); the module constant is a fallback for older files. So PRA, assists and rebounds probabilities are
  raw model probabilities and `compare.py` marks them UNCALIBRATED. Old file: `reports/calibration_v2_backup.json`.
- **`python -m oklahoma.backtest`** takes `--out-dir` and `--production-model`; its default model list now ends with the production model and it writes the calibration
  file with `_meta`. Production rows (`reports/backtest_rows.parquet`) were regenerated on the current data; the old file is `reports/backtest_rows_v2_backup.parquet`.
  The v3 experiment lives in `reports/v3/` (`jobs/j08_v3_eval.py`: bootstraps, gate, calibration check).
- **`python -m oklahoma.compare --date D --team T --lines lines.csv [--out ..] [--add ..] [--log scratch.csv]`**: for each line, the model's side, P(more), P(less),
  P(push) (they sum to 1), break-even for a pick'em slip and the edge. Flags: STALE, LOW_HISTORY, PLAYOFF_BENCH_MORE, BIG_DISAGREEMENT, SAME_PLAYER, COMBO_UNCALIBRATED,
  UNCALIBRATED, NOT_ON_ROSTER and the new MINUTES_DIFF (the minutes model's median differs from her recent minutes by 3 or more; a flag, never a model input).
  The old ad hoc playoff role shift now applies to `context_glm_plus2` only and is switched off automatically for models with `starter_prev` terms, so the effect is not counted twice.
  Every run appends all rows to `data/line_log.csv` unless `--log` points elsewhere.
- **Minutes** (`oklahoma/minutes.py`, `jobs/j06_minutes.py --seeds 5`): quantile GBM with a conformalized 80% band, pregame inputs only. Gate passes on the 5-seed average
  (0.316 min MAE gain, coverage 0.807) but thinly: seed 2 alone fails, and playoff coverage is 0.767. Not wired into the projections yet, only into the flag.
- **3PM model** now fits dispersion per fifth of the predicted mean like the other markets.
- Plugin `oklahoma-slate` (outside this repo): its daily-slate skill now runs `oklahoma.compare`.
- 70 tests pass (16 at the end of Round 6).

Still open: the 2027 playoff confirmation above; real prop odds (see Next); the copula (`jobs/j02`) was fit on plus2 rows, not refit on plus2si;
`reports/summary.txt` is from the earlier backtest (the current numbers are in `reports/v3_full/summary.txt`); `MANUS_QUEUE.md` still quotes an old test count.

## Next

1. Load purchased odds into Supabase `prop_lines`, match to ESPN game/athlete ids.
2. Run `benter.blend_backtest` on real lines: blend weights, ROI, closing-line value.
3. Only if that holds up: forward-log live lines for a season before staking.

## Historical odds requirements (for the purchase)

WNBA player props (pts/reb/ast/PRA), 2023-2026, both over and under prices,
multiple books incl. at least one sharp book, timestamps (open and close).
Ask for a sample file before paying. Keep the API key in an environment
secret (e.g. `ODDS_API_KEY`), never in code.
