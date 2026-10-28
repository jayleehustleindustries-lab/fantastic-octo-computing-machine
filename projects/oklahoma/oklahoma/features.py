"""Pregame features for every market. Each value on a row uses only games that tipped before it.

Two kinds of inputs:
  * Box-score history (rates, minutes, form): strictly prior games.
  * Who is playing tonight (teammates out): known before tip from the official
    inactive list, so the game's own roster is allowed. Its box score is not.

tests/test_pipeline.py enforces this: changing a game's box score must not
change that game's features or any earlier game's.
"""
from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd

STATS = ["points", "rebounds", "assists", "pra"]
EWM_HALFLIFE = 5        # games
OPP_SHRINK = 150.0      # pseudo-minutes pulling opponent ratios toward league average
REST_CAP = 10           # days
ROTATION_MIN = 12.0     # recent minutes for a teammate to count when absent
ABSENCE_WINDOW = 5      # team games a missing rotation player keeps counting
COACHES_PATH = pathlib.Path(__file__).parent / "reference" / "coaches.csv"
TENURE_CAP = 100        # team games; coaches hired before 2015 start here
NEW_COACH_GAMES = 20    # first N games under a coach count as "new coach"


def _prior(grouped, col: str, fn) -> pd.Series:
    """Apply fn to each group's history shifted by one game (strictly prior)."""
    return grouped[col].transform(lambda s: fn(s.shift(1)))


def _team_schedule(g: pd.DataFrame) -> pd.DataFrame:
    """Per team-game: team game index, rest days, back-to-back, games in last 7 days."""
    tg = (
        g.groupby(["season", "game_id", "team_id"], as_index=False)
        .agg(tip=("tip", "min"))
        .sort_values(["team_id", "tip", "game_id"])
        .reset_index(drop=True)
    )
    by = tg.groupby(["team_id", "season"])
    tg["team_k"] = by.cumcount()
    rest = (tg["tip"] - by["tip"].shift(1)).dt.total_seconds() / 86400
    tg["rest_days"] = rest.round().clip(upper=REST_CAP).fillna(REST_CAP)
    tg["b2b"] = tg["rest_days"] <= 1

    def games_last7(s: pd.Series) -> pd.Series:
        secs = (s - s.iloc[0]).dt.total_seconds().to_numpy()
        lo = np.searchsorted(secs, secs - 7 * 86400, side="left")
        return pd.Series(np.arange(len(secs)) - lo, index=s.index)

    tg["team_games_last7"] = by["tip"].transform(games_last7)
    return tg[["game_id", "team_id", "team_k", "rest_days", "b2b", "team_games_last7"]]


def _teammates_out(g: pd.DataFrame) -> pd.DataFrame:
    """Recent production of rotation teammates missing from tonight's game.

    Candidates: anyone who played for the team in its previous ABSENCE_WINDOW
    games this season with recent minutes >= ROTATION_MIN. Their numbers are
    as of their last appearance (all before tonight).
    """
    post_cols = {f"post_{s}": s for s in STATS + ["minutes"]}
    by = g.groupby("athlete_id", sort=False)
    post = g[["team_id", "season", "team_k", "athlete_id", "game_id"]].copy()
    for name, col in post_cols.items():
        post[name] = by[col].transform(lambda s: s.ewm(halflife=EWM_HALFLIFE).mean())
    post = post[post["post_minutes"] >= ROTATION_MIN]

    cand = pd.concat(
        [post.assign(target_k=post["team_k"] + d) for d in range(1, ABSENCE_WINDOW + 1)],
        ignore_index=True,
    )
    cand = cand.sort_values("team_k").drop_duplicates(["team_id", "season", "target_k", "athlete_id"], keep="last")

    roster = g[["team_id", "season", "team_k", "athlete_id"]].rename(columns={"team_k": "target_k"})
    roster["present"] = True
    cand = cand.merge(roster, on=["team_id", "season", "target_k", "athlete_id"], how="left")
    absent = cand[cand["present"].isna()]

    out = (
        absent.groupby(["team_id", "season", "target_k"])[list(post_cols)].sum()
        .rename(columns=lambda c: c.replace("post_", "out_"))
        .reset_index()
        .rename(columns={"target_k": "team_k"})
    )
    return out


def load_coaches(path: pathlib.Path = COACHES_PATH) -> pd.DataFrame:
    """Head coach per team-season, with mid-season changes (from_game = first game coached)."""
    return pd.read_csv(path, dtype={"tenure_before_2015": "string", "note": "string"})


def _coach_tenure(g: pd.DataFrame, coaches: pd.DataFrame) -> pd.DataFrame:
    """Per team-game: consecutive team games under tonight's head coach before tonight.

    A coaching change is public before the new coach's first game, so this is pregame.
    Team-seasons missing from the table get coach_known = False and a neutral tenure.
    """
    tg = (
        g.groupby(["season", "game_id", "team_id"], as_index=False)
        .agg(tip=("tip", "min"), team_k=("team_k", "first"))
    )
    tg["game_no"] = (tg["team_k"] + 1).astype("int64")
    tg[["team_id", "season"]] = tg[["team_id", "season"]].astype("int64")
    c = coaches[["team_id", "season", "from_game", "coach", "tenure_before_2015"]].astype(
        {"team_id": "int64", "season": "int64", "from_game": "int64"}
    )
    tg = pd.merge_asof(
        tg.sort_values("game_no"), c.sort_values("from_game"),
        left_on="game_no", right_on="from_game", by=["team_id", "season"], direction="backward",
    )
    tg = tg.sort_values(["team_id", "tip", "game_id"]).reset_index(drop=True)
    tg["coach_known"] = tg["coach"].notna()
    coach = tg["coach"].fillna("UNMAPPED")
    new_run = coach.ne(coach.groupby(tg["team_id"]).shift())
    run = new_run.groupby(tg["team_id"]).cumsum()
    tenure = tg.groupby(["team_id", run]).cumcount()
    carried = tg.groupby(["team_id", run])["tenure_before_2015"].transform("first").eq("yes").fillna(False)
    tg["coach_tenure"] = (tenure + carried.astype(int) * TENURE_CAP).clip(upper=TENURE_CAP)
    tg.loc[~tg["coach_known"], "coach_tenure"] = TENURE_CAP
    tg["new_coach"] = tg["coach_tenure"] < NEW_COACH_GAMES
    out = tg[["game_id", "team_id", "coach", "coach_known", "coach_tenure", "new_coach"]]
    return out.astype({"team_id": g["team_id"].dtype})


def _defense_by_position(g: pd.DataFrame) -> pd.DataFrame:
    """Opponent's per-minute stat allowed to this position group, vs league, season to date."""
    d = g.assign(pos=g["athlete_position_abbreviation"].fillna("F"))
    allowed = (
        d.groupby(["season", "game_id", "opponent_team_id", "pos"], as_index=False)
        .agg(tip=("tip", "min"), minutes=("minutes", "sum"), **{s: (s, "sum") for s in STATS})
        .rename(columns={"opponent_team_id": "def_team"})
        .sort_values(["tip", "game_id"])
        .reset_index(drop=True)
    )
    by = allowed.groupby(["def_team", "season", "pos"])
    cum = by[["minutes"] + STATS].cumsum() - allowed[["minutes"] + STATS]

    allowed["date"] = allowed["tip"].dt.date
    daily = allowed.groupby(["season", "pos", "date"])[["minutes"] + STATS].sum().reset_index()
    daily_cum = daily.groupby(["season", "pos"])[["minutes"] + STATS].cumsum()
    daily_cum = daily_cum.groupby([daily["season"], daily["pos"]]).shift(1)
    daily[[f"lg_{c}" for c in ["minutes"] + STATS]] = daily_cum.to_numpy()
    allowed = allowed.merge(daily.drop(columns=["minutes"] + STATS), on=["season", "pos", "date"], how="left")

    out = allowed[["game_id", "def_team", "pos"]].copy()
    for s in STATS:
        team_rate = cum[s] / cum["minutes"]
        lg_rate = allowed[f"lg_{s}"] / allowed["lg_minutes"]
        ratio = (team_rate / lg_rate).replace([np.inf, -np.inf], np.nan).fillna(1.0)
        w = cum["minutes"].fillna(0)
        out[f"opp_{s}_ratio"] = (w * ratio + OPP_SHRINK) / (w + OPP_SHRINK)
    return out.rename(columns={"def_team": "opponent_team_id", "pos": "athlete_position_abbreviation"})


def _game_pace(g: pd.DataFrame) -> pd.DataFrame:
    """Expected game total: each team's recent combined score (theirs + opponent's), averaged
    for the two teams and scaled by the league's season-to-date average. Pregame only."""
    tg = (
        g.groupby(["season", "game_id", "team_id", "opponent_team_id"], as_index=False)
        .agg(tip=("tip", "min"), total=("team_score", "first"), opp_score=("opponent_team_score", "first"))
        .sort_values(["tip", "game_id"])
        .reset_index(drop=True)
    )
    tg["total"] = tg["total"] + tg["opp_score"]
    by = tg.groupby(["team_id", "season"])
    tg["total_ewm"] = by["total"].transform(lambda s: s.shift(1).ewm(halflife=EWM_HALFLIFE).mean())
    tg["date"] = tg["tip"].dt.date
    daily = tg.groupby(["season", "date"])["total"].agg(["sum", "count"]).reset_index()
    cum = daily.groupby("season")[["sum", "count"]].cumsum()
    cum = cum.groupby(daily["season"]).shift(1)
    daily["league_total"] = (cum["sum"] / cum["count"]).to_numpy()
    tg = tg.merge(daily[["season", "date", "league_total"]], on=["season", "date"], how="left")
    opp = tg[["game_id", "team_id", "total_ewm"]].rename(columns={"team_id": "opponent_team_id", "total_ewm": "opp_total_ewm"})
    tg = tg.merge(opp, on=["game_id", "opponent_team_id"], how="left")
    expected = tg[["total_ewm", "opp_total_ewm"]].mean(axis=1)
    tg["pace_ratio"] = (expected / tg["league_total"]).replace([np.inf, -np.inf], np.nan).fillna(1.0)
    return tg[["game_id", "team_id", "pace_ratio"]]


def build_features(games: pd.DataFrame, coaches: pd.DataFrame | None = None) -> pd.DataFrame:
    g = games.sort_values(["athlete_id", "tip", "game_id"]).reset_index(drop=True)
    if "pra" not in g:
        g["pra"] = g["points"] + g["rebounds"] + g["assists"]
    first_data_season = g["season"].min()

    sched = _team_schedule(g)
    g = g.merge(sched, on=["game_id", "team_id"], how="left")
    g = g.sort_values(["athlete_id", "tip", "game_id"]).reset_index(drop=True)

    by = g.groupby("athlete_id", sort=False)
    bs = g.groupby(["athlete_id", "season"], sort=False)
    g["career_games"] = by.cumcount()
    g["season_games"] = bs.cumcount()
    career_min = by["minutes"].cumsum() - g["minutes"]
    season_min = bs["minutes"].cumsum() - g["minutes"]
    g["season_min_pg"] = season_min / g["season_games"]
    g["min_l5"] = _prior(by, "minutes", lambda s: s.rolling(5, min_periods=1).mean())
    g["min_ewm"] = _prior(by, "minutes", lambda s: s.ewm(halflife=EWM_HALFLIFE).mean())
    # Whether she started her previous game. The game's own `starter` flag is only known at tip
    # (lineups are announced minutes before), so a minutes model must never read it; this is
    # the pregame-safe stand-in, and exactly what the slate projector can fill in.
    g["starter_prev"] = by["starter"].shift(1, fill_value=False).astype(bool)
    # Usage: shot attempts + trips to the line + turnovers per minute (possessions she ends).
    if {"field_goals_attempted", "free_throws_attempted", "turnovers"} <= set(g.columns):
        g["usage_load"] = g["field_goals_attempted"] + 0.44 * g["free_throws_attempted"] + g["turnovers"]
        load_ewm = _prior(by, "usage_load", lambda s: s.ewm(halflife=EWM_HALFLIFE).mean())
        g["usage_pm_ewm"] = load_ewm / g["min_ewm"]
    else:
        g["usage_pm_ewm"] = np.nan

    for s in STATS:
        g[f"career_{s}_pm"] = (by[s].cumsum() - g[s]) / career_min
        season_sum = bs[s].cumsum() - g[s]
        g[f"season_{s}_pg"] = season_sum / g["season_games"]
        g[f"season_{s}_pm"] = season_sum / season_min
        g[f"{s}_l5"] = _prior(by, s, lambda x: x.rolling(5, min_periods=1).mean())
        g[f"{s}_l10"] = _prior(by, s, lambda x: x.rolling(10, min_periods=1).mean())
        g[f"{s}_ewm"] = _prior(by, s, lambda x: x.ewm(halflife=EWM_HALFLIFE).mean())
        g[f"{s}_pm_ewm"] = g[f"{s}_ewm"] / g["min_ewm"]
        # Stand-in for the book's line: the recent average rounded to x.5.
        # NOT a real sportsbook line; real lines live in prop_lines.
        g[f"line_proxy_{s}"] = np.floor(g[f"{s}_ewm"]) + 0.5

    # Player availability: days since her last game, and returning after missing team games.
    prev_tip = by["tip"].shift(1)
    g["days_since_last"] = ((g["tip"] - prev_tip).dt.total_seconds() / 86400).clip(upper=30).fillna(30)
    prev_k = bs["team_k"].shift(1)
    same_team = g["team_id"].eq(bs["team_id"].shift(1))
    g["team_games_missed"] = (g["team_k"] - prev_k - 1).where(same_team).clip(lower=0).fillna(0)
    g["returning"] = g["team_games_missed"] >= 2

    first_season = by["season"].transform("min")
    g["rookie"] = g["season"].eq(first_season) & g["season"].gt(first_data_season)

    out = _teammates_out(g)
    g = g.merge(out, on=["team_id", "season", "team_k"], how="left")
    for c in [f"out_{s}" for s in STATS + ["minutes"]]:
        g[c] = g[c].fillna(0.0)

    coach = _coach_tenure(g, load_coaches() if coaches is None else coaches)
    g = g.merge(coach, on=["game_id", "team_id"], how="left")

    if {"team_score", "opponent_team_score"} <= set(g.columns):
        g = g.merge(_game_pace(g), on=["game_id", "team_id"], how="left")
    else:
        g["pace_ratio"] = 1.0
    g["pace_ratio"] = g["pace_ratio"].fillna(1.0)

    dpos = _defense_by_position(g)
    g = g.merge(dpos, on=["game_id", "opponent_team_id", "athlete_position_abbreviation"], how="left")
    for s in STATS:
        g[f"opp_{s}_ratio"] = g[f"opp_{s}_ratio"].fillna(1.0)

    # Backwards-compatible names used by the original rebound-only code and tests.
    g["reb_l10"], g["reb_ewm"], g["reb_pm_ewm"] = g["rebounds_l10"], g["rebounds_ewm"], g["rebounds_pm_ewm"]
    g["season_reb_pg"], g["season_reb_pm"] = g["season_rebounds_pg"], g["season_rebounds_pm"]
    g["career_reb_pm"], g["opp_reb_ratio"] = g["career_rebounds_pm"], g["opp_rebounds_ratio"]
    g["line_proxy"] = g["line_proxy_rebounds"]

    return g.sort_values(["tip", "game_id", "athlete_id"]).reset_index(drop=True)
