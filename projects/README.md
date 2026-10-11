# Benter-method betting research models (research only — nothing places bets)

Backup of the working code from the Claude Code session, so daily research runs survive container resets.

- `oklahoma/` — WNBA player-prop model (Poisson GLM + negative-binomial spread, walk-forward backtest, calibration, `compare.py` for Dabble lines).
  The "Round 7" build (Plus2SI playoff-role model, calibration `_meta`) is **partially done and not yet reviewed**; Plus2SI passed its gate in `reports/v3/gate.json`.
  Raw data (`data/`) and backtest parquet files are excluded; rebuild with `python -m oklahoma.ingest --seasons 2015-2026 --force`.
  The `supabase/` folder is intentionally left out of this repo (it references a live project and a pending security fix).
- `ufc/` — UFC win model (Elo + antisymmetric logistic on pre-fight differentials; holdout 2023-26 log loss 0.641 vs Elo 0.678), method/duration model and stat-prop projections. Data from Greco1899/scrape_ufc_stats.
- `nfl/` — NFL game lines (`model/`: Elo+QB ratings, walk-forward vs nflverse closing lines; holdout 2023-25 ATS 47.8%, totals 51.5% — **fails**, no game-line bets), market angles (`market/`), and player props (`props/`: recency-weighted negative-binomial GLM; `projections.csv` holds the Dabble/Underdog cutoffs). Raw data excluded; scripts re-download from nflverse.
- `tennis/` — ATP and WTA point-by-point Monte Carlo (`atp/`, `wta/`), with the skeptic re-check in `atp/review/`. WTA match-totals lookup in `wta/grid_pwin_totals.csv`.

Rules: public data only, no app scraping/logins, no insider info, no spending without the owner's OK.
