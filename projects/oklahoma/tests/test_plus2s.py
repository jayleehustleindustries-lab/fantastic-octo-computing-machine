"""Out-of-sample dispersion (plus2o), the playoff starter terms (plus2s, plus2si) and the calibration `_meta` block.

Synthetic frames with fixed seeds; no network, no real data.
"""
import json
import sys

import numpy as np
import pandas as pd
import pytest

from oklahoma import backtest, calibrate, ingest
from oklahoma.models import (PRODUCTION_MODEL, ContextGLMPlus, ContextGLMPlus2, ContextGLMPlus2O, ContextGLMPlus2S,
                             ContextGLMPlus2SI, Model, alpha_method, registry)


def design_frame(seasons, n=2500, seed=0, alphas=None, playoff_shift=(0.75, 1.2), p_playoff=0.1):
    """Points rows carrying exactly the columns the plus2 design reads.

    Per-season NB dispersion comes from `alphas` (0 = Poisson). In the playoffs bench players' means are
    scaled by playoff_shift[0] and starters' (by previous-game flag) by playoff_shift[1]."""
    rng = np.random.default_rng(seed)
    alphas = alphas or {}
    frames = []
    for s in seasons:
        mins = rng.uniform(8, 36, n)
        starter_prev = rng.random(n) < np.clip((mins - 8) / 36 + 0.1, 0, 0.95)
        rate = rng.uniform(0.2, 0.6, n)
        playoffs = rng.random(n) < p_playoff
        mu = rate * mins * np.where(playoffs, np.where(starter_prev, playoff_shift[1], playoff_shift[0]), 1.0)
        a = alphas.get(s, 0.0)
        y = rng.poisson(mu) if a == 0 else rng.negative_binomial(1 / a, (1 / a) / (1 / a + mu))
        frames.append(pd.DataFrame({
            "season": s, "points": y.astype(float), "minutes": mins,
            "points_pm_ewm": rate, "season_points_pm": rate, "career_points_pm": rate,
            "min_ewm": mins, "min_l5": mins, "opp_points_ratio": 1.0, "is_home": rng.random(n) < 0.5,
            "playoffs": playoffs, "rookie": False, "rest_days": 2.0, "career_games": 50,
            "out_minutes": 0.0, "out_points": 0.0, "team_games_last7": 2, "returning": False,
            "days_since_last": 2.0, "points_l5": rate * mins, "points_ewm": rate * mins,
            "usage_pm_ewm": 0.5, "pace_ratio": 1.0, "starter_prev": starter_prev,
        }))
    return pd.concat(frames, ignore_index=True)


# ---------- plus2o: out-of-sample dispersion ----------

def test_registry_has_both_variants_and_existing_classes_keep_in_sample_alpha():
    reg = registry()
    assert reg["context_glm_plus2o"] is ContextGLMPlus2O and reg["context_glm_plus2s"] is ContextGLMPlus2S
    assert Model.oos_alpha is False and ContextGLMPlus2.oos_alpha is False
    assert ContextGLMPlus2O.oos_alpha is True and ContextGLMPlus2S.oos_alpha is True
    train = design_frame([2018, 2019, 2020], n=800)
    assert ContextGLMPlus2("points").fit(train).alpha_source_ == "in_sample"


def test_oos_alpha_path_runs_and_tracks_the_last_training_season():
    # Poisson seasons followed by an overdispersed one: dispersion fit on the last season sees alpha ~0.35,
    # the in-sample pooled value averages it away.
    train = design_frame([2017, 2018, 2019, 2020], n=2500, alphas={2020: 0.35})
    plain = ContextGLMPlus2("points").fit(train)
    oos = ContextGLMPlus2O("points").fit(train)
    assert oos.alpha_source_ == "out_of_sample"
    assert np.isfinite(oos.alpha_bins_).all() and (oos.alpha_bins_ >= 0).all() and len(oos.alpha_edges_) == 4
    assert 0.25 < oos.alpha_ < 0.45
    assert oos.alpha_ > 1.5 * plain.alpha_
    # Same mean model: only the dispersion differs, and the final mean is the full-window refit.
    test = design_frame([2021], n=500, seed=9)
    np.testing.assert_allclose(oos.predict_mean(test), plain.predict_mean(test))
    a = oos.alpha_for(oos.predict_mean(test))
    assert a.shape == (500,) and np.isfinite(a).all()


def test_oos_alpha_inner_fit_never_sees_the_held_out_season(monkeypatch):
    seen = []
    orig = ContextGLMPlus2O._fit_mean

    def spy(self, train):
        seen.append(train["season"].max())
        return orig(self, train)

    monkeypatch.setattr(ContextGLMPlus2O, "_fit_mean", spy)
    ContextGLMPlus2O("points").fit(design_frame([2018, 2019, 2020], n=600))
    # full-window mean fit, then the inner fit on the seasons before the last one
    assert seen == [2020, 2019]


def test_oos_alpha_falls_back_to_in_sample_with_a_single_season():
    train = design_frame([2020], n=1500)
    m = ContextGLMPlus2O("points").fit(train)
    assert m.alpha_source_ == "in_sample"
    np.testing.assert_allclose(m.alpha_bins_, ContextGLMPlus2("points").fit(train).alpha_bins_)


# ---------- plus2s: playoff role terms ----------

def test_plus2s_design_has_two_more_columns_and_keeps_plus2_indices():
    df = design_frame([2020], n=300)
    p2, p2o, p2s = (c("points").fit(design_frame([2019, 2020], n=300)) for c in (ContextGLMPlus2, ContextGLMPlus2O, ContextGLMPlus2S))
    X2, X2o, X2s = p2._design(df), p2o._design(df), p2s._design(df)
    assert X2s.shape[1] == X2.shape[1] + 2 and X2o.shape == X2.shape      # jobs/j01 indexes plus2's columns
    np.testing.assert_allclose(X2s[:, :X2.shape[1]], X2)
    sp, po = df["starter_prev"].to_numpy(float), df["playoffs"].to_numpy(float)
    np.testing.assert_allclose(X2s[:, -2], sp)
    np.testing.assert_allclose(X2s[:, -1], sp * po)


def test_plus2s_removes_the_playoff_bench_and_starter_bias_that_plus2o_keeps():
    train = design_frame([2016, 2017, 2018, 2019], n=3000, seed=1)
    test = design_frame([2020], n=3000, seed=2)
    po = test["playoffs"].to_numpy(bool)
    bench, starter = po & ~test["starter_prev"].to_numpy(bool), po & test["starter_prev"].to_numpy(bool)
    resid = {}
    for cls in (ContextGLMPlus2O, ContextGLMPlus2S):
        mu = cls("points").fit(train).predict_mean(test)
        r = test["points"].to_numpy() - mu
        resid[cls.__name__] = (r[bench].mean(), r[starter].mean())
    o_bench, o_start = resid["ContextGLMPlus2O"]
    s_bench, s_start = resid["ContextGLMPlus2S"]
    assert o_bench < -0.5 and o_start > 0.5            # the pooled playoff term cannot fit both roles
    assert abs(s_bench) < 0.3 * abs(o_bench) and abs(s_start) < 0.3 * abs(o_start)


# ---------- plus2si: plus2s's design with plus2's in-sample dispersion ----------

def test_plus2si_is_plus2s_design_with_in_sample_alpha_and_is_registered():
    reg = registry()
    assert reg["context_glm_plus2si"] is ContextGLMPlus2SI and PRODUCTION_MODEL == "context_glm_plus2si"
    assert ContextGLMPlus2SI.oos_alpha is False and ContextGLMPlus2SI.has_starter_terms is True
    assert issubclass(ContextGLMPlus2SI, ContextGLMPlus2S)               # the design code is reused, not copied
    train, test = design_frame([2017, 2018, 2019, 2020], n=700), design_frame([2021], n=300, seed=9)
    p2, p2s, p2si = (c("points").fit(train) for c in (ContextGLMPlus2, ContextGLMPlus2S, ContextGLMPlus2SI))
    X2, Xs, Xsi = p2._design(test), p2s._design(test), p2si._design(test)
    assert Xsi.shape[1] == X2.shape[1] + 2                               # plus2's columns first (jobs/j01 indexes them) ...
    np.testing.assert_allclose(Xsi[:, :X2.shape[1]], X2)
    np.testing.assert_allclose(Xsi, Xs)                                  # ... then the same two starter columns as plus2s
    sp, po = test["starter_prev"].to_numpy(float), test["playoffs"].to_numpy(float)
    np.testing.assert_allclose(Xsi[:, -2:], np.column_stack([sp, sp * po]))
    # Same mean model as plus2s (only the dispersion method differs), and plus2's in-sample dispersion path.
    np.testing.assert_allclose(p2si.predict_mean(test), p2s.predict_mean(test))
    assert p2si.alpha_source_ == "in_sample" and p2s.alpha_source_ == "out_of_sample" and p2.alpha_source_ == "in_sample"
    assert alpha_method(ContextGLMPlus2SI).startswith("in_sample") and alpha_method(ContextGLMPlus2O).startswith("out_of_sample")


def test_has_starter_terms_matches_what_the_design_actually_reads():
    # The flag decides whether compare.py may add its playoff role shift, so it must not drift from the design:
    # flipping starter_prev changes a model's mean exactly when the flag says the design reads it.
    train, test = design_frame([2017, 2018, 2019, 2020], n=500), design_frame([2021], n=400, seed=9)
    flipped = test.assign(starter_prev=~test["starter_prev"])
    for cls in (c for c in registry().values() if issubclass(c, ContextGLMPlus)):
        m = cls("points").fit(train)
        reads = not np.allclose(m.predict_mean(test), m.predict_mean(flipped))
        assert reads == cls.has_starter_terms, cls.__name__
    assert {c.__name__ for c in registry().values() if c.has_starter_terms} == {"ContextGLMPlus2S", "ContextGLMPlus2SI"}


# ---------- backtest CLI keeps production files out of the way ----------

def test_backtest_out_dir_and_production_model(tmp_path, monkeypatch):
    from test_pipeline import synthetic_games
    games_path = tmp_path / "games.parquet"
    synthetic_games().to_parquet(games_path)
    monkeypatch.setattr(ingest, "GAMES_PATH", games_path)
    prod = {p: p.read_bytes() for p in (calibrate.PATH, backtest.REPORTS / "backtest_rows.parquet") if p.exists()}
    out = tmp_path / "v3"
    argv = ["backtest", "--test-seasons", "2022-2022", "--min-prior-games", "3", "--out-dir", str(out),
            "--models", "season_avg,context_glm_plus2s", "--production-model", "context_glm_plus2s"]
    monkeypatch.setattr(sys, "argv", argv)
    backtest.main()
    rows = pd.read_parquet(out / "backtest_rows.parquet")
    assert set(rows["model"]) == {"season_avg", "context_glm_plus2s"} and "starter_prev" in rows
    cal = json.loads((out / "calibration.json").read_text())
    assert set(cal) == {"points", "rebounds", "assists", "pra", "_meta"} and set(calibrate.load(out / "calibration.json")) == set(cal) - {"_meta"}
    assert cal["_meta"]["model"] == "context_glm_plus2s" and cal["_meta"]["alpha_method"].startswith("out_of_sample")
    assert cal["_meta"]["fit_seasons"] == [2022] and cal["_meta"]["apply_to"] == []     # one test season: nothing held out
    assert (out / "summary.txt").exists() and (out / "summary.json").exists()
    assert {p: p.read_bytes() for p in prod} == prod                      # production files untouched
    monkeypatch.setattr(sys, "argv", argv[:-1] + ["no_such_model"])
    with pytest.raises(SystemExit):
        backtest.main()


def test_backtest_defaults_to_the_production_model_and_calibrates_it_by_rule(tmp_path, monkeypatch):
    from test_pipeline import synthetic_games
    games_path = tmp_path / "games.parquet"
    synthetic_games().to_parquet(games_path)
    monkeypatch.setattr(ingest, "GAMES_PATH", games_path)
    assert backtest.DEFAULT_MODELS[-1] == PRODUCTION_MODEL and set(backtest.DEFAULT_MODELS) <= set(registry())
    assert "context_glm_plus2o" not in backtest.DEFAULT_MODELS and "context_glm_plus2s" not in backtest.DEFAULT_MODELS
    out = tmp_path / "default"
    monkeypatch.setattr(sys, "argv", ["backtest", "--test-seasons", "2021-2022", "--min-prior-games", "3", "--out-dir", str(out)])
    backtest.main()
    rows = pd.read_parquet(out / "backtest_rows.parquet")
    assert set(rows["model"]) == set(backtest.DEFAULT_MODELS)
    meta = calibrate.load_meta(out / "calibration.json")
    assert meta["model"] == PRODUCTION_MODEL and meta["alpha_method"].startswith("in_sample")
    assert meta["fit_seasons"] == [2021, 2022] and set(meta["n"]) == {"points", "rebounds", "assists", "pra"}
    assert set(meta["apply_to"]) <= set(meta["n"])                          # the rule's verdict, whatever it is on noise


# ---------- calibrate: "_meta" ----------

def test_calibrate_load_ignores_meta_and_roundtrips_it(tmp_path):
    path = tmp_path / "calibration.json"
    meta = {"model": "context_glm_plus2s", "alpha_method": "out_of_sample", "fit_seasons": [2021, 2022],
            "n": {"points": 10}, "apply_to": ["points"]}
    calibrate.save({"points": (0.1, 0.8), "pra": (0.0, 0.9)}, path, meta=meta)
    raw = json.loads(path.read_text())
    assert raw["_meta"] == meta and raw["points"] == {"a": 0.1, "b": 0.8}     # same format plus _meta
    params = calibrate.load(path)
    assert params == {"points": (0.1, 0.8), "pra": (0.0, 0.9)}               # no "_meta" market, no crash
    assert calibrate.load_meta(path) == meta
    assert calibrate.calibrate(0.73, "points", params) < 0.73
    assert calibrate.calibrate(0.73, "rebounds", params) == 0.73
    calibrate.save({"points": (0.1, 0.8)}, path)                              # without meta: old format, nothing extra
    assert "_meta" not in json.loads(path.read_text()) and calibrate.load_meta(path) == {}
    assert calibrate.load_meta(tmp_path / "missing.json") == {}
