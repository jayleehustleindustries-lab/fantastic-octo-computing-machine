import numpy as np
import pandas as pd
import pytest

from oklahoma.minutes import FEATS, MinutesModel, design


def synthetic_minutes(seasons, n=1200, seed=0, drift_sd=0.4):
    """Minutes with starter-dependent spread, heavy tails and a per-season level shift, so the
    band has to be wider for bench players and the held-out season never matches training exactly."""
    rng = np.random.default_rng(seed)
    frames = []
    for s in seasons:
        ewm = rng.uniform(5, 35, n)
        starter_prev = rng.random(n) < np.clip((ewm - 12) / 25, 0.02, 0.95)
        base = 0.85 * ewm + 4.0 * starter_prev + rng.normal(0, drift_sd)
        sd = np.where(starter_prev, 3.0, 6.0)
        d = pd.DataFrame({
            "season": s, "min_ewm": ewm, "min_l5": ewm + rng.normal(0, 2, n), "starter_prev": starter_prev,
            "rest_days": rng.integers(1, 6, n).astype(float), "out_minutes": rng.exponential(5, n),
            "is_home": rng.random(n) < 0.5, "playoffs": rng.random(n) < 0.07,
            "team_games_last7": rng.integers(1, 4, n), "days_since_last": rng.integers(1, 10, n).astype(float),
            "returning": rng.random(n) < 0.05, "career_games": rng.integers(5, 200, n),
            "rookie": rng.random(n) < 0.1, "pace_ratio": rng.normal(1, 0.03, n), "season_min_pg": ewm + rng.normal(0, 1, n),
            "athlete_position_abbreviation": rng.choice(["G", "F", "C", "G-F"], n),
        })
        d["minutes"] = np.clip(base + sd * rng.standard_t(5, n), 0, 48)
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


def fitted(max_iter=60, **kw):
    train = synthetic_minutes(range(2016, 2023), **kw)
    return MinutesModel(max_iter=max_iter).fit(train), train


def test_cqr_band_covers_80_percent_on_a_held_out_season():
    # Small training seasons + many boosting rounds overfit, so the raw p10-p90 band is too narrow
    # on a new season (~0.7 coverage). CQR must pull it back to the 80% target.
    m, _ = fitted(max_iter=150, n=250)
    test = synthetic_minutes([2023], n=4000, seed=99)

    def band_coverage():
        q = m.predict(test)
        return ((test["minutes"] >= q["min_p10"]) & (test["minutes"] <= q["min_p90"])).mean()

    cqr = band_coverage()
    shift, m.shift_ = m.shift_, 0.0
    raw = band_coverage()
    m.shift_ = shift
    assert raw < 0.75 and shift > 0, (raw, shift)       # without CQR the band is visibly too narrow
    assert 0.75 <= cqr <= 0.85, cqr


def test_predict_quantiles_are_sorted_and_within_game_length():
    m, _ = fitted()
    test = synthetic_minutes([2023], n=800, seed=5)
    test.loc[:20, "min_ewm"] = 60.0                 # out-of-range inputs must still give a legal band
    test.loc[21:40, "min_ewm"] = -20.0
    q = m.predict(test)
    assert list(q.columns) == ["min_p10", "min_p50", "min_p90"] and q.index.equals(test.index)
    assert np.isfinite(q.to_numpy()).all()
    assert (q["min_p10"] <= q["min_p50"]).all() and (q["min_p50"] <= q["min_p90"]).all()
    assert q.to_numpy().min() >= 0.0 and q.to_numpy().max() <= 48.0


def test_conformal_shift_is_applied_to_both_edges():
    m, _ = fitted()
    test = synthetic_minutes([2023], n=800, seed=5)
    with_shift = m.predict(test)
    shift = m.shift_
    m.shift_ = 0.0
    raw = m.predict(test)
    m.shift_ = shift
    ok = (raw["min_p10"] - shift > 0) & (raw["min_p90"] + shift < 48) & (raw["min_p10"] <= raw["min_p90"])
    ok &= (raw["min_p10"] - shift <= raw["min_p50"]) & (raw["min_p50"] <= raw["min_p90"] + shift)
    assert ok.mean() > 0.9 and shift != 0.0
    np.testing.assert_allclose((with_shift["min_p10"] - raw["min_p10"])[ok], -shift, atol=1e-9)
    np.testing.assert_allclose((with_shift["min_p90"] - raw["min_p90"])[ok], shift, atol=1e-9)


def test_game_day_starter_flag_is_never_read():
    train = synthetic_minutes(range(2016, 2021), n=600)
    assert "starter" not in FEATS and "starter" not in design(train).columns
    m = MinutesModel(max_iter=30).fit(train)            # trains with no `starter` column at all
    test = synthetic_minutes([2021], n=300, seed=2)
    a = m.predict(test)
    b = m.predict(test.assign(starter=~test["starter_prev"], minutes=test["minutes"] + 25))   # tampered game-day columns
    pd.testing.assert_frame_equal(a, b)
    with pytest.raises(KeyError, match="starter_prev"):
        m.predict(test.drop(columns="starter_prev"))


def test_seed_option_controls_the_fit_and_random_state_is_an_alias():
    # Early stopping holds out a random validation split once a fit has more than 10k rows, so the seed matters there.
    train = synthetic_minutes(range(2018, 2021), n=3500)               # 10,500 rows
    test = synthetic_minutes([2021], n=400, seed=3)
    assert MinutesModel().seed == 0 and MinutesModel(seed=3).seed == 3 and MinutesModel(random_state=4).seed == 4
    a0 = MinutesModel(max_iter=40, seed=0).fit(train).predict(test)
    a0_again = MinutesModel(max_iter=40, seed=0).fit(train).predict(test)
    a1 = MinutesModel(max_iter=40, random_state=1).fit(train).predict(test)       # alias for seed=1
    pd.testing.assert_frame_equal(a0, a0_again)                          # same seed: identical
    assert not np.allclose(a0["min_p50"], a1["min_p50"])                  # different seed: a different model


def test_j06_averages_over_seeds_and_gates_the_average():
    from jobs import j06_minutes as J

    def table(gains, cov):
        return pd.DataFrame({"season": range(2021, 2027), "n": 100, "n_bench": 40, "mae_gbm": 4.0, "mae_baseline": 4.0 + np.array(gains),
                             "mae_gain": gains, "coverage_10_90": cov})

    def pooled(gain, cov):
        return {"mae_gbm": 4.0, "mae_baseline": 4.0 + gain, "mae_gain": gain, "coverage_10_90": cov, "n": 600.0}

    # Two seeds near the 0.30 line: each passes or fails the 5-of-6 rule on its own, the average decides.
    s0 = table([0.33, 0.31, 0.32, 0.34, 0.29, 0.32], [0.80] * 6)           # 5 seasons >= 0.30: passes
    s1 = table([0.33, 0.31, 0.32, 0.34, 0.29, 0.29], [0.80] * 6)           # 4 seasons >= 0.30: fails
    out, pool, per_seed, g = J.combine([(s0, pooled(0.32, 0.80)), (s1, pooled(0.31, 0.81))])
    assert per_seed["passed"].tolist() == [True, False] and per_seed["seed"].tolist() == [0, 1]
    assert per_seed["gain_2026"].tolist() == [0.32, 0.29] and per_seed["gain_2025"].tolist() == [0.29, 0.29]   # per-season gains by seed
    assert out["mae_gain"].round(4).tolist() == [0.33, 0.31, 0.32, 0.34, 0.29, 0.305]
    assert out["n"].tolist() == [100] * 6 and out["n_seeds"].tolist() == [2] * 6 and out["n"].dtype.kind == "i"
    assert pool["mae_gain"] == pytest.approx(0.315) and pool["coverage_10_90"] == pytest.approx(0.805)
    assert g["seasons_with_gain_ge_0.30"] == 5 and g["passed"] and g["n_seeds"] == 2 and g["seeds_passing"] == 1
    assert g["pooled_mae_gain_by_seed"] == [0.32, 0.31]
    # The average can also fail where every seed passes: each misses a different season by a hair, the average misses two.
    a = table([0.33, 0.29, 0.30, 0.34, 0.32, 0.32], [0.80] * 6)
    b = table([0.33, 0.30, 0.29, 0.34, 0.32, 0.32], [0.80] * 6)
    out, pool, per_seed, g = J.combine([(a, pooled(0.32, 0.80)), (b, pooled(0.32, 0.80))])
    assert per_seed["passed"].tolist() == [True, True]
    assert g["seasons_with_gain_ge_0.30"] == 4 and not g["gain_ok"] and not g["passed"] and g["seeds_passing"] == 2
