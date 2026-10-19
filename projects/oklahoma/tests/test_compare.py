"""Line-comparison tool: probabilities, break-even, flags, line log, and the slate placeholder rows.

Everything runs on a tiny synthetic league with fixed seeds; no network, no real data.
"""
import numpy as np
import pandas as pd
import pytest
from scipy import stats

from oklahoma import calibrate, compare as C, ingest, project as P, threes
from oklahoma.features import STATS, build_features
from oklahoma.models import PRODUCTION_MODEL, registry

TEAMS = ["AAA", "BBB", "CCC", "DDD"]


def tiny_games(seasons=(2021, 2022), per_season=24, seed=0):
    """4 teams x 5 players; the last 6 games of the final season are playoff games."""
    rng = np.random.default_rng(seed)
    rows, gid = [], 100
    for season in seasons:
        start = pd.Timestamp(f"{season}-05-15 23:00", tz="UTC")
        for g in range(per_season):
            gid += 1
            home, away = rng.choice(4, 2, replace=False)
            tip = start + pd.Timedelta(days=2 * g)
            playoffs = season == seasons[-1] and g >= per_season - 6
            for t, o, is_home in ((home, away, True), (away, home, False)):
                for p in range(5):
                    if rng.random() < 0.05:
                        continue
                    mins = float(rng.integers(12, 36))
                    reb, pts, ast = (float(rng.poisson(r * mins)) for r in (0.2, 0.45, 0.12))
                    tpa = float(rng.poisson(0.2 * mins))
                    rows.append({
                        "game_id": gid, "season": season, "season_type": 3 if playoffs else 2, "tip": tip,
                        "athlete_id": t * 100 + p, "athlete_display_name": f"Pat {TEAMS[t]}{p}",
                        "athlete_position_abbreviation": "GFFCG"[p], "team_id": t, "team_abbreviation": TEAMS[t],
                        "opponent_team_id": o, "opponent_team_abbreviation": TEAMS[o], "is_home": is_home,
                        "playoffs": playoffs, "starter": p < 3, "minutes": mins,
                        "offensive_rebounds": 0.0, "defensive_rebounds": reb, "rebounds": reb, "points": pts,
                        "assists": ast, "pra": reb + pts + ast,
                        "field_goals_attempted": float(rng.poisson(0.35 * mins)),
                        "free_throws_attempted": float(rng.poisson(0.1 * mins)),
                        "turnovers": float(rng.poisson(0.05 * mins)),
                        "threes_attempted": tpa, "threes_made": float(rng.binomial(int(tpa), 0.33)),
                    })
    df = pd.DataFrame(rows)
    score = df.groupby(["game_id", "team_id"])["points"].sum().rename("team_score").reset_index()
    df = df.merge(score, on=["game_id", "team_id"])
    opp = score.rename(columns={"team_id": "opponent_team_id", "team_score": "opponent_team_score"})
    return df.merge(opp, on=["game_id", "opponent_team_id"])


def last_roster(games, abbr):
    """Names who played the team's most recent game: the roster the slate projector expects."""
    t = games[games["team_abbreviation"] == abbr]
    return list(t[t["tip"] == t["tip"].max()]["athlete_display_name"])


def schedule_of(games, slate_date="2022-07-12", home="AAA", away="BBB", slate_type=3, extra_completed=()):
    """Schedule table in the sportsdataverse shape: every played game, optional unplayed completed games, one slate game."""
    g = games[games["is_home"]].drop_duplicates("game_id")
    rows = [{"game_id": r.game_id, "season": r.season, "season_type": r.season_type, "date": f"{r.tip:%Y-%m-%dT%H:%MZ}",
             "game_date": f"{r.tip:%Y-%m-%d}", "home_abbreviation": r.team_abbreviation,
             "away_abbreviation": r.opponent_team_abbreviation, "status_type_completed": True, "notes_headline": ""}
            for r in g.itertuples()]
    for gid, day, h, a in extra_completed:
        rows.append({"game_id": gid, "season": 2022, "season_type": 2, "date": f"{day}T23:00Z", "game_date": day,
                     "home_abbreviation": h, "away_abbreviation": a, "status_type_completed": True, "notes_headline": ""})
    rows.append({"game_id": 9000, "season": 2022, "season_type": slate_type, "date": f"{slate_date}T23:00Z",
                 "game_date": slate_date, "home_abbreviation": home, "away_abbreviation": away,
                 "status_type_completed": False, "notes_headline": "Test Game 1"})
    return pd.DataFrame(rows)


def hand_target():
    """Three rostered players: a starter, a bench player, and a newcomer with 3 career games."""
    return pd.DataFrame({
        "athlete_id": [1, 2, 3], "athlete_display_name": ["Ann Starter", "Bea Bench", "Cy Newbie"],
        "team_abbreviation": "AAA", "opponent_team_abbreviation": "BBB", "game_id": 7,
        "starter": [True, False, False], "starter_prev": [True, False, False],
        "career_games": [100, 80, 3], "min_ewm": [30.0, 15.0, 10.0],
    })


def hand_fits():
    mu = {"points": np.array([14.0, 4.0, 2.0]), "rebounds": np.array([6.0, 2.5, 1.0]),
          "assists": np.array([4.0, 1.5, 0.8])}
    mu["pra"] = mu["points"] + mu["rebounds"] + mu["assists"]
    alpha = {s: np.array([0.10, 0.20, 0.30]) for s in STATS}
    return {s: (mu[s], alpha[s]) for s in STATS}


def lines_of(*rows):
    df = pd.DataFrame(rows, columns=["player", "market", "line", "side"])
    df["side"] = df["side"].where(df["side"].notna(), None)
    return df


def run(lines, **kw):
    kw.setdefault("playoffs", False)
    kw.setdefault("cal_params", {})
    return C.evaluate(lines, hand_target(), hand_fits(), **kw)


# ---------- probabilities ----------

def test_over_push_under_sum_to_one_and_push_only_on_whole_lines():
    lines = lines_of(("Ann Starter", "points", 14.0, None), ("Ann Starter", "points", 14.5, None),
                     ("Ann Starter", "pr", 20.0, None), ("Ann Starter", "pr", 20.5, None),
                     ("Bea Bench", "ra", 4.0, None), ("Bea Bench", "pra", 8.5, None))
    res = run(lines)
    assert ((res.p_over + res.p_push + res.p_under) - 1).abs().max() < 1e-9
    assert ((res.p_more_cal + res.p_less_cal + res.p_push) - 1).abs().max() < 1e-9
    whole = res["line"] % 1 == 0
    assert (res.loc[whole, "p_push"] > 0).all()
    assert (res.loc[~whole, "p_push"] == 0).all()


def test_simulation_matches_the_negative_binomial_it_samples():
    res = run(lines_of(("Ann Starter", "points", 14.5, None), ("Ann Starter", "points", 14.0, None)))
    n = 1 / 0.10
    dist = stats.nbinom(n, n / (n + 14.0))
    assert res.p_over.iloc[0] == pytest.approx(dist.sf(14), abs=0.012)       # 4.8 standard errors at 40,000 draws
    assert res.p_push.iloc[1] == pytest.approx(dist.pmf(14), abs=0.012)
    assert res["mean"].iloc[0] == pytest.approx(14.0)
    assert res.sd.iloc[0] == pytest.approx(dist.std(), rel=0.03)


def test_rows_of_one_player_share_random_numbers_and_ignore_roster_order():
    # Same draws for every row of a player: P(>9.5) - P(>10.5) is exactly P(== 10).
    res = run(lines_of(("Ann Starter", "points", 9.5, None), ("Ann Starter", "points", 10.5, None),
                       ("Ann Starter", "points", 10.0, None)))
    assert res.p_over.iloc[0] - res.p_over.iloc[1] == pytest.approx(res.p_push.iloc[2], abs=1e-12)
    # Deterministic, and independent of who else is on the roster or in what order.
    again = run(lines_of(("Ann Starter", "points", 9.5, None), ("Ann Starter", "points", 10.5, None),
                         ("Ann Starter", "points", 10.0, None)))
    pd.testing.assert_frame_equal(res, again)
    order = [2, 0, 1]
    shuffled = C.evaluate(lines_of(("Ann Starter", "points", 9.5, None)), hand_target().iloc[order],
                          {s: (m[order], a[order]) for s, (m, a) in hand_fits().items()}, playoffs=False, cal_params={})
    assert shuffled.p_over.iloc[0] == res.p_over.iloc[0]


def test_break_even_for_pickem_slips():
    assert C.break_even(3, 2) == pytest.approx(0.5774, abs=5e-5)
    assert C.break_even(6, 3) == pytest.approx(0.5503, abs=5e-5)
    res = run(lines_of(("Ann Starter", "points", 10.5, None)), payout=3.0, legs=2)
    assert res.break_even.iloc[0] == pytest.approx(3 ** -0.5)
    assert res.edge.iloc[0] == pytest.approx(res.p_side.iloc[0] - 3 ** -0.5)
    assert res.side.iloc[0] == res.rec_side.iloc[0] == "MORE"                # mean 14 vs line 10.5



def test_benter_blend_pulls_legs_toward_the_line_and_drives_the_sort():
    res = run(lines_of(("Ann Starter", "points", 10.5, None), ("Ann Starter", "points", 14.0, None),
                       ("Bea Bench", "points", 3.5, None)), payout=3.0, legs=2)
    w = C.BENTER_W
    expect = w * res.p_side + (1 - w) * (1 - res.p_push) * 0.5
    assert (res.p_blend - expect).abs().max() < 1e-12
    assert (res.edge_blend - (res.p_blend - res.break_even)).abs().max() < 1e-12
    # A blend never moves a leg further from 50/50 than the model alone did.
    assert ((res.p_blend - 0.5 * (1 - res.p_push)).abs() <= (res.p_side - 0.5 * (1 - res.p_push)).abs() + 1e-12).all()
    # The Oct 9 lesson: raw 0.69 on a 3x 2-pick looks like +11% but blends below break-even.
    assert C.blend(0.69) == pytest.approx(0.557)
    assert C.blend(0.69) < C.break_even(3, 2) < 0.69
    # The printed table is ordered by the blended edge, not the raw one (orders made opposite here).
    t = res.copy()
    t["player"] = ["P1", "P2", "P3"]
    t["edge"], t["edge_blend"] = [-0.1, 0.0, 0.1], [0.1, 0.0, -0.1]
    assert [r.split()[0] for r in C.format_table(t).splitlines()[1:]] == ["P1", "P2", "P3"]


def test_break_even_follows_slip_size_on_every_row():
    # Every row is priced against the slip it is for, not a 2-pick default.
    for payout, legs in ((6.0, 3), (20.0, 5), (10.0, 4)):
        res = run(lines_of(("Ann Starter", "points", 10.5, None), ("Bea Bench", "points", 3.5, "LESS")),
                  payout=payout, legs=legs)
        assert (res.break_even - payout ** (-1 / legs)).abs().max() < 1e-12
        assert (res.edge_blend - (res.p_blend - res.break_even)).abs().max() < 1e-12
        assert (res.edge - (res.p_side - res.break_even)).abs().max() < 1e-12


def test_caller_side_drives_p_side_and_blend_even_against_the_model():
    # Ann: mean 14 vs 10.5 -> model says MORE. Bea: mean 4 vs 6.5 -> model says LESS. Each priced all three ways.
    res = run(lines_of(("Ann Starter", "points", 10.5, "MORE"), ("Ann Starter", "points", 10.5, "LESS"),
                       ("Ann Starter", "points", 10.5, None), ("Bea Bench", "points", 6.5, "MORE"),
                       ("Bea Bench", "points", 6.5, "LESS"), ("Bea Bench", "points", 6.5, None)), payout=3.0, legs=2)
    assert res.rec_side.tolist() == ["MORE"] * 3 + ["LESS"] * 3
    assert res.side.tolist() == ["MORE", "LESS", "MORE", "MORE", "LESS", "LESS"]
    more = res.side == "MORE"
    assert (res.p_side[more] == res.p_more_cal[more]).all()
    assert (res.p_side[~more] == res.p_less_cal[~more]).all()
    assert (res.p_blend - C.blend(res.p_side, res.p_push)).abs().max() < 1e-12
    assert (res.edge_blend - (res.p_blend - res.break_even)).abs().max() < 1e-12
    # Betting against the model scores worse than the model's own side, not a copy of it.
    assert res.edge_blend.iloc[1] < res.edge_blend.iloc[0] == res.edge_blend.iloc[2]
    assert res.edge_blend.iloc[3] < res.edge_blend.iloc[4] == res.edge_blend.iloc[5]


def test_calibration_applies_to_non_push_split_and_combos_shrink_toward_half():
    cal = {"points": (0.0, 0.8)}
    res = run(lines_of(("Ann Starter", "points", 14.0, None), ("Ann Starter", "rebounds", 5.5, None),
                       ("Ann Starter", "pr", 20.0, None)), cal_params=cal)
    pts, reb, pr = (res.iloc[i] for i in range(3))
    q = pts.p_over / (pts.p_over + pts.p_under)
    assert pts.p_more_cal == pytest.approx((1 - pts.p_push) * calibrate.apply(q, 0.0, 0.8))
    assert "UNCALIBRATED" not in pts["flags"].split()
    assert reb.p_more_cal == pytest.approx((1 - reb.p_push) * reb.p_over / (reb.p_over + reb.p_under))   # rebounds: no map
    assert "UNCALIBRATED" in reb["flags"].split()
    q = pr.p_over / (pr.p_over + pr.p_under)
    assert pr.p_more_cal == pytest.approx((1 - pr.p_push) * (0.5 + 0.85 * (q - 0.5)))


# ---------- playoff role bias ----------

def test_role_bias_shifts_means_by_previous_starter_in_playoffs_only():
    lines = lines_of(("Ann Starter", "points", 14.5, None), ("Ann Starter", "pra", 24.5, None),
                     ("Ann Starter", "pr", 20.5, None), ("Bea Bench", "points", 4.5, None),
                     ("Bea Bench", "pra", 8.5, None), ("Bea Bench", "ra", 4.5, None))
    on = run(lines, playoffs=True)
    assert on.role_shift.round(6).tolist() == [0.77, 1.20, 1.09, -0.94, -1.66, -0.72]
    assert (on["mean"] - on.mean_raw).round(6).tolist() == on.role_shift.round(6).tolist()
    assert (run(lines, playoffs=False).role_shift == 0).all()                 # regular season: off
    assert (run(lines, playoffs=True, role_bias=False).role_shift == 0).all() # --no-role-bias
    assert on.role.tolist() == ["S", "S", "S", "B", "B", "B"]


def test_role_bias_keeps_whole_number_lines_pushable_and_starter_prev_wins():
    res = run(lines_of(("Ann Starter", "points", 15.0, None)), playoffs=True)
    assert res.p_push.iloc[0] > 0                                            # shifted mean, integer draws
    t = hand_target()
    t.loc[0, "starter_prev"] = False                                          # started tonight's roster slot, not last game
    shifted = C.evaluate(lines_of(("Ann Starter", "points", 14.5, None)), t, hand_fits(), playoffs=True, cal_params={})
    assert shifted.role.iloc[0] == "B" and shifted.role_shift.iloc[0] == pytest.approx(-0.94)
    t = t.drop(columns="starter_prev")                                        # no starter_prev: use the roster's last-game flag
    assert C.evaluate(lines_of(("Ann Starter", "points", 14.5, None)), t, hand_fits(), playoffs=True,
                      cal_params={}).role.iloc[0] == "S"


def test_role_bias_status_allows_only_plus2_and_names_the_reason():
    ok, why = C.role_bias_status("context_glm_plus2")
    assert ok and why == ""
    for name in ("context_glm_plus2s", "context_glm_plus2si"):                  # starter_prev is in the design
        ok, why = C.role_bias_status(name)
        assert not ok and "starter_prev" in why and "twice" in why
    for name in ("context_glm", "context_glm_plus", "context_glm_plus2o", "season_avg"):   # never measured against the constants
        ok, why = C.role_bias_status(name)
        assert not ok and "context_glm_plus2 only" in why
    with pytest.raises(SystemExit):
        C.role_bias_status("no_such_model")


def test_no_double_counting_of_the_playoff_role_effect():
    games = tiny_games()
    sched = schedule_of(games)                                                   # the slate game is a playoff game
    names = last_roster(games, "AAA")
    lines = lines_of(*[(n, mkt, line, None) for n in names for mkt, line in (("points", 8.5), ("pra", 14.5))])
    for name in ("context_glm_plus2si", "context_glm_plus2s"):                   # designs with starter_prev terms
        asked, info = compare_tiny(lines, games, sched, model=name, role_bias=True)
        not_asked, _ = compare_tiny(lines, games, sched, model=name, role_bias=False)
        assert info["playoffs"] and not info["role_bias"]
        assert (asked.role_shift == 0).all() and (asked["mean"] == asked.mean_raw).all()
        pd.testing.assert_frame_equal(asked, not_asked)                          # asking for the shift changes nothing
    # plus2 (no starter terms) still gets exactly the documented starter / bench constants on its own means.
    on, info = compare_tiny(lines, games, sched, model="context_glm_plus2")
    off, _ = compare_tiny(lines, games, sched, model="context_glm_plus2", role_bias=False)
    assert info["role_bias"] and set(on.role) == {"S", "B"}
    want = np.array([C.ROLE_BIAS[r == "S"][m] for r, m in zip(on.role, on.market)])
    np.testing.assert_allclose(on.role_shift, want)
    np.testing.assert_allclose(on["mean"], off["mean"] + want)
    np.testing.assert_allclose(on.mean_raw, off.mean_raw)


def test_the_plus2_shift_would_double_count_on_a_model_with_starter_terms():
    # Synthetic playoffs where bench means are cut and starters' raised (the effect ROLE_BIAS encodes). plus2 leaves that
    # bias in its means, so the shift removes it; plus2si has already removed it, so the same shift puts it back
    # with the opposite sign.
    from test_plus2s import design_frame
    from oklahoma.models import ContextGLMPlus2, ContextGLMPlus2SI
    shape = dict(playoff_shift=(0.90, 1.07), p_playoff=0.15)
    train = design_frame(range(2014, 2020), n=4000, seed=1, **shape)
    test = design_frame([2020], n=12000, seed=2, **shape)
    po, sp = test["playoffs"].to_numpy(bool), test["starter_prev"].to_numpy(bool)
    groups = {"bench": po & ~sp, "starter": po & sp}
    shift = np.where(sp, C.ROLE_BIAS[True]["points"], C.ROLE_BIAS[False]["points"])
    y = test["points"].to_numpy()
    bias = {}
    for cls in (ContextGLMPlus2, ContextGLMPlus2SI):
        mu = cls("points").fit(train).predict_mean(test)
        bias[cls.__name__] = {g: ((y - mu)[m].mean(), (y - (mu + shift))[m].mean()) for g, m in groups.items()}
    for g in groups:
        before, after = bias["ContextGLMPlus2"][g]
        assert abs(before) > 0.5 and abs(after) < 0.5 * abs(before), (g, before, after)     # the shift helps plus2
        before, after = bias["ContextGLMPlus2SI"][g]
        assert abs(before) < 0.15 and abs(after) > 0.6 and abs(after) > 4 * abs(before), (g, before, after)   # and hurts plus2si


# ---------- flags ----------

def flags_of(res, i):
    return set(res["flags"].iloc[i].split())


def test_flags_fire_only_when_their_condition_holds():
    lines = lines_of(
        ("Ann Starter", "points", 14.5, "MORE"),     # 0: SAME_PLAYER (2 rows), nothing else
        ("Ann Starter", "points", 30.5, None),       # 1: BIG_DISAGREEMENT (line 16 above the mean, sd ~5)
        ("Bea Bench", "points", 3.5, "MORE"),        # 2: PLAYOFF_BENCH_MORE
        ("Cy Newbie", "assists", 0.5, "LESS"),       # 3: LOW_HISTORY, side LESS so no bench flag
        ("Cy Newbie", "pa", 2.5, "MORE"),            # 4: LOW_HISTORY + bench MORE + combo
        ("Nobody Here", "points", 9.5, None),        # 5: unmatched
    )
    res = run(lines, playoffs=True)
    f = [flags_of(res, i) for i in range(6)]
    assert "SAME_PLAYER" in f[0] and "SAME_PLAYER" in f[1] and not (f[2] & {"SAME_PLAYER"})
    assert "BIG_DISAGREEMENT" in f[1] and "BIG_DISAGREEMENT" not in f[0]
    assert "PLAYOFF_BENCH_MORE" in f[2] and "PLAYOFF_BENCH_MORE" not in f[0] | f[3]
    assert "LOW_HISTORY" in f[3] and "LOW_HISTORY" in f[4] and "LOW_HISTORY" not in f[2]
    assert "PLAYOFF_BENCH_MORE" in f[4] and "COMBO_UNCALIBRATED" in f[4] and "COMBO_UNCALIBRATED" not in f[3]
    assert "NOT_ON_ROSTER" in f[5] and np.isnan(res.p_more_cal.iloc[5])
    assert not any("STALE" in x for x in f)
    # Not a playoff game: bench MORE is fine. LESS is never flagged.
    reg = run(lines, playoffs=False)
    assert "PLAYOFF_BENCH_MORE" not in flags_of(reg, 2) | flags_of(reg, 4)


def test_stale_flag_marks_every_row_including_unmatched():
    res = run(lines_of(("Ann Starter", "points", 14.5, None), ("Nobody Here", "points", 9.5, None)), stale=True)
    assert all("STALE" in flags_of(res, i) for i in range(2))


def test_staleness_compares_latest_completed_game_in_schedule_to_the_data():
    games = tiny_games()
    last = games["tip"].max()
    assert C.staleness(games, schedule_of(games), ["AAA", "BBB"], pd.Timestamp("2022-07-12T23:00Z")) == {}
    # A completed AAA game the data never saw (after the data's last game, before the slate game).
    day = f"{last + pd.Timedelta(days=2):%Y-%m-%d}"
    sched = schedule_of(games, extra_completed=[(8888, day, "AAA", "CCC")])
    stale = C.staleness(games, sched, ["AAA", "BBB"], pd.Timestamp("2022-07-12T23:00Z"))
    assert list(stale) == ["AAA"] and "8888" in stale["AAA"]
    # Not-yet-completed games and games after the slate tip are ignored.
    assert C.staleness(games, sched, ["AAA"], pd.Timestamp(f"{day}T00:00Z")) == {}


def test_minutes_diff_flag_fires_at_three_minutes_and_changes_nothing_else():
    lines = lines_of(("Ann Starter", "points", 14.5, None), ("Bea Bench", "points", 4.5, None),
                     ("Cy Newbie", "points", 2.5, None), ("Nobody Here", "points", 9.5, None))
    # hand_target min_ewm = 30, 15, 10. Differences: +3.0 (the boundary, flagged), +2.9 (no), -3.5 (flagged, either sign).
    p50 = np.array([33.0, 17.9, 6.5])
    res = run(lines, min_p50=p50)
    assert [("MINUTES_DIFF" in f.split()) for f in res["flags"]] == [True, False, True, False]
    assert res.min_p50.iloc[:3].tolist() == p50.tolist() and np.isnan(res.min_p50.iloc[3])
    base = run(lines)                                                               # no minutes model: no flag, no column values
    assert base.min_p50.isna().all() and not base["flags"].str.contains("MINUTES_DIFF").any()
    drop = ["flags", "min_p50"]
    pd.testing.assert_frame_equal(res.drop(columns=drop), base.drop(columns=drop))  # a flag, never a model input
    nan = run(lines, min_p50=np.array([np.nan, 17.9, 6.5]))                          # a missing prediction cannot flag
    assert "MINUTES_DIFF" not in nan["flags"].iloc[0].split()


def test_compare_flags_minutes_diff_from_a_minutes_model_fit_on_the_training_window(monkeypatch):
    games = tiny_games()
    sched = schedule_of(games)
    names = last_roster(games, "AAA") + last_roster(games, "BBB")
    lines = lines_of(*[(n, "points", 9.5, None) for n in names])

    seen = {}

    class Spy(C.MinutesModel):
        def fit(self, train):
            seen["train"] = train.copy()
            return super().fit(train)

    monkeypatch.setattr(C, "MinutesModel", Spy)
    res, info = compare_tiny(lines, games, sched)
    tip = info["game"]["tip"]
    assert seen["train"]["tip"].max() < tip and 9000 not in set(seen["train"]["game_id"])    # no slate rows, nothing at or after tip
    assert (seen["train"]["career_games"] >= 5).all() and len(res) == len(names)
    got = res.dropna(subset=["mean"])
    assert got.min_p50.notna().all()
    flagged = got["flags"].str.contains("MINUTES_DIFF")
    assert (flagged == ((got.min_p50 - got.recent_min).abs() >= C.MINUTES_DIFF_MIN)).all()
    # The threshold is what decides, in both directions (the synthetic league may not straddle 3 minutes by itself).
    monkeypatch.setattr(C, "MINUTES_DIFF_MIN", 0.0)
    assert compare_tiny(lines, games, sched)[0]["flags"].str.contains("MINUTES_DIFF").all()
    monkeypatch.setattr(C, "MINUTES_DIFF_MIN", 1e9)
    assert not compare_tiny(lines, games, sched)[0]["flags"].str.contains("MINUTES_DIFF").any()
    # Without the minutes model: no flag, no column values, and identical projections.
    monkeypatch.setattr(C, "MINUTES_DIFF_MIN", 3.0)
    off, _ = compare_tiny(lines, games, sched, minutes_flag=False)
    assert off.min_p50.isna().all() and not off["flags"].str.contains("MINUTES_DIFF").any()
    pd.testing.assert_frame_equal(res.drop(columns=["flags", "min_p50"]), off.drop(columns=["flags", "min_p50"]))


# ---------- inputs ----------

def test_read_lines_accepts_mkt_alias_market_names_and_sides(tmp_path):
    f = tmp_path / "lines.csv"
    f.write_text("player,mkt,line,side\nAnn Starter,PTS,14.5,over\nAnn Starter,P+R,20,Less\nBea Bench,pra,8.5,\n")
    df = C.read_lines(f)
    assert df.market.tolist() == ["points", "pr", "pra"] and df.line.tolist() == [14.5, 20.0, 8.5]
    assert df.side.tolist() == ["MORE", "LESS", None]
    f.write_text("player,market,line\nAnn Starter,steals,1.5\n")
    with pytest.raises(SystemExit):
        C.read_lines(f)
    f.write_text("player,line\nAnn Starter,1.5\n")
    with pytest.raises(SystemExit):
        C.read_lines(f)


def test_name_matching_ignores_case_accents_and_punctuation():
    assert C.normalize_name("A'ja Wilson") == C.normalize_name("AJA WILSON") == "aja wilson"
    assert C.normalize_name("Cheyenne Parker-Tyus") == C.normalize_name("cheyenne parker tyus")
    assert C.normalize_name("Cecilia Zandalasini ") == "cecilia zandalasini"
    assert C.normalize_name("Nyára Sabally") == "nyara sabally"


# ---------- end to end on the synthetic league ----------

def compare_tiny(lines, games, sched, **kw):
    """C.compare on the synthetic league: few sims, no calibration file, a small minutes model."""
    return C.compare(lines, games, sched, "2022-07-12", "AAA", **{"n_sims": 4000, "cal_params": {}, "minutes_iter": 20, **kw})


def test_compare_end_to_end_and_line_log(tmp_path):
    games = tiny_games()
    sched = schedule_of(games)
    a, b = last_roster(games, "AAA")[0], last_roster(games, "BBB")[0]
    lines = lines_of((a, "points", 12.5, None), (a, "pra", 20.0, "LESS"),
                     (b, "rebounds", 4.5, None), ("Pat Ghost", "points", 9.5, None))
    res, info = compare_tiny(lines, games, sched)
    assert info["playoffs"] and not info["stale"]
    assert info["model"] == PRODUCTION_MODEL == "context_glm_plus2si" and info["data_cutoff"] == games["tip"].max().isoformat()
    assert not info["role_bias"] and "starter_prev" in info["role_bias_note"]        # plus2si models the role itself
    assert len(res) == 4 and res.game_id.iloc[:3].eq(9000).all()
    assert ((res.p_over + res.p_push + res.p_under).dropna() - 1).abs().max() < 1e-9
    assert res.loc[0, ["mean", "role_shift"]].notna().all() and (res.role_shift.dropna() == 0).all()
    assert "NOT_ON_ROSTER" in res["flags"].iloc[3]
    # plus2 keeps the ad hoc playoff role shift, which is on by default and can be switched off.
    p2, info_p2 = compare_tiny(lines, games, sched, model="context_glm_plus2")
    assert info_p2["role_bias"] and info_p2["role_bias_note"].startswith("ON") and p2.loc[0, "role_shift"] != 0
    off, info_off = compare_tiny(lines, games, sched, model="context_glm_plus2", role_bias=False)
    assert (off.role_shift.dropna() == 0).all() and not info_off["role_bias"] and "--no-role-bias" in info_off["role_bias_note"]
    # A model can be chosen by name.
    glm, info2 = compare_tiny(lines, games, sched, model="context_glm")
    assert info2["model"] == "context_glm" and not np.allclose(glm.mean_raw.dropna(), res.mean_raw.dropna())

    # A schedule that shows an unseen completed game: every row flagged STALE.
    stale_sched = schedule_of(games, extra_completed=[(8888, f"{games['tip'].max() + pd.Timedelta(days=1):%Y-%m-%d}", "AAA", "CCC")])
    bad, info3 = compare_tiny(lines, games, stale_sched)
    assert list(info3["stale"]) == ["AAA"] and bad["flags"].str.contains("STALE").all()

    # The line log gets every row (matched or not), with one header however many runs append.
    log = tmp_path / "data" / "line_log.csv"
    for _ in range(2):
        assert C.append_log(res, date="2022-07-12", model=info["model"], data_cutoff=info["data_cutoff"], path=log) == 4
    got = pd.read_csv(log)
    assert list(got.columns) == C.LOG_COLS and len(got) == 8
    assert got.timestamp_utc.str.endswith("+00:00").all()
    assert got.p_more_cal.iloc[:3].between(0, 1).all() and np.isnan(got.p_more_cal.iloc[3])
    assert got.player.iloc[3] == "Pat Ghost" and got.game_id.eq(9000).all()


def test_line_log_default_path_is_read_at_call_time(tmp_path, monkeypatch):
    # Tests and demos redirect C.LOG_PATH; a default bound at import time would write the real log.
    res = run(lines_of(("Ann Starter", "points", 14.5, None), ("Nobody Here", "points", 9.5, None)))
    monkeypatch.setattr(C, "LOG_PATH", tmp_path / "elsewhere" / "log.csv")
    assert C.append_log(res, date="2026-10-09", model="m", data_cutoff="2026-10-08T01:30:00+00:00") == 2
    got = pd.read_csv(tmp_path / "elsewhere" / "log.csv")
    assert got["player"].tolist() == ["Ann Starter", "Nobody Here"] and got["athlete_id"].iloc[0] == 1
    assert np.isnan(got["athlete_id"].iloc[1]) and "NOT_ON_ROSTER" in got["flags"].iloc[1]


def test_cli_writes_the_report_and_the_log_where_it_is_told_to(tmp_path, monkeypatch, capsys):
    games = tiny_games()
    path = tmp_path / "player_games.parquet"
    games.to_parquet(path)
    monkeypatch.setattr(ingest, "GAMES_PATH", path)
    monkeypatch.setattr(P, "load_schedule", lambda season: schedule_of(games))
    monkeypatch.setattr(C, "REPORTS", tmp_path / "reports")
    monkeypatch.setattr(C, "LOG_PATH", tmp_path / "must_stay_empty.csv")
    names = last_roster(games, "AAA")[:2]
    csv = tmp_path / "lines.csv"
    csv.write_text("player,mkt,line\n" + "".join(f"{n},pts,9.5\n{n},pr,14.0\n" for n in names) + "Pat Ghost,pts,8.5\n")
    log = tmp_path / "scratch_log.csv"
    assert C.main(["--date", "2022-07-12", "--team", "AAA", "--lines", str(csv), "--log", str(log)]) == 0
    out = capsys.readouterr().out
    assert "model context_glm_plus2si" in out and "role bias off: context_glm_plus2si already models" in out
    assert str(log) in out and not (tmp_path / "must_stay_empty.csv").exists()
    got = pd.read_csv(tmp_path / "reports" / "compare_2022-07-12_AAA.csv")
    assert len(got) == 5 and ((got.p_over + got.p_push + got.p_under).dropna() - 1).abs().max() < 1e-9
    assert ((got.p_more_cal + got.p_less_cal + got.p_push).dropna() - 1).abs().max() < 1e-9
    assert len(pd.read_csv(log)) == 5 and "NOT_ON_ROSTER" in got["flags"].iloc[-1]


def test_compare_refuses_a_game_already_in_the_data():
    games = tiny_games()
    sched = schedule_of(games)
    sched.loc[sched.index[-1], "game_id"] = int(games.game_id.iloc[0])
    with pytest.raises(SystemExit, match="already in the data"):
        compare_tiny(lines_of(("Pat AAA0", "points", 12.5, None)), games, sched)


# ---------- project.py ----------

def test_project_outputs_unrounded_mu_alpha_model_and_cutoff(tmp_path, monkeypatch):
    games = tiny_games()
    path = tmp_path / "player_games.parquet"
    games.to_parquet(path)
    monkeypatch.setattr(ingest, "GAMES_PATH", path)
    monkeypatch.setattr(P, "load_schedule", lambda season: schedule_of(games))
    monkeypatch.setattr(calibrate, "PATH", tmp_path / "no_calibration.json")   # independent of the production file
    slate, res = P.project("2022-07-12", set(), model="context_glm")
    assert (res.model == "context_glm").all() and (res.data_cutoff == games["tip"].max().isoformat()).all()
    assert {"mu", "alpha"} <= set(res.columns) and res.mu.notna().all() and res.alpha.notna().all()
    assert not np.allclose(res.mu, res.mu.round(1))                          # unrounded
    assert np.allclose(res.projection, res.mu.round(1))
    other = P.project("2022-07-12", set())[1]                                 # default = the production model
    assert (other.model == "context_glm_plus2si").all() and P.DEFAULT_MODEL == PRODUCTION_MODEL
    assert P.get_model() is registry()["context_glm_plus2si"]
    with pytest.raises(SystemExit):
        P.get_model("no_such_model")


def test_production_means_are_the_models_own_predicted_means_with_no_role_adjustment(tmp_path, monkeypatch):
    # No role multiplier / starter shift on top of plus2si anywhere on the production path. In a playoff game (where
    # the plus2 shift would fire) with the shift requested, project.py's mu and compare.py's mean for every row equal
    # ContextGLMPlus2SI.predict_mean, fit independently here on the same training rows.
    from oklahoma.models import ContextGLMPlus2SI
    games = tiny_games()
    sched = schedule_of(games)
    path = tmp_path / "player_games.parquet"
    games.to_parquet(path)
    monkeypatch.setattr(ingest, "GAMES_PATH", path)
    monkeypatch.setattr(P, "load_schedule", lambda season: sched)
    slate = P.load_slate("2022-07-12", 2022, sched)
    train, target = P.prepare(games, slate, set())
    assert target["playoffs"].all() and target["starter_prev"].any() and not target["starter_prev"].all()
    want = {s: ContextGLMPlus2SI(s).fit(train).predict_mean(target) for s in STATS}
    names = target["athlete_display_name"].tolist()

    proj = P.project("2022-07-12", set())[1]                                   # default model
    assert (proj.model == PRODUCTION_MODEL).all()
    for s in STATS:
        got = proj[proj.market == s]
        assert got["player"].tolist() == names
        np.testing.assert_array_equal(got["mu"].to_numpy(), want[s])

    lines = lines_of(*[(n, s, 9.5, None) for n in names for s in STATS])
    res, info = compare_tiny(lines, games, sched, role_bias=True, minutes_flag=False)
    assert info["playoffs"] and not info["role_bias"] and set(res.role) == {"S", "B"}
    for s in STATS:
        got = res[res.market == s]
        assert got["player"].tolist() == names
        np.testing.assert_array_equal(got["mean"].to_numpy(), want[s])
        np.testing.assert_array_equal(got["mean_raw"].to_numpy(), want[s])
        assert (got["role_shift"] == 0).all()
    # A known row, spelled out: a bench player, the case the plus2 shift would have cut by 0.94 points.
    i = names.index(target.loc[~target["starter_prev"], "athlete_display_name"].iloc[0])
    row = res[(res.player == names[i]) & (res.market == "points")].iloc[0]
    assert row.role == "B" and row["mean"] == want["points"][i] == proj[(proj.player == names[i]) & (proj.market == "points")]["mu"].iloc[0]


def test_placeholder_rows_carry_zero_threes_and_box_columns_not_nan():
    games = tiny_games()
    slate = P.load_slate("2022-07-12", 2022, schedule_of(games))
    ph = P.placeholder_rows(games, slate, set())
    assert len(ph) == len(last_roster(games, "AAA")) + len(last_roster(games, "BBB")) > 0
    for col in ["threes_made", "threes_attempted", "field_goals_attempted", "free_throws_attempted", "turnovers"]:
        assert ph[col].notna().all() and (ph[col] == 0.0).all(), col
    # The reason it matters: with the columns missing, 3P% and career 3PA/game silently become NaN.
    both = lambda p: pd.concat([games.assign(_slate=False), p.assign(_slate=True)], ignore_index=True)
    ok = threes.three_features(both(ph))
    slate_ids = set(ph.athlete_id)
    mine = ok[ok.game_id.eq(9000)]
    assert len(mine) == len(ph) and mine[["att_pm_ewm", "mk_pm_ewm", "pct_shrunk", "att_pg_career"]].notna().all().all()
    broken = threes.three_features(both(ph.drop(columns=["threes_made", "threes_attempted"])))
    assert broken[broken.game_id.eq(9000)][["pct_shrunk", "att_pg_career"]].isna().all().all()
    # And the model features the slate rows feed to a model are all finite.
    feats = build_features(both(ph))
    row = feats[feats.game_id.eq(9000)]
    assert len(row) == len(ph) and slate_ids == set(row.athlete_id)
    needed = ["min_ewm", "usage_pm_ewm", "pace_ratio", "out_minutes", "career_games", "starter_prev"] + \
        [f"{s}_pm_ewm" for s in STATS] + [f"opp_{s}_ratio" for s in STATS]
    assert row[needed].notna().all().all()


# ---------- threes.py ----------

def test_threes_model_fits_dispersion_per_fifth_of_predicted_mean():
    rng = np.random.default_rng(5)
    n = 6000
    minutes = rng.uniform(8, 36, n)
    att_pm, pct = rng.uniform(0.02, 0.35, n), rng.uniform(0.25, 0.42, n)
    mu_true = att_pm * minutes * pct * 1.1
    alpha_true = np.where(mu_true > np.median(mu_true), 0.02, 0.5)           # low-volume shooters are far more dispersed
    nb_n = 1 / alpha_true
    d = pd.DataFrame({
        "att_pm_ewm": att_pm, "mk_pm_ewm": att_pm * pct, "pct_shrunk": pct, "min_ewm": minutes, "minutes": minutes,
        "is_home": rng.random(n) < 0.5, "playoffs": False, "pace_ratio": 1.0, "out_minutes": 0.0,
        "threes_made": rng.negative_binomial(nb_n, nb_n / (nb_n + mu_true)).astype(float),
    })
    m = threes.ThreesModel().fit(d)
    mu = m.predict_mean(d)
    alphas = m.alpha_for(mu)
    assert len(m.alpha_bins_) == 5 and alphas.shape == mu.shape
    assert len(np.unique(alphas)) > 1 and alphas[mu < np.quantile(mu, .2)].mean() > alphas[mu > np.quantile(mu, .8)].mean()
    assert m.alpha_ > 0 and mu.min() > 0
