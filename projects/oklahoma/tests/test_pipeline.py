import numpy as np
import pandas as pd
import pytest

from oklahoma import benter
from oklahoma.backtest import walk_forward
from oklahoma.features import STATS, build_features
from oklahoma.models import fit_alpha, log_pmf, prob_over, registry

POSITIONS = ["G", "G", "F", "F", "C"]


def synthetic_games(seasons=(2020, 2021, 2022), teams=4, players_per_team=5, games_per_season=20,
                    absence_rate=0.05, seed=0):
    rng = np.random.default_rng(seed)
    rows, gid = [], 0
    for season in seasons:
        start = pd.Timestamp(f"{season}-05-15", tz="UTC")
        for g in range(games_per_season):
            gid += 1
            home, away = rng.choice(teams, 2, replace=False)
            tip = start + pd.Timedelta(days=2 * g)
            for team, opp, is_home in [(home, away, True), (away, home, False)]:
                for p in range(players_per_team):
                    if rng.random() < absence_rate:
                        continue
                    minutes = float(rng.integers(10, 36))
                    reb = float(rng.poisson(0.2 * minutes * (1 + p / 5)))
                    pts = float(rng.poisson(0.45 * minutes))
                    ast = float(rng.poisson(0.1 * minutes * (2 - p / 4)))
                    rows.append({
                        "game_id": gid, "season": season, "tip": tip,
                        "athlete_id": team * 100 + p, "athlete_display_name": f"P{team}-{p}",
                        "athlete_position_abbreviation": POSITIONS[p], "team_id": team, "opponent_team_id": opp,
                        "is_home": is_home, "playoffs": False, "starter": p < 3, "minutes": minutes,
                        "rebounds": reb, "points": pts, "assists": ast, "pra": reb + pts + ast,
                        "field_goals_attempted": float(rng.poisson(0.35 * minutes)),
                        "free_throws_attempted": float(rng.poisson(0.1 * minutes)),
                        "turnovers": float(rng.poisson(0.05 * minutes)),
                    })
    df = pd.DataFrame(rows)
    score = df.groupby(["game_id", "team_id"])["points"].sum().rename("team_score").reset_index()
    df = df.merge(score, on=["game_id", "team_id"])
    opp = score.rename(columns={"team_id": "opponent_team_id", "team_score": "opponent_team_score"})
    return df.merge(opp, on=["game_id", "opponent_team_id"])


PREGAME_COLS = (
    ["career_games", "season_games", "min_l5", "min_ewm", "rest_days", "b2b", "team_games_last7",
     "days_since_last", "team_games_missed", "returning", "out_minutes", "coach_tenure", "new_coach",
     "usage_pm_ewm", "pace_ratio", "starter_prev", "season_min_pg"]
    + [f"{c}_{s}" for s in STATS for c in ["out", "opp"] if c == "out"]
    + [f"opp_{s}_ratio" for s in STATS]
    + [f"{s}_{c}" for s in STATS for c in ["l5", "l10", "ewm", "pm_ewm"]]
    + [f"{c}_{s}_{u}" for s in STATS for c, u in [("career", "pm"), ("season", "pg"), ("season", "pm")]]
    + [f"line_proxy_{s}" for s in STATS]
)


def test_features_use_only_prior_games():
    games = synthetic_games()
    base = build_features(games)
    # Blow up one mid-sample game's box score for every player in it.
    target = games["game_id"].iloc[len(games) // 2]
    tampered = games.copy()
    hit = tampered["game_id"] == target
    for s in ["rebounds", "points", "assists", "pra", "field_goals_attempted", "team_score", "opponent_team_score"]:
        tampered.loc[hit, s] += 50
    tampered.loc[hit, "minutes"] += 10
    # The lineup is only known at tip, so flipping this game's own starter flag must not change
    # any pregame feature of the game (starter_prev reads the PREVIOUS game's flag).
    tampered.loc[hit, "starter"] = ~tampered.loc[hit, "starter"]
    after = build_features(tampered)

    key = ["game_id", "athlete_id"]
    merged = base.merge(after, on=key, suffixes=("", "_t"))
    tip_target = games.loc[hit, "tip"].iloc[0]
    upto = merged[merged["tip"] <= tip_target]
    for col in PREGAME_COLS:
        pd.testing.assert_series_equal(upto[col], upto[f"{col}_t"], check_names=False, obj=col)
    # And it must matter afterwards, or the test proves nothing.
    later = merged[(merged["tip"] > tip_target) & merged["athlete_id"].isin(games.loc[hit, "athlete_id"])]
    for col in ["reb_ewm", "points_ewm", "opp_points_ratio", "usage_pm_ewm", "pace_ratio", "season_min_pg"]:
        assert not np.allclose(later[col], later[f"{col}_t"], equal_nan=True), col
    # starter_prev carries the flipped flag into the player's next game (so the tamper is visible downstream).
    assert (later["starter_prev"] != later["starter_prev_t"]).any()


def test_season_min_pg_uses_only_strictly_prior_games_of_the_season():
    # season_min_pg feeds the minutes model behind compare.py's MINUTES_DIFF flag. Corrupt ONE future game's minutes
    # for one player: her season_min_pg up to and including that game must not move; only later games of the season do.
    games = synthetic_games(absence_rate=0.0)
    pid, season = 101, 2021
    mine = games[games["athlete_id"] == pid].sort_values("tip")
    this = mine[mine["season"] == season]
    victim = this.iloc[len(this) // 2]
    tampered = games.copy()
    tampered.loc[(tampered["athlete_id"] == pid) & (tampered["game_id"] == victim["game_id"]), "minutes"] = 999.0
    col = lambda f: f[f["athlete_id"] == pid].set_index("game_id")["season_min_pg"]
    base, after = col(build_features(games)), col(build_features(tampered))

    upto = this.loc[this["tip"] <= victim["tip"], "game_id"]
    later = this.loc[this["tip"] > victim["tip"], "game_id"]
    assert len(upto) >= 3 and len(later) >= 3
    pd.testing.assert_series_equal(base.loc[upto], after.loc[upto])
    # The definition, exactly: mean of her strictly earlier minutes this season (NaN before her first game of it).
    expected = this["minutes"].shift(1).expanding().mean().to_numpy()
    np.testing.assert_allclose(base.loc[this["game_id"]].to_numpy(), expected, equal_nan=True)
    assert np.isnan(base.loc[this["game_id"].iloc[0]])
    # The corruption is visible afterwards (so the check above is not vacuous) and does not cross into next season.
    assert (after.loc[later] > base.loc[later] + 10).all()
    nxt = mine.loc[mine["season"] == season + 1, "game_id"]
    pd.testing.assert_series_equal(base.loc[nxt], after.loc[nxt])


def test_teammates_out_counts_missing_rotation_player():
    games = synthetic_games(seasons=(2022,), teams=2, absence_rate=0.0, games_per_season=12)
    star = 0 * 100 + 4                                   # team 0, player 4
    team0_games = games.loc[games["team_id"] == 0, "game_id"].unique()
    sit = team0_games[6]
    games = games[~((games["athlete_id"] == star) & (games["game_id"] == sit))]
    f = build_features(games)

    star_min_before = (
        games[(games["athlete_id"] == star) & (games["game_id"].isin(team0_games[:6]))]["minutes"]
        .ewm(halflife=5).mean().iloc[-1]
    )
    tonight = f[(f["game_id"] == sit) & (f["team_id"] == 0)]
    np.testing.assert_allclose(tonight["out_minutes"], star_min_before)
    assert (f.loc[(f["game_id"] == team0_games[5]) & (f["team_id"] == 0), "out_minutes"] == 0).all()
    # Opponents are unaffected.
    assert (f.loc[(f["game_id"] == sit) & (f["team_id"] != 0), "out_minutes"] == 0).all()
    # The star's own return game is flagged when she has missed 2+ games; one miss is not.
    back = f[(f["athlete_id"] == star) & (f["game_id"] == team0_games[7])]
    assert back["team_games_missed"].iloc[0] == 1 and not back["returning"].iloc[0]


def test_coach_change_resets_tenure_mid_season():
    games = synthetic_games(seasons=(2021, 2022), teams=2, absence_rate=0.0, games_per_season=16)
    coaches = pd.DataFrame({
        "team_id": [0, 0, 0, 1, 1],
        "season": [2021, 2022, 2022, 2021, 2022],
        "from_game": [1, 1, 6, 1, 1],
        "coach": ["A", "A", "B", "C", "C"],
        "tenure_before_2015": ["yes", None, None, None, None],
        "note": None,
    })
    f = build_features(games, coaches).drop_duplicates(["game_id", "team_id"])
    t0 = f[(f["team_id"] == 0) & (f["season"] == 2022)].sort_values("tip")
    assert list(t0["coach"].iloc[4:6]) == ["A", "B"]
    assert t0["coach_tenure"].iloc[4] == 100 and not t0["new_coach"].iloc[4]   # carried-over coach
    assert t0["coach_tenure"].iloc[5] == 0 and t0["new_coach"].iloc[5]         # first game for B
    assert t0["coach_tenure"].iloc[6] == 1
    t1 = f[f["team_id"] == 1].sort_values("tip")
    assert t1["coach_tenure"].tolist() == list(range(len(t1)))                 # same coach both seasons
    assert t1["coach_known"].all()


@pytest.mark.parametrize("alpha", [0.0, 0.15])
def test_distribution_is_consistent(alpha):
    mu = np.array([0.7, 4.0, 11.5])
    y = np.arange(0, 200)[:, None]
    total = np.exp(log_pmf(y, mu, alpha)).sum(axis=0)
    np.testing.assert_allclose(total, 1.0, atol=1e-9)
    over = prob_over(np.array([6.5, 6.5, 6.5]), mu, alpha)
    manual = np.exp(log_pmf(y[7:], mu, alpha)).sum(axis=0)
    np.testing.assert_allclose(over, manual, atol=1e-9)


def test_fit_alpha_recovers_overdispersion():
    rng = np.random.default_rng(1)
    mu = rng.uniform(2, 10, 20000)
    alpha = 0.2
    y = rng.negative_binomial(1 / alpha, (1 / alpha) / (1 / alpha + mu))
    assert abs(fit_alpha(y, mu) - alpha) < 0.03
    assert fit_alpha(rng.poisson(mu), mu) < 0.02


def test_walk_forward_trains_only_on_past_seasons():
    feats = build_features(synthetic_games())
    res = walk_forward(feats, list(registry()), [2022], train_window=5, min_prior_games=3)
    assert set(res["season"]) == {2022}
    assert set(res["model"]) == set(registry())
    assert set(res["market"]) == set(STATS)
    assert res["p_over"].between(0, 1).all()
    assert np.isfinite(res["nll"]).all()


# ---------- Benter stages 2 and 3 ----------

def test_odds_conversion_and_devig():
    np.testing.assert_allclose(benter.american_to_decimal([-110, 150, 100]), [1 + 100 / 110, 2.5, 2.0])
    # -110 / -110: 4.76% margin, fair 50/50 under either method.
    assert benter.margin(-110, -110) == pytest.approx(2 * 110 / 210 - 1)
    for method in ["multiplicative", "power"]:
        assert benter.devig([-110], [-110], method)[0] == pytest.approx(0.5)
    # Lopsided market: both methods sum to 1 with the under, power shades the longshot more.
    mult = benter.devig([-200], [160], "multiplicative")[0]
    power = benter.devig([-200], [160], "power")[0]
    assert 0.6 < mult < 0.7 and power > mult


def test_market_blend_beats_model_and_market_when_both_carry_information():
    rng = np.random.default_rng(7)
    n = 40000
    z_true = rng.normal(0, 0.8, n)                       # true log-odds of the over
    p_true = benter.sigmoid(z_true)
    y = (rng.random(n) < p_true).astype(int)
    # The market sees most of the signal; the model sees some, with independent noise.
    p_market = benter.sigmoid(0.85 * z_true + rng.normal(0, 0.35, n))
    p_model = benter.sigmoid(0.6 * z_true + rng.normal(0, 0.6, n))
    tr, te = slice(0, n // 2), slice(n // 2, n)
    blend = benter.MarketBlend().fit(p_model[tr], p_market[tr], y[tr])
    p_final = blend.predict(p_model[te], p_market[te])

    def ll(p):
        p = np.clip(p, 1e-6, 1 - 1e-6)
        return -np.mean(y[te] * np.log(p) + (1 - y[te]) * np.log(1 - p))

    assert blend.a_ > 0 and blend.b_ > 0
    assert ll(p_final) < ll(p_market[te]) < ll(p_model[te])


def test_kelly_bets_only_with_edge_and_respects_cap():
    d = benter.american_to_decimal([-110, -110, -110])
    stakes = benter.kelly_fraction([0.50, 0.55, 0.90], d, fraction=0.25, cap=0.02)
    assert stakes[0] == 0.0                              # 50% at -110 is a losing bet
    assert 0 < stakes[1] < 0.02
    assert stakes[2] == pytest.approx(0.02)              # capped


def test_blend_backtest_runs_walk_forward_on_real_line_shape():
    rng = np.random.default_rng(3)
    rows = []
    for season in [2023, 2024, 2025]:
        z = rng.normal(0, 0.7, 3000)
        y = (rng.random(3000) < benter.sigmoid(z)).astype(int)
        fair = benter.sigmoid(0.8 * z + rng.normal(0, 0.4, 3000))
        # Price both sides with a ~4.5% margin.
        over_dec, under_dec = 1 / (fair * 1.045 / 1.0), 1 / ((1 - fair) * 1.045)
        to_am = lambda d: np.where(d >= 2, (d - 1) * 100, -100 / (d - 1))
        rows.append(pd.DataFrame({
            "season": season, "went_over": y,
            "p_model": benter.sigmoid(0.6 * z + rng.normal(0, 0.6, 3000)),
            "over_price": to_am(over_dec), "under_price": to_am(under_dec), "close_p_over": fair,
        }))
    bets, summary = benter.blend_backtest(pd.concat(rows), [2024, 2025])
    assert list(summary["season"]) == [2024, 2025]
    assert (summary["logloss_blend"] < summary["logloss_market"]).all()
    assert (bets["stake"] >= 0).all() and (bets["stake"] <= 0.02).all()


# ---------- Gemini price snapshot parser (fixture = real Gemini listing) ----------

def test_gemini_parser_keeps_only_priced_open_wnba_game_and_champion_contracts():
    import json
    import pathlib
    from oklahoma import gemini_prices

    payload = json.loads((pathlib.Path(__file__).parent / "fixtures" / "gemini_wnba_events.json").read_text())
    rows = gemini_prices.parse(payload, captured_at="2026-10-04T12:00:00+00:00")
    got = {(r["event_ticker"], r["contract_ticker"]) for r in rows}
    assert ("WNBA-2610042000-LVA-GSV-M", "GSV") in got and ("WNBA26CHAMP", "LVACES") in got
    assert not any(t == "WNBA26CHAMP" and c in ("DALWINGS", "MINNESOTA") for t, c in got)   # no price / closed
    assert not any(t == "WNBAMVP26" for t, _ in got)                                          # not a game or title market
    gsv = next(r for r in rows if r["contract_ticker"] == "GSV")
    assert (gsv["best_bid"], gsv["best_ask"], gsv["mid"], gsv["spread"]) == (0.48, 0.49, 0.485, 0.01)
    assert gsv["market_type"] == "moneyline" and len(rows) == 5
    # bare-list and 'events' shapes parse identically
    assert len(gemini_prices.parse(payload["data"])) == len(gemini_prices.parse({"events": payload["data"]})) == 5
    with pytest.raises(ValueError):
        gemini_prices.parse({"nope": 1})


def test_gemini_cli_saves_csv_and_reports_nothing_when_empty(tmp_path, capsys):
    import pathlib
    import sys
    from oklahoma import gemini_prices

    fx = pathlib.Path(__file__).parent / "fixtures" / "gemini_wnba_events.json"
    out = tmp_path / "prices.csv"
    sys.argv = ["x", "--from-file", str(fx), "--out", str(out)]
    assert gemini_prices.main() == 0 and "saved 5 prices" in capsys.readouterr().out
    assert gemini_prices.main() == 0                      # appends, header only once
    lines = out.read_text().strip().splitlines()
    assert len(lines) == 11 and lines[0].startswith("captured_at")
    empty = tmp_path / "empty.json"
    empty.write_text('{"data": []}')
    sys.argv = ["x", "--from-file", str(empty), "--out", str(tmp_path / "none.csv")]
    assert gemini_prices.main() == 0 and not (tmp_path / "none.csv").exists()


def test_calibration_recovers_overconfidence_and_leaves_other_markets_alone():
    from oklahoma import calibrate

    rng = np.random.default_rng(11)
    true_p = rng.uniform(0.2, 0.8, 60000)
    overconfident = benter.sigmoid(1.3 * benter.logit(true_p))            # pushes probabilities too far from 50%
    went_over = (rng.random(len(true_p)) < true_p).astype(int)
    a, b = calibrate.fit(overconfident, went_over)
    assert 0.65 < b < 0.85 and abs(a) < 0.08                              # 1/1.3 ~ 0.77
    fixed = calibrate.apply(overconfident, a, b)
    assert abs(fixed.mean() - went_over.mean()) < 0.01 and np.abs(fixed - true_p).mean() < np.abs(overconfident - true_p).mean()
    params = {"points": (a, b), "rebounds": (a, b)}
    assert calibrate.calibrate(0.73, "points", params) < 0.73             # pulled toward 50%
    assert calibrate.calibrate(0.73, "rebounds", params) == 0.73          # not in APPLY_TO
    assert calibrate.calibrate(0.73, "points", {}) == 0.73                # no params -> unchanged


def test_copula_recovers_correlation_and_margins():
    from oklahoma import joint
    rng = np.random.default_rng(0)
    true = np.array([[1, .5, .2], [.5, 1, .3], [.2, .3, 1]])
    mu, al = np.array([15., 5., 4.]), np.array([.1, .2, .3])
    d = joint.simulate(mu, al, true, 40000, rng)
    assert np.allclose(d.mean(0), mu, rtol=0.05)
    z = np.column_stack([joint.normal_scores(d[:, j], np.full(len(d), mu[j]), al[j], rng) for j in range(3)])
    assert np.abs(joint.fit_corr(z) - true).max() < 0.05
    indep = joint.simulate(mu, al, np.eye(3), 40000, rng)
    assert d[:, :2].sum(1).std() > indep[:, :2].sum(1).std()   # positive dependence widens the sum


def test_three_features_use_only_prior_games():
    from oklahoma import threes
    rng = np.random.default_rng(1)
    n = 40
    g = pd.DataFrame({"game_id": np.arange(n), "athlete_id": 1, "tip": pd.date_range("2025-06-01", periods=n, freq="2D", tz="UTC"),
                      "minutes": rng.uniform(15, 35, n), "threes_attempted": rng.integers(0, 9, n).astype(float)})
    g["threes_made"] = np.minimum(g["threes_attempted"], rng.integers(0, 5, n)).astype(float)
    base = threes.three_features(g)
    t = g.copy(); t.loc[25:, ["threes_made", "threes_attempted"]] += 7           # tamper with game 25 onward
    changed = threes.three_features(t)
    cols = ["att_pm_ewm", "mk_pm_ewm", "pct_shrunk"]
    pd.testing.assert_frame_equal(base.loc[:25, cols].reset_index(drop=True), changed.loc[:25, cols].reset_index(drop=True))
