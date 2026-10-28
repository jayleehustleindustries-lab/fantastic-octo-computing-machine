"""Three-pointers made: features and a Poisson model. Same rules as the other markets: strictly prior games.

mean = f(expected minutes, recent 3PA per minute, shrunk 3P%). Adds the 3PM market the main model lacks.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor

from oklahoma.models import MU_FLOOR, Model

HALFLIFE = 8
LEAGUE_PCT_START = 0.32   # only used before any games exist
PCT_PRIOR_ATT = 40.0   # pseudo-attempts pulling 3P% toward the league rate


def three_features(games: pd.DataFrame) -> pd.DataFrame:
    """Per (game_id, athlete_id): prior EWM 3PA/min, prior EWM 3PM/min, prior shrunk 3P%, prior career 3PA/game."""
    g = games.sort_values(["athlete_id", "tip", "game_id"]).reset_index(drop=True)
    mins = g["minutes"].clip(lower=1)
    g["_att_pm"] = g["threes_attempted"] / mins
    g["_mk_pm"] = g["threes_made"] / mins
    by = g.groupby("athlete_id", sort=False)
    prior_ewm = lambda col: by[col].transform(lambda s: s.shift(1).ewm(halflife=HALFLIFE, min_periods=1).mean())
    g["att_pm_ewm"], g["mk_pm_ewm"] = prior_ewm("_att_pm"), prior_ewm("_mk_pm")
    cum_att = by["threes_attempted"].cumsum() - g["threes_attempted"]
    cum_mk = by["threes_made"].cumsum() - g["threes_made"]
    # League 3P% from games strictly before this one (a whole-data constant would leak the future).
    per_game = g.groupby("game_id").agg(tip=("tip", "min"), mk=("threes_made", "sum"), att=("threes_attempted", "sum")).sort_values("tip")
    league = ((per_game["mk"].cumsum() - per_game["mk"]) / (per_game["att"].cumsum() - per_game["att"]).replace(0, np.nan))
    g["_league"] = g["game_id"].map(league).fillna(LEAGUE_PCT_START)
    g["pct_shrunk"] = (cum_mk + PCT_PRIOR_ATT * g["_league"]) / (cum_att + PCT_PRIOR_ATT)
    g["att_pg_career"] = (cum_att / by.cumcount().replace(0, np.nan))
    return g[["game_id", "athlete_id", "att_pm_ewm", "mk_pm_ewm", "pct_shrunk", "att_pg_career"]]


class ThreesModel(Model):
    """Poisson GLM for 3PM with per-fifth negative-binomial dispersion.

    Subclasses models.Model so fit() fits the mean, then a separate dispersion for each fifth of
    the predicted mean (alpha_for(mu)). One pooled alpha, dominated by low-volume shooters, made
    high-volume shooters' distributions too wide, exactly the flaw fixed for the other markets.
    `alpha_` stays the pooled value (kept for reference and for jobs/j04_threes.py).
    """
    name = "threes_glm"

    def __init__(self, stat: str = "threes_made"):
        super().__init__(stat)
        self.glm = PoissonRegressor(alpha=1e-4, max_iter=1000)

    def _X(self, df):
        att = df["att_pm_ewm"].fillna(self.att_fill_)
        mk = df["mk_pm_ewm"].fillna(self.mk_fill_)
        mn = df["min_ewm"].fillna(self.min_fill_).clip(lower=1)
        return np.column_stack([
            np.log((att * mn).clip(lower=0.02)), np.log((mk * mn).clip(lower=0.02)),
            np.log(df["pct_shrunk"].fillna(0.3).clip(lower=0.02)), np.log(mn),
            df["is_home"].astype(float), df["playoffs"].astype(float), np.log(df["pace_ratio"].clip(lower=0.5)),
            np.log1p(df["out_minutes"]),
        ])

    def _fit_mean(self, train):
        self.att_fill_, self.mk_fill_ = train["att_pm_ewm"].median(), train["mk_pm_ewm"].median()
        self.min_fill_ = train["min_ewm"].median()
        X = self._X(train)
        self.m_, self.s_ = X.mean(0), X.std(0) + 1e-9
        self.glm.fit((X - self.m_) / self.s_, train[self.stat])

    def predict_mean(self, df):
        return np.maximum(self.glm.predict((self._X(df) - self.m_) / self.s_), MU_FLOOR)
