"""Walk-forward backtest: train on past seasons, score the next one, repeat.

Runs every market (points, rebounds, assists, PRA) separately.

Two kinds of scores:
  * Count accuracy (nll, mae): how well the full stat distribution fits.
    Lower nll is better. This is the honest test with free data.
  * Over/under at line_proxy (brier, over_logloss, calibration): a rehearsal of
    prop scoring against a STAND-IN line. It is not evidence of betting edge;
    that needs real sportsbook lines.
"""
from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np
import pandas as pd

from oklahoma import calibrate, ingest
from oklahoma.features import STATS, build_features
from oklahoma.models import PLUS_FEATURES, PRODUCTION_MODEL, ContextGLMPlus, alpha_method, log_pmf, prob_over, registry

REPORTS = ingest.ROOT / "reports"
BASELINE = "season_avg"
# Models run when --models is not given: the baselines, the plus ladder and the production model. The
# experiments that did not become production (plus2o, plus2s) are opt-in, as is any new variant.
DEFAULT_MODELS = ("season_avg", "last10", "rate_x_minutes", "context_glm", "context_glm_plus", "context_glm_plus2",
                  PRODUCTION_MODEL)


def walk_forward(
    feats: pd.DataFrame,
    model_names: list[str],
    test_seasons: list[int],
    train_window: int = 5,
    min_prior_games: int = 5,
    markets: list[str] = STATS,
) -> pd.DataFrame:
    models = registry()
    rows = []
    for market in markets:
        line_col = f"line_proxy_{market}"
        eligible = feats[(feats["career_games"] >= min_prior_games) & feats[line_col].notna()]
        for season in test_seasons:
            train = eligible[(eligible["season"] < season) & (eligible["season"] >= season - train_window)]
            test = eligible[eligible["season"] == season]
            if train.empty or test.empty:
                continue
            assert train["season"].max() < season, "training data leaked into the test season"
            y = test[market].to_numpy()
            line = test[line_col].to_numpy()
            for name in model_names:
                m = models[name](market).fit(train)
                mu = m.predict_mean(test)
                alpha = m.alpha_for(mu)
                rows.append(pd.DataFrame({
                    "market": market,
                    "model": name,
                    "season": season,
                    "game_id": test["game_id"].to_numpy(),
                    "athlete_id": test["athlete_id"].to_numpy(),
                    "player": test["athlete_display_name"].to_numpy(),
                    "rookie": test["rookie"].to_numpy(),
                    "starter_gameday": test["starter"].to_numpy(),
                    "starter_prev": test["starter_prev"].to_numpy(),
                    "position": test["athlete_position_abbreviation"].to_numpy(),
                    "playoffs": test["playoffs"].to_numpy(),
                    "teammates_out": test["out_minutes"].to_numpy() >= 20,
                    "actual": y,
                    "mu": mu,
                    "alpha": alpha,
                    "nll": -log_pmf(y, mu, alpha),
                    "line": line,
                    "p_over": prob_over(line, mu, alpha),
                    "went_over": (y > line).astype(int),
                }))
    return pd.concat(rows, ignore_index=True)


def plus_coefficients(feats: pd.DataFrame, season: int, train_window: int = 5,
                      min_prior_games: int = 5) -> pd.DataFrame:
    """Standardized coefficients of the added features, from the model trained for `season`."""
    out = {}
    for market in STATS:
        el = feats[(feats["career_games"] >= min_prior_games) & feats[f"line_proxy_{market}"].notna()]
        train = el[(el["season"] < season) & (el["season"] >= season - train_window)]
        m = ContextGLMPlus(market).fit(train)
        out[market] = m.glm_.coef_[-len(PLUS_FEATURES):]
    return pd.DataFrame(out, index=PLUS_FEATURES).round(4)


def score(results: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    r = results.assign(
        abs_err=(results["actual"] - results["mu"]).abs(),
        brier=(results["p_over"] - results["went_over"]) ** 2,
        over_logloss=-(
            results["went_over"] * np.log(results["p_over"].clip(1e-6, 1 - 1e-6))
            + (1 - results["went_over"]) * np.log((1 - results["p_over"]).clip(1e-6, 1 - 1e-6))
        ),
    )
    out = r.groupby(by + ["model"]).agg(
        n=("nll", "size"), nll=("nll", "mean"), mae=("abs_err", "mean"),
        brier=("brier", "mean"), over_logloss=("over_logloss", "mean"),
    )
    if BASELINE not in out.index.get_level_values("model"):
        return out.round(4)
    base = out.xs(BASELINE, level="model")["nll"] if by else out.loc[BASELINE, "nll"]
    if by:
        out["nll_vs_baseline"] = out["nll"] - out.index.droplevel("model").map(base).to_numpy()
    else:
        out["nll_vs_baseline"] = out["nll"] - base
    return out.round(4)


def calibration(results: pd.DataFrame, model: str, bins: int = 10) -> pd.DataFrame:
    r = results[results["model"] == model]
    edges = np.linspace(0, 1, bins + 1)
    bucket = pd.cut(r["p_over"], edges, include_lowest=True)
    return (
        r.groupby(bucket, observed=True)
        .agg(n=("p_over", "size"), predicted=("p_over", "mean"), actual=("went_over", "mean"))
        .round(3)
    )


def segment(results: pd.DataFrame) -> pd.DataFrame:
    seg = results.assign(
        group=np.select(
            [results["rookie"], results["starter_gameday"]],
            ["rookie", "veteran_starter"],
            default="veteran_bench",
        )
    )
    return score(seg, ["group"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--test-seasons", default="2021-2026")
    ap.add_argument("--train-window", type=int, default=5)
    ap.add_argument("--min-prior-games", type=int, default=5)
    ap.add_argument("--models", default=",".join(DEFAULT_MODELS))
    ap.add_argument("--markets", default=",".join(STATS))
    ap.add_argument("--out-dir", default="reports",
                    help="where rows, calibration and summary are written (relative paths are under the repo root); "
                         "the default is the production reports/")
    ap.add_argument("--production-model", default=PRODUCTION_MODEL,
                    help="model whose over/under probabilities the calibration map is fit on "
                         "(also the model recorded in the calibration file's _meta)")
    args = ap.parse_args()
    if args.production_model not in registry():
        raise SystemExit(f"unknown --production-model {args.production_model!r}; choose from {sorted(registry())}")
    out_dir = pathlib.Path(args.out_dir)
    out_dir = out_dir if out_dir.is_absolute() else ingest.ROOT / out_dir

    if not ingest.GAMES_PATH.exists():
        raise SystemExit("no data yet: run `python -m oklahoma.ingest` first")
    feats = build_features(pd.read_parquet(ingest.GAMES_PATH))
    test_seasons = ingest.parse_seasons(args.test_seasons)
    results = walk_forward(
        feats, args.models.split(","), test_seasons,
        args.train_window, args.min_prior_games, args.markets.split(","),
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    results.to_parquet(out_dir / "backtest_rows.parquet", index=False)
    if args.production_model in set(results["model"]):
        # Which markets get calibrated is decided by calibrate.fit_by_rule (walk-forward keep-or-drop rule)
        # and travels with the file as _meta.apply_to, so projections never calibrate a market the rule dropped.
        params, meta, _ = calibrate.fit_by_rule(results[results["model"] == args.production_model],
                                                args.production_model, alpha_method(registry()[args.production_model]))
        calibrate.save(params, out_dir / "calibration.json", meta=meta)

    overall = score(results, ["market"])
    by_season = score(results, ["market", "season"])
    teammates = score(results, ["market", "teammates_out"])
    coefs = plus_coefficients(feats, max(test_seasons), args.train_window, args.min_prior_games)
    sections = [
        ("Overall by market (lower nll is better; nll_vs_baseline < 0 beats season average)", overall),
        ("By market and test season", by_season),
        ("Games with >= 20 rotation minutes missing (teammates_out) vs not", teammates),
        (f"context_glm_plus: standardized coefficients of added features ({max(test_seasons)} fold)", coefs),
    ]
    for market in args.markets.split(","):
        mres = results[results["market"] == market]
        best = score(mres, [])["nll"].idxmin()
        sections.append((f"Calibration, {market}, best model {best}", calibration(mres, best)))

    text = "\n\n".join(f"## {title}\n\n{table.to_string()}" for title, table in sections)
    (out_dir / "summary.txt").write_text(text + "\n")
    summary = {
        "params": vars(args),
        "overall": overall.reset_index().to_dict(orient="records"),
        "plus_coefficients": coefs.to_dict(),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, default=str, indent=1))
    print(text)
    print(f"\nrows -> {out_dir / 'backtest_rows.parquet'}\nsummary -> {out_dir / 'summary.txt'}")


if __name__ == "__main__":
    main()
