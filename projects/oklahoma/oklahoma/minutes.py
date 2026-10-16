"""Quantile minutes model with a conformalized 80% band (CQR), using pregame inputs only.

Why it exists: minutes drive most of the big prop misses (a role cut, a returning starter).
The first version of this model (jobs/j06_minutes.py) read `starter`, the game's OWN box-score
flag, which is only known at tip. The honest stand-in is `starter_prev` (did she start her
previous game), built in oklahoma/features.py and the only starter signal used here.

Band: gradient-boosted p10/p50/p90 are nominal, not guaranteed. Conformalized quantile
regression (Romano, Patterson, Candes 2019) measures how far held-out games fall outside
[p10, p90] and widens (or narrows) the band by that amount so the 10-90 coverage is ~80%.
The held-out scores come from SEASON-GROUPED out-of-fold fits inside the training window
(fit on the other seasons, score the held-out one), so the shift reflects season-to-season
drift, not in-sample fit. Nothing from the season being predicted is ever touched.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

QUANTILES = (0.1, 0.5, 0.9)
COVERAGE = 0.8                      # target for the [p10, p90] band
MAX_MINUTES = 48.0
POS_COLS = ["pos_G", "pos_F", "pos_C"]
# `starter` (game-day flag) is deliberately absent. season_min_pg is optional (falls back to min_ewm).
FEATS = ["min_ewm", "min_l5", "starter_prev", "rest_days", "out_minutes", "is_home", "playoffs",
         "team_games_last7", "days_since_last", "returning", "career_games", "rookie", "pace_ratio",
         "season_min_pg"]


def design(df: pd.DataFrame) -> pd.DataFrame:
    """Numeric design matrix: FEATS plus G/F/C position dummies (first letter of the position)."""
    d = df if "season_min_pg" in df else df.assign(season_min_pg=df["min_ewm"])
    missing = [c for c in FEATS if c not in d] + (["athlete_position_abbreviation"] if "athlete_position_abbreviation" not in d else [])
    if missing:
        raise KeyError(f"minutes model needs columns {missing}")
    x = d[FEATS].astype(float)
    pos = d["athlete_position_abbreviation"].fillna("?").str[0]
    for c in POS_COLS:
        x[c] = (pos == c[-1]).astype(float)
    return x


class MinutesModel:
    """fit(train) / predict(df) -> DataFrame[min_p10, min_p50, min_p90].

    train needs `minutes`, `season` and the FEATS columns; predict needs the FEATS columns only.
    Hyperparameters match jobs/j06 (sklearn's default early stopping applies once a fit has more
    than 10k rows, as it did there). `max_iter` is exposed so tests and --quick runs can be fast.

    `seed` seeds the boosting (for these fits that is the random validation split early stopping
    holds out, so different seeds give slightly different models and band shifts); jobs/j06 averages
    several. `random_state` is the same thing under sklearn's name, kept for earlier callers.
    """

    def __init__(self, max_iter: int = 250, coverage: float = COVERAGE, seed: int = 0, random_state: int | None = None):
        self.max_iter, self.coverage = max_iter, coverage
        self.seed = seed if random_state is None else random_state

    def _gbm(self, q: float) -> HistGradientBoostingRegressor:
        return HistGradientBoostingRegressor(
            loss="quantile", quantile=q, max_iter=self.max_iter, learning_rate=0.06,
            max_leaf_nodes=15, l2_regularization=1.0, random_state=self.seed)

    def _band(self, models: dict, x: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """Raw (lo, hi) with crossing prevented."""
        a, b = models[QUANTILES[0]].predict(x), models[QUANTILES[-1]].predict(x)
        return np.minimum(a, b), np.maximum(a, b)

    def fit(self, train: pd.DataFrame) -> "MinutesModel":
        x, y = design(train), train["minutes"].to_numpy(float)
        seasons = train["season"].to_numpy()
        self.columns_ = list(x.columns)
        self.models_ = {q: self._gbm(q).fit(x, y) for q in QUANTILES}

        # CQR scores from season-grouped out-of-fold band fits (only p10 and p90 are needed).
        scores = []
        for s in np.unique(seasons):
            held = seasons == s
            if held.all():
                continue
            m = {q: self._gbm(q).fit(x[~held], y[~held]) for q in (QUANTILES[0], QUANTILES[-1])}
            lo, hi = self._band(m, x[held])
            scores.append(np.maximum(lo - y[held], y[held] - hi))     # >0 means outside the band
        if scores:
            e = np.concatenate(scores)
            # Finite-sample corrected level; the shift is negative when the raw band over-covers.
            level = min(1.0, np.ceil((len(e) + 1) * self.coverage) / len(e))
            self.shift_ = float(np.quantile(e, level, method="higher"))
            self.oof_raw_coverage_ = float((e <= 0).mean())
        else:                         # a single training season: no honest held-out scores exist
            self.shift_, self.oof_raw_coverage_ = 0.0, float("nan")
        self.n_oof_ = int(sum(len(s) for s in scores))
        return self

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        x = design(df)[self.columns_]
        lo, hi = self._band(self.models_, x)
        q = np.column_stack([lo - self.shift_, self.models_[0.5].predict(x), hi + self.shift_])
        q = np.clip(np.sort(q, axis=1), 0.0, MAX_MINUTES)     # sorted first: clipping keeps the order
        return pd.DataFrame(q, columns=["min_p10", "min_p50", "min_p90"], index=df.index)
