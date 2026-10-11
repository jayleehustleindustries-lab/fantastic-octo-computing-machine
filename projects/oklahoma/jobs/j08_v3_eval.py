"""J08: does plus2si (plus2 + previous-game starter terms, same dispersion method) earn production status?

Reads reports/v3/backtest_rows.parquet from
    python -m oklahoma.backtest --models season_avg,context_glm_plus2,context_glm_plus2s,context_glm_plus2si \
        --out-dir reports/v3 --production-model context_glm_plus2si
and writes reports/v3/eval.csv (long format: section, market, subject, metric, value, CIs, reps), gate.json and
reports/v3/calibration.json (with a "_meta" block). Production files are never touched: promotion is a separate,
backed-up copy step.

Models: plus2 (production), plus2s (starter terms + out-of-sample dispersion) and plus2si (the same starter terms
with plus2's in-sample dispersion). plus2si vs plus2 is the adoption test; plus2si vs plus2s shows what
out-of-sample dispersion adds on top. Out-of-sample dispersion alone (plus2o) was rejected by the earlier version of
this job; that run is archived in reports/v3_prev_plus2o/.

Sections of eval.csv. "reps" = --reps (default 2000), "aux reps" = --aux-reps (default 500; slopes and residual
means are costlier per rep and only need a rough interval). Every CI is a percentile 95% interval of a cluster bootstrap:
  clusters     number of games and of player-seasons the bootstraps resample
  delta_nll    candidate minus reference, per-row mean nll, by market. CIs: games resampled (lo_game/hi_game, reps)
               AND player-seasons resampled (lo_player_season/hi_player_season, reps; a player's games within a
               season are correlated). Also the difference in each season 2021-2026 and how many seasons improved.
  slope        calibration slope (logistic of went_over on logit(p_over)), games resampled, aux reps
  coverage     observed vs model-nominal coverage of the [q10, q90] stat interval (no CI; a discrete NB interval is
               not exactly 80%, so the nominal column is the fair comparison)
  resid        mean residual (actual - mu) by playoffs x previous-game starter; negative = over-projection.
               CI: games resampled, aux reps
  role_cut     relative cut in the playoff bench over-projection (and in the playoff starter under-projection)
               versus the reference model. CIs: games AND player-seasons resampled, reps
  calib_check  walk-forward calibration of the adopted model (calibrate.walk_forward_check)

Gate for adopting plus2si over production plus2 (thresholds are constants below). "Adopted" only means the evidence
supports switching; nothing is switched here.
  * plus2si - plus2 mean nll <= -0.0005 with BOTH 95% CIs (games, player-seasons) below 0 and >= 5 of 6 seasons
    improved, in points or PRA;
  * no market (all four) worse than plus2 by more than 0.0003;
  * playoff bench over-projection cut by >= 30% for points and for PRA.
If it fails, production stays plus2 and calibration is fit on plus2's rows.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy import stats

from jobs import common as C
from jobs.j03_bootstrap import weighted_logit_slope
from oklahoma import calibrate
from oklahoma.models import _nb_params, alpha_method, registry

V3 = C.ROOT / "reports" / "v3"
BASE, STARTER, SI = "context_glm_plus2", "context_glm_plus2s", "context_glm_plus2si"
MODELS = (BASE, STARTER, SI)
PAIRS = [(SI, BASE), (SI, STARTER), (STARTER, BASE)]     # (candidate, reference); the first is the gate
KEY = ["season", "game_id", "athlete_id"]
SEASONS = list(range(2021, 2027))
KEY_MARKETS = ("points", "pra")

WORSE_TOL = 0.0003            # no market may get worse than this versus plus2
MIN_GAIN = -0.0005            # plus2si - plus2 mean nll must be at most this in points or PRA
MIN_SEASONS = 5               # ... with both CIs below 0, and negative in this many of 6 seasons
BENCH_CUT = 0.30              # playoff bench over-projection must shrink by this share (points and PRA)
N_RESID_MIN = 30              # fewest rows for a residual CI


def label(pair) -> str:
    short = lambda m: m.replace("context_glm_", "")
    return f"{short(pair[0])} - {short(pair[1])}"


# ---------- bootstrap helpers ----------

def codes(labels) -> tuple[np.ndarray, int]:
    inv = pd.factorize(pd.Series(labels))[0]
    return inv, int(inv.max()) + 1


def boot_mean(x: np.ndarray, inv: np.ndarray, G: int, reps: int, rng, mask=None) -> tuple[float, float]:
    """95% CI of the row mean of x over `mask`, resampling whole clusters (inv = cluster code per row)."""
    keep = np.ones(len(x), bool) if mask is None else mask
    s = np.bincount(inv[keep], weights=x[keep], minlength=G)
    n = np.bincount(inv[keep], minlength=G).astype(float)
    idx = rng.integers(0, G, (reps, G))
    boot = s[idx].sum(1) / n[idx].sum(1)
    return float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))


def bias_cut(b_ref, b_cand):
    """Share of the reference bias removed: 1 - |candidate| / |reference| (negative if it got worse).
    A bootstrap resample whose reference bias is exactly 0 gives inf / NaN, which the quantiles treat honestly."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return 1 - np.abs(b_cand) / np.abs(b_ref)


def boot_cut(r_ref: np.ndarray, r_cand: np.ndarray, inv: np.ndarray, G: int, reps: int, rng, mask) -> tuple[float, float]:
    """95% CI of bias_cut of the mean residuals over `mask`, resampling whole clusters."""
    n = np.bincount(inv[mask], minlength=G).astype(float)
    s_ref = np.bincount(inv[mask], weights=r_ref[mask], minlength=G)
    s_cand = np.bincount(inv[mask], weights=r_cand[mask], minlength=G)
    idx = rng.integers(0, G, (reps, G))
    n_b = n[idx].sum(1)
    boot = bias_cut(s_ref[idx].sum(1) / n_b, s_cand[idx].sum(1) / n_b)
    return float(np.nanquantile(boot, 0.025)), float(np.nanquantile(boot, 0.975))


def logit(p):
    p = np.clip(np.asarray(p, dtype=float), 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def slope_ci(x, y, inv, G, reps, rng) -> tuple[float, float, float]:
    point = float(weighted_logit_slope(x, y, np.ones(len(x)))[1])
    sl = [weighted_logit_slope(x, y, np.bincount(rng.integers(0, G, G), minlength=G)[inv].astype(float))[1]
          for _ in range(reps)]
    return point, float(np.quantile(sl, 0.025)), float(np.quantile(sl, 0.975))


def interval(mu: np.ndarray, alpha: np.ndarray, lo_q=0.1, hi_q=0.9):
    """[q10, q90] of the count distribution and the probability the model itself puts inside it."""
    a = np.asarray(alpha, dtype=float)
    pois = a <= 1e-8
    n, p = _nb_params(mu, np.where(pois, 1.0, a))
    ppf = lambda q: np.where(pois, stats.poisson.ppf(q, mu), stats.nbinom.ppf(q, n, p))
    cdf = lambda k: np.where(pois, stats.poisson.cdf(k, mu), stats.nbinom.cdf(k, n, p))
    lo, hi = ppf(lo_q), ppf(hi_q)
    return lo, hi, cdf(hi) - cdf(lo - 1)


# ---------- evaluation ----------

def load(path) -> dict[str, dict[str, pd.DataFrame]]:
    """{market: {model: rows}} for MODELS, with identical row order across models (asserted)."""
    r = pd.read_parquet(path)
    missing = set(MODELS) - set(r["model"])
    if missing:
        raise SystemExit(f"{path} lacks models {sorted(missing)}; rerun the v3 backtest")
    out = {}
    for market, d in r[r["model"].isin(MODELS)].groupby("market"):
        per = {m: g.sort_values(KEY).reset_index(drop=True) for m, g in d.groupby("model")}
        for m in MODELS[1:]:
            assert per[m][KEY].equals(per[BASE][KEY]), f"{market}: {m} rows differ from {BASE}"
        out[market] = per
    return out


def evaluate(data, reps: int, aux_reps: int, seed: int = 8) -> tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(seed)
    rows: list[dict] = []

    def add(section, market, subject, metric, value, ci_game=(np.nan, np.nan), ci_ps=(np.nan, np.nan), n=np.nan,
            reps_game=np.nan, reps_ps=np.nan):
        rows.append({"section": section, "market": market, "subject": subject, "metric": metric, "value": value,
                     "lo_game": ci_game[0], "hi_game": ci_game[1], "lo_player_season": ci_ps[0],
                     "hi_player_season": ci_ps[1], "n": n, "reps_game": reps_game, "reps_player_season": reps_ps})

    stash: dict = {"delta": {}, "cut": {}, "slope": {}}
    for market, per in data.items():
        b = per[BASE]
        g_inv, G = codes(b["game_id"])
        p_inv, P = codes(b["athlete_id"].astype(str) + "_" + b["season"].astype(str))
        n = len(b)
        add("clusters", market, "games", "count", G, n=n)
        add("clusters", market, "player-seasons", "count", P, n=n)

        for pair in PAIRS:
            diff = (per[pair[0]]["nll"] - per[pair[1]]["nll"]).to_numpy()
            ci_g = boot_mean(diff, g_inv, G, reps, rng)
            ci_p = boot_mean(diff, p_inv, P, reps, rng)
            by_season = {s: float(diff[(b["season"] == s).to_numpy()].mean()) for s in SEASONS}
            improved = sum(v < 0 for v in by_season.values())
            add("delta_nll", market, label(pair), "mean", float(diff.mean()), ci_g, ci_p, n, reps, reps)
            for s, v in by_season.items():
                add("delta_nll", market, label(pair), f"season_{s}", v, n=int((b["season"] == s).sum()))
            add("delta_nll", market, label(pair), "seasons_improved", improved, n=len(SEASONS))
            stash["delta"][(market, pair)] = {"mean": float(diff.mean()), "game": ci_g, "ps": ci_p, "improved": improved,
                                              "by_season": by_season}

        y = b["went_over"].to_numpy(float)
        po = b["playoffs"].to_numpy(bool)
        sp = b["starter_prev"].to_numpy(bool)
        resid = {m: (d["actual"] - d["mu"]).to_numpy() for m, d in per.items()}
        for model, d in per.items():
            sl = slope_ci(logit(d["p_over"]), y, g_inv, G, aux_reps, rng)
            add("slope", market, model, "slope", sl[0], (sl[1], sl[2]), n=n, reps_game=aux_reps)
            stash["slope"][(market, model)] = sl[0]
            lo, hi, nominal = interval(d["mu"].to_numpy(), d["alpha"].to_numpy())
            inside = (d["actual"].to_numpy() >= lo) & (d["actual"].to_numpy() <= hi)
            add("coverage", market, model, "observed_q10_q90", float(inside.mean()), n=n)
            add("coverage", market, model, "model_nominal_q10_q90", float(nominal.mean()), n=n)
            add("coverage", market, model, "mean_alpha", float(d["alpha"].mean()), n=n)
            for is_po in (True, False):
                for is_st in (True, False):
                    m = (po == is_po) & (sp == is_st)
                    lab = f"{'playoffs' if is_po else 'regular'}/{'starter_prev' if is_st else 'bench'}"
                    ci = boot_mean(resid[model], g_inv, G, aux_reps, rng, m) if m.sum() > N_RESID_MIN else (np.nan, np.nan)
                    add("resid", market, f"{lab}/{model}", "mean_actual_minus_mu", float(resid[model][m].mean()), ci,
                        n=int(m.sum()), reps_game=aux_reps)

        # Playoff role bias: how much of the reference's bench over-projection / starter under-projection is gone?
        for pair in PAIRS:
            ref, cand = resid[pair[1]], resid[pair[0]]
            for kind, mask, wrong_sign in (("bench_overprojection", po & ~sp, -1), ("starter_underprojection", po & sp, 1)):
                b_ref, b_cand = float(ref[mask].mean()), float(cand[mask].mean())
                value = float(bias_cut(b_ref, b_cand)) if np.sign(b_ref) == wrong_sign else float("nan")
                ci_g = boot_cut(ref, cand, g_inv, G, reps, rng, mask) if np.isfinite(value) else (np.nan, np.nan)
                ci_p = boot_cut(ref, cand, p_inv, P, reps, rng, mask) if np.isfinite(value) else (np.nan, np.nan)
                add("role_cut", market, label(pair), f"playoff_{kind}_cut", value, ci_g, ci_p, int(mask.sum()), reps, reps)
                add("role_cut", market, label(pair), f"playoff_{kind}_ref_bias", b_ref, n=int(mask.sum()))
                add("role_cut", market, label(pair), f"playoff_{kind}_cand_bias", b_cand, n=int(mask.sum()))
                stash["cut"][(market, pair, kind)] = {"ref_bias": b_ref, "cand_bias": b_cand, "cut": value,
                                                      "ci_game": ci_g, "ci_player_season": ci_p, "n": int(mask.sum())}
    return pd.DataFrame(rows), stash


def decide(stash: dict, markets: list[str]) -> dict:
    """Apply the gate in the module docstring. Returns every number the decision used."""
    gate_pair = PAIRS[0]
    d, cuts = stash["delta"], stash["cut"]
    nll = {}
    for m in KEY_MARKETS:
        x = d[(m, gate_pair)]
        nll[m] = {"mean": x["mean"], "ci_game": x["game"], "ci_player_season": x["ps"], "seasons_improved": x["improved"],
                  "ok": bool(x["mean"] <= MIN_GAIN and x["game"][1] < 0 and x["ps"][1] < 0 and x["improved"] >= MIN_SEASONS)}
    vs_base = {m: d[(m, gate_pair)]["mean"] for m in markets}
    no_worse = all(v <= WORSE_TOL for v in vs_base.values())
    bench = {m: {**cuts[(m, gate_pair, "bench_overprojection")]} for m in KEY_MARKETS}
    for v in bench.values():
        v["ok"] = bool(v["cut"] >= BENCH_CUT)               # nan (nothing to cut) fails
    passed = any(v["ok"] for v in nll.values()) and no_worse and all(v["ok"] for v in bench.values())
    return {"candidate": SI, "reference": BASE, "adopted_model": SI if passed else BASE, "gate_passed": bool(passed),
            "nll": nll, "no_market_worse_than_tol": bool(no_worse), "delta_vs_plus2_all_markets": vs_base,
            "bench": bench,
            "thresholds": {"worse_tol": WORSE_TOL, "min_gain": MIN_GAIN, "min_seasons": MIN_SEASONS, "bench_cut": BENCH_CUT}}


def calibration_rows(data, model: str) -> tuple[pd.DataFrame, dict, dict, dict]:
    """The calibration rule on `model`'s walk-forward rows -> (eval rows, calibration params, _meta, per-market checks)."""
    rows = pd.concat([per[model] for per in data.values()], ignore_index=True)
    params, meta, checks = calibrate.fit_by_rule(rows, model, alpha_method(registry()[model]))
    out = []
    for market, c in checks.items():
        for r in c["per_season"]:
            out.append({"section": "calib_check", "market": market, "subject": model,
                        "metric": f"logloss_gain_{r['season']}", "value": r["gain"], "n": r["n"]})
        out.append({"section": "calib_check", "market": market, "subject": model, "metric": "seasons_improved",
                    "value": c["seasons_improved"], "n": c["of"]})
        out.append({"section": "calib_check", "market": market, "subject": model, "metric": "pooled_gain",
                    "value": c["pooled_gain"], "n": sum(r["n"] for r in c["per_season"])})
        out.append({"section": "calib_check", "market": market, "subject": model, "metric": "apply",
                    "value": int(c["apply"]), "n": c["of"]})
    return pd.DataFrame(out), params, meta, checks


def main():
    ap = C.parser(__doc__)
    ap.add_argument("--reps", type=int, default=2000, help="bootstrap reps for the delta_nll and role_cut CIs")
    ap.add_argument("--aux-reps", type=int, default=500, help="bootstrap reps for the slope and residual CIs")
    ap.add_argument("--rows", default=str(V3 / "backtest_rows.parquet"))
    args = ap.parse_args()
    reps, aux_reps = (200, 50) if args.quick else (args.reps, args.aux_reps)
    suffix = "_quick" if args.quick else ""

    data = load(args.rows)
    table, stash = evaluate(data, reps, aux_reps)
    gate = decide(stash, sorted(data))
    cal_rows, params, meta, checks = calibration_rows(data, gate["adopted_model"])
    table = pd.concat([table, cal_rows], ignore_index=True)
    gate["calibration"] = {"model": gate["adopted_model"], "apply_to": meta["apply_to"],
                           "per_market": {m: {k: c[k] for k in ("seasons_improved", "of", "pooled_gain", "apply")}
                                          for m, c in checks.items()}}
    gate["reps"] = {"reps": reps, "aux_reps": aux_reps}
    if not args.quick:                                       # a smoke test must not rewrite the calibration file
        V3.mkdir(parents=True, exist_ok=True)
        calibrate.save(params, V3 / "calibration.json", meta=meta)

    V3.mkdir(parents=True, exist_ok=True)
    table.to_csv(V3 / f"eval{suffix}.csv", index=False)
    (V3 / f"gate{suffix}.json").write_text(json.dumps(gate, indent=1, default=float))
    show(table, gate, reps, aux_reps)


def show(table: pd.DataFrame, gate: dict, reps: int, aux_reps: int) -> None:
    pd.set_option("display.width", 250, "display.max_columns", 30)
    f = lambda d: d.round(4).to_string(index=False)
    sec = lambda name: table[table.section == name]
    d = sec("delta_nll")
    print(f"\n== delta nll, candidate - reference (negative = candidate better): mean per row, 95% CI from {reps} reps "
          f"resampling games (game) and {reps} reps resampling player-seasons (player_season) ==")
    print(f(d[d.metric == "mean"][["market", "subject", "value", "lo_game", "hi_game", "lo_player_season", "hi_player_season"]]))
    cl = sec("clusters").pivot_table(index="market", columns="subject", values="value").astype(int)
    print("clusters resampled per market:\n" + cl.to_string())
    print("\n== delta nll by season ==")
    print(f(d[d.metric.str.startswith("season_")].pivot_table(index=["market", "subject"], columns="metric", values="value").reset_index()))
    print("\n== seasons improved (of 6; negative delta = improved) ==")
    print(f(d[d.metric == "seasons_improved"][["market", "subject", "value"]]))
    print(f"\n== calibration slope of p_over (1 = calibrated); 95% CI from {aux_reps} reps resampling games ==")
    print(f(sec("slope")[["market", "subject", "value", "lo_game", "hi_game"]]))
    print("\n== q10-q90 coverage (observed vs the model's own nominal; no CI) ==")
    print(f(sec("coverage").pivot_table(index=["market", "subject"], columns="metric", values="value").reset_index()))
    print(f"\n== playoff residual (actual - mu) by previous-game starter; 95% CI from {aux_reps} reps resampling games ==")
    r = sec("resid")
    print(f(r[r.subject.str.startswith("playoffs")][["market", "subject", "value", "lo_game", "hi_game", "n"]]))
    print(f"\n== playoff bench over-projection / starter under-projection cut vs the reference; 95% CI from {reps} reps "
          f"resampling games and {reps} reps resampling player-seasons ==")
    rc = sec("role_cut")
    print("(NaN, dropped here but kept in eval.csv, = the reference has no bias of that sign to cut; the starter cut "
          "interval is wide when the reference bias is small)")
    print(f(rc[rc.metric.str.endswith("_cut")].dropna(subset=["value"])[
        ["market", "subject", "metric", "value", "lo_game", "hi_game", "lo_player_season", "hi_player_season", "n"]]))
    print(f(rc[rc.metric.str.endswith("_bias") & (rc.subject == label(PAIRS[0]))][["market", "metric", "value", "n"]]))
    print(f"\n== walk-forward calibration check of {gate['calibration']['model']} (fit on seasons < s, score s) ==")
    cc = sec("calib_check")
    print(f(cc[["market", "metric", "value", "n"]]))
    print("\n== gate: plus2si vs production plus2 ==")
    print(json.dumps({k: gate[k] for k in ("gate_passed", "adopted_model", "no_market_worse_than_tol")}, indent=1))
    print("points/pra nll:", json.dumps(gate["nll"], default=float))
    print("bench cut:", json.dumps(gate["bench"], default=float))
    print("calibration apply_to:", gate["calibration"]["apply_to"])


if __name__ == "__main__":
    main()
