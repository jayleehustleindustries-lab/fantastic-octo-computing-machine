"""jobs/j08_v3_eval.py: bootstraps, the adoption gate for plus2si over plus2, and the report's own accounting.

Synthetic backtest rows with fixed seeds; no network, no real data.
"""
import copy

import numpy as np
import pandas as pd
import pytest

from jobs import j08_v3_eval as J

MARKETS = ("points", "rebounds", "assists", "pra")
PAIR = J.PAIRS[0]                                   # (plus2si, plus2): the gate


def fake_rows(markets=MARKETS, gain=0.004, fixes_bias=True, seed=0):
    """Rows for plus2, plus2s and plus2si. plus2si's nll is `gain` lower than plus2's; in the playoffs plus2
    over-projects the bench by 0.9 and under-projects starters by 0.8, which plus2s/plus2si remove (or keep)."""
    rng = np.random.default_rng(seed)
    frames = []
    for market in markets:
        for season in range(2021, 2027):
            g, a = np.meshgrid(np.arange(60), np.arange(25), indexing="ij")
            game, ath = g.ravel(), a.ravel()
            n = len(game)
            playoffs, starter = game >= 50, ath < 10
            base = 2.5 + rng.normal(0, 0.3, n)
            actual = rng.poisson(8, n).astype(float)
            bias = np.where(playoffs & ~starter, 0.9, np.where(playoffs & starter, -0.8, 0.0))
            for model, mu, nll in (
                (J.BASE, 8.0 + bias, base),
                (J.STARTER, 8.0 + (bias if not fixes_bias else 0.0), base - gain * 0.5 + rng.normal(0, 0.003, n)),
                (J.SI, 8.0 + (bias if not fixes_bias else 0.0), base - gain + rng.normal(0, 0.003, n)),
            ):
                p = np.clip(0.5 + rng.normal(0, 0.15, n), 0.05, 0.95)
                frames.append(pd.DataFrame({
                    "market": market, "model": model, "season": season, "game_id": season * 100 + game,
                    "athlete_id": ath, "playoffs": playoffs, "starter_prev": starter, "actual": actual, "mu": mu,
                    "alpha": 0.1, "nll": nll, "p_over": p, "went_over": (rng.random(n) < p).astype(int)}))
    return pd.concat(frames, ignore_index=True)


def as_data(rows):
    out = {}
    for market, d in rows.groupby("market"):
        out[market] = {m: g.sort_values(J.KEY).reset_index(drop=True) for m, g in d.groupby("model")}
    return out


def test_evaluate_reports_the_gain_with_both_clusterings_and_states_its_reps():
    table, stash = J.evaluate(as_data(fake_rows(("points", "pra"))), reps=100, aux_reps=30)
    d = table[(table.section == "delta_nll") & (table.metric == "mean") & (table.subject == J.label(PAIR))]
    assert set(d.market) == {"points", "pra"}
    assert (d.value.between(-0.006, -0.002)).all()                                  # built-in gain 0.004
    assert ((d.lo_game < d.value) & (d.value < d.hi_game) & (d.hi_game < 0)).all()
    assert ((d.lo_player_season < d.value) & (d.value < d.hi_player_season) & (d.hi_player_season < 0)).all()
    assert (d.reps_game == 100).all() and (d.reps_player_season == 100).all()
    clusters = table[table.section == "clusters"].set_index(["market", "subject"])["value"]
    assert clusters["points", "games"] == 360 and clusters["points", "player-seasons"] == 150   # 60 games x 6, 25 players x 6
    si = table[(table.section == "delta_nll") & (table.metric == "seasons_improved") & (table.subject == J.label(PAIR))]
    assert (si.value == 6).all()
    by_season = table[(table.section == "delta_nll") & table.metric.str.startswith("season_") & (table.subject == J.label(PAIR))]
    assert len(by_season) == 12 and (by_season.value < 0).all()
    # Every section says how many reps its interval used: headline CIs 100, slope and residual CIs 30, none for coverage.
    slope = table[table.section == "slope"]
    assert set(slope.subject) == set(J.MODELS) and (slope.reps_game == 30).all()
    resid = table[(table.section == "resid") & table.lo_game.notna()]
    assert len(resid) > 0 and (resid.reps_game == 30).all()
    cut = table[(table.section == "role_cut") & table.metric.str.endswith("_cut") & table.value.notna()]
    assert len(cut) > 0 and (cut.reps_game == 100).all() and (cut.reps_player_season == 100).all()
    assert table[table.section == "coverage"].reps_game.isna().all()


def test_playoff_role_cut_measures_the_share_of_bias_removed():
    table, stash = J.evaluate(as_data(fake_rows(("points", "pra"), fixes_bias=True)), reps=100, aux_reps=30)
    bench = stash["cut"][("points", PAIR, "bench_overprojection")]
    assert bench["ref_bias"] < -0.7 and abs(bench["cand_bias"]) < 0.15 and bench["cut"] > 0.8 and bench["n"] > 0
    star = stash["cut"][("points", PAIR, "starter_underprojection")]
    assert star["ref_bias"] > 0.6 and star["cut"] > 0.8
    assert bench["ci_game"][0] < bench["cut"] <= 1 and bench["ci_player_season"][0] < bench["cut"] <= 1
    # A reference that is not biased in that direction has nothing to cut: NaN, not a made-up share.
    vs_s = stash["cut"][("points", (J.SI, J.STARTER), "bench_overprojection")]
    assert np.isnan(vs_s["cut"]) or abs(vs_s["ref_bias"]) < 0.15
    assert J.bias_cut(-1.0, 0.25) == pytest.approx(0.75) and J.bias_cut(-1.0, 1.5) == pytest.approx(-0.5)


def test_decide_passes_a_clear_win_and_each_condition_can_fail_it():
    data = as_data(fake_rows())
    _, stash = J.evaluate(data, reps=100, aux_reps=30)
    gate = J.decide(stash, sorted(data))
    assert gate["gate_passed"] and gate["adopted_model"] == J.SI and gate["no_market_worse_than_tol"]
    assert all(v["ok"] for v in gate["nll"].values()) and all(v["ok"] for v in gate["bench"].values())

    def failing(edit):
        s = copy.deepcopy(stash)
        edit(s)
        g = J.decide(s, sorted(data))
        assert not g["gate_passed"] and g["adopted_model"] == J.BASE
        return g

    d = lambda s, m: s["delta"][(m, PAIR)]
    # gain too small in both key markets
    def small(s):
        for m in J.KEY_MARKETS:
            d(s, m)["mean"] = -0.0004
    failing(small)
    # one clustering's interval touches 0 (the other excludes it): both are required
    def one_ci(s):
        for m in J.KEY_MARKETS:
            d(s, m)["ps"] = (d(s, m)["ps"][0], 0.0001)
    assert not failing(one_ci)["nll"]["points"]["ok"]
    def other_ci(s):
        for m in J.KEY_MARKETS:
            d(s, m)["game"] = (d(s, m)["game"][0], 0.0001)
    failing(other_ci)
    # fewer than 5 of 6 seasons improved
    def seasons(s):
        for m in J.KEY_MARKETS:
            d(s, m)["improved"] = 4
    failing(seasons)
    # any market, not only points/PRA, worse than plus2 by more than 0.0003
    def worse(s):
        d(s, "assists")["mean"] = 0.0004
    assert not failing(worse)["no_market_worse_than_tol"]
    # bench over-projection cut below 30% in one of the two key markets
    def bench(s):
        s["cut"][("pra", PAIR, "bench_overprojection")]["cut"] = 0.29
    assert not failing(bench)["bench"]["pra"]["ok"]
    def nothing_to_cut(s):
        s["cut"][("points", PAIR, "bench_overprojection")]["cut"] = float("nan")
    failing(nothing_to_cut)
    # passing needs only ONE of points / PRA to clear the nll test
    ok = copy.deepcopy(stash)
    d(ok, "points")["mean"] = -0.0001
    g = J.decide(ok, sorted(data))
    assert g["gate_passed"] and not g["nll"]["points"]["ok"] and g["nll"]["pra"]["ok"]


def test_a_gain_that_is_not_there_fails_the_gate_end_to_end():
    data = as_data(fake_rows(gain=0.0))
    _, stash = J.evaluate(data, reps=100, aux_reps=30)
    gate = J.decide(stash, sorted(data))
    assert not gate["gate_passed"] and gate["adopted_model"] == J.BASE


def test_calibration_rows_run_the_rule_on_the_adopted_models_rows():
    data = as_data(fake_rows(("points", "pra")))
    table, params, meta, checks = J.calibration_rows(data, J.SI)
    assert set(params) == {"points", "pra"} and meta["model"] == J.SI and meta["alpha_method"].startswith("in_sample")
    assert meta["fit_seasons"] == list(range(2021, 2027)) and set(meta["apply_to"]) <= {"points", "pra"}
    gains = table[(table.metric.str.startswith("logloss_gain_")) & (table.market == "points")]
    assert gains.metric.tolist() == [f"logloss_gain_{s}" for s in range(2022, 2027)]    # 5 held-out seasons
    assert set(table[table.metric == "apply"].value) <= {0, 1}


def test_load_keeps_only_the_compared_models_and_demands_all_three(tmp_path):
    rows = fake_rows(("points", "pra"))
    extra = rows[rows.model == J.BASE].assign(model="season_avg")
    path = tmp_path / "rows.parquet"
    pd.concat([rows, extra]).to_parquet(path)
    data = J.load(path)
    assert set(data) == {"points", "pra"} and set(data["points"]) == set(J.MODELS)
    pd.concat([rows[rows.model != J.SI]]).to_parquet(path)
    with pytest.raises(SystemExit, match="context_glm_plus2si"):
        J.load(path)
