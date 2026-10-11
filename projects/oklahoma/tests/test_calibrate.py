"""calibrate.py: the file's own market list (_meta.apply_to) and the walk-forward keep-or-drop rule.

Synthetic probabilities with fixed seeds; no network, no real data.
"""
import json

import numpy as np
import pandas as pd
import pytest

from oklahoma import benter, calibrate


def write_cal(path, markets=("points", "pra", "rebounds"), apply_to=None, ab=(0.0, 0.8)):
    meta = None if apply_to is None else {"model": "m", "alpha_method": "x", "fit_seasons": [2021], "n": {}, "apply_to": apply_to}
    calibrate.save({m: ab for m in markets}, path, meta=meta)


def test_calibrate_honors_the_files_apply_to_and_falls_back_to_the_constant(tmp_path, monkeypatch):
    path = tmp_path / "calibration.json"
    monkeypatch.setattr(calibrate, "PATH", path)                      # the production file, redirected
    # A file that says "points only": pra has parameters and is in the module's APPLY_TO, but the file wins.
    write_cal(path, apply_to=["points"])
    assert calibrate.effective_apply_to() == ("points",)
    assert calibrate.calibrate(0.73, "points") < 0.73
    assert calibrate.calibrate(0.73, "pra") == 0.73
    # The file can also add a market the constant leaves out.
    write_cal(path, apply_to=["rebounds"])
    assert "rebounds" not in calibrate.APPLY_TO
    assert calibrate.calibrate(0.73, "rebounds") < 0.73 and calibrate.calibrate(0.73, "points") == 0.73
    # An empty list means "calibrate nothing" (rule dropped every market), not "use the default".
    write_cal(path, apply_to=[])
    assert calibrate.effective_apply_to() == () and calibrate.calibrate(0.73, "points") == 0.73
    # No _meta (older files), or no file at all: the module constant is the fallback.
    write_cal(path, apply_to=None)
    assert calibrate.effective_apply_to() == calibrate.APPLY_TO
    assert calibrate.calibrate(0.73, "pra") < 0.73 and calibrate.calibrate(0.73, "rebounds") == 0.73
    path.unlink()
    assert calibrate.effective_apply_to() == calibrate.APPLY_TO and calibrate.calibrate(0.73, "points") == 0.73


def test_explicit_params_use_the_constant_unless_apply_to_is_passed():
    params = {"points": (0.0, 0.8), "rebounds": (0.0, 0.8)}
    assert calibrate.calibrate(0.73, "rebounds", params) == 0.73                       # constant: rebounds is out
    assert calibrate.calibrate(0.73, "rebounds", params, apply_to=("rebounds",)) < 0.73
    assert calibrate.calibrate(0.73, "points", params, apply_to=("rebounds",)) == 0.73


def test_projector_follows_the_files_market_list(tmp_path, monkeypatch):
    # project.py and compare.py both read the production file; the market list must travel with it.
    from oklahoma import compare as C
    from test_compare import hand_fits, hand_target, lines_of
    path = tmp_path / "calibration.json"
    monkeypatch.setattr(calibrate, "PATH", path)
    lines = lines_of(("Ann Starter", "points", 10.5, None), ("Ann Starter", "pra", 20.5, None),
                     ("Ann Starter", "rebounds", 5.5, None))

    def run(apply_to):
        write_cal(path, markets=("points", "pra", "rebounds"), apply_to=apply_to)
        return C.evaluate(lines, hand_target(), hand_fits(), playoffs=False)          # cal_params=None: the file

    only_points = run(["points"])
    assert [("UNCALIBRATED" in f.split()) for f in only_points["flags"]] == [False, True, True]
    both = run(["points", "pra"])
    assert [("UNCALIBRATED" in f.split()) for f in both["flags"]] == [False, False, True]
    # pra: calibrated under "both", raw under "only_points"; points identical either way.
    raw = lambda r: r.p_over / (r.p_over + r.p_under) * (1 - r.p_push)
    assert only_points.iloc[1].p_more_cal == pytest.approx(raw(only_points.iloc[1]))
    assert both.iloc[1].p_more_cal != pytest.approx(raw(both.iloc[1]), abs=1e-4)
    assert only_points.iloc[0].p_more_cal == pytest.approx(both.iloc[0].p_more_cal)


def overconfident_rows(n=4000, seasons=range(2021, 2027), slope=0.6, seed=0):
    """p_over from a model that over-states the true log-odds by 1/slope; outcomes drawn from the truth."""
    rng = np.random.default_rng(seed)
    out = []
    for s in seasons:
        true_p = rng.uniform(0.15, 0.85, n)
        out.append(pd.DataFrame({
            "season": s, "p_over": benter.sigmoid(benter.logit(true_p) / slope),
            "went_over": (rng.random(n) < true_p).astype(int)}))
    return pd.concat(out, ignore_index=True)


def test_rule_keeps_an_overconfident_market_and_drops_a_calibrated_one():
    bad, good = overconfident_rows(slope=0.6), overconfident_rows(slope=1.0, seed=1)
    keep = calibrate.walk_forward_check(bad.p_over, bad.went_over, bad.season)
    assert keep["of"] == 5 and keep["seasons_improved"] == 5                   # held-out seasons 2022..2026
    assert [r["season"] for r in keep["per_season"]] == [2022, 2023, 2024, 2025, 2026]
    assert keep["pooled_gain"] >= calibrate.MIN_POOLED and keep["apply"]
    drop = calibrate.walk_forward_check(good.p_over, good.went_over, good.season)
    assert not drop["apply"] and drop["pooled_gain"] < calibrate.MIN_POOLED


def test_rule_needs_both_enough_seasons_and_enough_pooled_gain(monkeypatch):
    rows = overconfident_rows(slope=0.6)
    args = (rows.p_over, rows.went_over, rows.season)
    monkeypatch.setattr(calibrate, "MIN_POOLED", 10.0)                          # unreachable gain: seasons alone are not enough
    assert not calibrate.walk_forward_check(*args)["apply"]
    monkeypatch.setattr(calibrate, "MIN_POOLED", 0.001)
    monkeypatch.setattr(calibrate, "MIN_SEASONS", 6)                            # only 5 held-out seasons exist: pooled alone is not enough
    assert not calibrate.walk_forward_check(*args)["apply"]
    monkeypatch.setattr(calibrate, "MIN_SEASONS", 4)
    assert calibrate.walk_forward_check(*args)["apply"]


def test_rule_never_fits_a_season_on_itself():
    # Season 2022 has a different slope than 2021. A map fit with 2022 included would fit 2022 better than the
    # walk-forward map; the check must report the walk-forward (2021-only) number.
    rows = pd.concat([overconfident_rows(seasons=[2021], slope=1.0, seed=3),
                      overconfident_rows(seasons=[2022], slope=0.6, seed=4)], ignore_index=True)
    check = calibrate.walk_forward_check(rows.p_over, rows.went_over, rows.season)
    only = rows[rows.season == 2022]
    a, b = calibrate.fit(only.p_over, only.went_over)                          # the leaky version: fit on the scored season
    leaky = (calibrate.logloss(only.p_over, only.went_over) - calibrate.logloss(calibrate.apply(only.p_over, a, b), only.went_over)).mean()
    assert check["of"] == 1 and check["per_season"][0]["gain"] < 0.5 * leaky   # 2021 data is nearly calibrated, so little to learn


def test_fit_by_rule_writes_the_meta_block_with_the_markets_that_passed(tmp_path):
    bad, good = overconfident_rows(slope=0.6), overconfident_rows(slope=1.0, seed=1)
    rows = pd.concat([bad.assign(market="points"), good.assign(market="rebounds")], ignore_index=True)
    params, meta, checks = calibrate.fit_by_rule(rows, "some_model", "in_sample: test")
    assert set(params) == {"points", "rebounds"} and set(checks) == {"points", "rebounds"}
    assert params["points"][1] < 0.75 and params["rebounds"][1] > 0.9           # slope b recovers ~0.6 vs ~1.0
    assert set(meta) == {"model", "alpha_method", "fit_seasons", "n", "apply_to"}
    assert meta["model"] == "some_model" and meta["alpha_method"] == "in_sample: test"
    assert meta["fit_seasons"] == list(range(2021, 2027)) and meta["n"] == {"points": len(bad), "rebounds": len(good)}
    assert meta["apply_to"] == ["points"]
    path = tmp_path / "calibration.json"
    calibrate.save(params, path, meta=meta)
    assert json.loads(path.read_text())["_meta"] == meta
    assert calibrate.effective_apply_to(path) == ("points",) and set(calibrate.load(path)) == {"points", "rebounds"}
    # One season only: nothing held out, so nothing passes (an empty list, not a crash).
    one = bad[bad.season == 2021].assign(market="points")
    _, meta1, checks1 = calibrate.fit_by_rule(one, "m", "x")
    assert checks1["points"]["of"] == 0 and meta1["apply_to"] == []
