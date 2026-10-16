"""Rebound models. Each predicts a full count distribution, not just a number.

Every model predicts a mean, then fits negative-binomial dispersion on its own
training residuals (variance = mu + alpha * mu^2; alpha = 0 is Poisson).
Dispersion is fit separately for each fifth of predicted means: one pooled value,
dominated by low-minute players, made stars' distributions far too wide.
That gives P(rebounds > line) for any line.

Dispersion is fit in-sample by default (misses season-to-season drift, so over/under
probabilities come out overconfident). Set `oos_alpha = True` on a subclass to fit it on the
training window's LAST season instead, using a mean fit on the seasons before it.

Every model is built for one market (stat): points, rebounds, assists or pra.
To add a model: subclass Model, implement _fit_mean and predict_mean, and add
it to registry().
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import optimize, stats
from sklearn.linear_model import PoissonRegressor

MU_FLOOR = 0.05


# ---------- distribution helpers ----------

def _nb_params(mu: np.ndarray, alpha):
    n = 1.0 / np.maximum(np.asarray(alpha, dtype=float), 1e-6)
    return n, n / (n + mu)


def log_pmf(y: np.ndarray, mu: np.ndarray, alpha) -> np.ndarray:
    """alpha may be a scalar or one value per row."""
    if np.all(np.asarray(alpha) <= 1e-8):
        return stats.poisson.logpmf(y, mu)
    n, p = _nb_params(mu, alpha)
    return stats.nbinom.logpmf(y, n, p)


def prob_over(line: np.ndarray, mu: np.ndarray, alpha) -> np.ndarray:
    """P(Y > line). For a .5 line this is P(Y >= ceil(line))."""
    k = np.floor(line)
    if np.all(np.asarray(alpha) <= 1e-8):
        return stats.poisson.sf(k, mu)
    n, p = _nb_params(mu, alpha)
    return stats.nbinom.sf(k, n, p)


def fit_alpha(y: np.ndarray, mu: np.ndarray) -> float:
    """MLE of the NB dispersion given fixed means. Returns 0 if Poisson fits better."""
    def nll(log_a: float) -> float:
        return -log_pmf(y, mu, float(np.exp(log_a))).sum()

    res = optimize.minimize_scalar(nll, bounds=(-8, 2), method="bounded")
    poisson_nll = -log_pmf(y, mu, 0.0).sum()
    return float(np.exp(res.x)) if res.fun < poisson_nll else 0.0


# ---------- models ----------

class Model:
    name = "base"
    oos_alpha = False        # True: fit dispersion out-of-sample (see _oos_pairs)
    has_starter_terms = False   # True: the design reads starter_prev, so it models the starter/bench role itself

    def __init__(self, stat: str = "rebounds"):
        self.stat = stat

    def col(self, template: str) -> str:
        return template.format(s=self.stat)

    def fit(self, train: pd.DataFrame) -> "Model":
        y = train[self.stat]
        self.league_pm_ = float(y.sum() / train["minutes"].sum())
        self.league_pg_ = float(y.mean())
        self.league_min_pg_ = float(train["minutes"].mean())
        self._fit_mean(train)
        yv = y.to_numpy()
        pairs = self._oos_pairs(train) if self.oos_alpha else None
        self.alpha_source_ = "out_of_sample" if pairs is not None else "in_sample"
        y_a, mu_a = pairs if pairs is not None else (yv, self.predict_mean(train))
        self.alpha_ = fit_alpha(y_a, mu_a)                    # pooled, kept for reference
        self.alpha_edges_ = np.quantile(mu_a, [0.2, 0.4, 0.6, 0.8])
        bins = np.digitize(mu_a, self.alpha_edges_)
        self.alpha_bins_ = np.array([
            fit_alpha(y_a[bins == b], mu_a[bins == b]) if (bins == b).sum() >= 200 else self.alpha_
            for b in range(5)
        ])
        return self

    def _oos_pairs(self, train: pd.DataFrame):
        """(actual, predicted mean) for the training window's last season, predicted by a fresh
        copy of this model fit only on the seasons before it. In-sample residuals are too small
        (the mean was fit on them), so dispersion fit there understates season-to-season drift.
        Returns None, falling back to in-sample, when the window has a single season."""
        last = train["season"].max()
        inner, held = train[train["season"] < last], train[train["season"] == last]
        if inner.empty or held.empty:
            return None
        assert inner["season"].max() < held["season"].min(), "inner fit leaked into the held-out season"
        m = type(self)(self.stat)
        m.oos_alpha = False
        m.fit(inner)
        return held[self.stat].to_numpy(), m.predict_mean(held)

    def alpha_for(self, mu: np.ndarray) -> np.ndarray:
        """Dispersion for each predicted mean, by fifth of the training means."""
        return self.alpha_bins_[np.digitize(np.asarray(mu, dtype=float), self.alpha_edges_)]

    def _fit_mean(self, train: pd.DataFrame) -> None:
        pass

    def predict_mean(self, df: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError

    def _floor(self, mu: pd.Series) -> np.ndarray:
        return np.maximum(mu.fillna(self.league_pg_).to_numpy(dtype=float), MU_FLOOR)


class SeasonAverage(Model):
    """Season-to-date per-game average; career rate x recent minutes early on."""
    name = "season_avg"

    def predict_mean(self, df):
        early = df["season_games"] < 3
        career_guess = df[self.col("career_{s}_pm")] * df["min_ewm"]
        return self._floor(df[self.col("season_{s}_pg")].where(~early, career_guess))


class Last10(Model):
    """Average of the last 10 games, any season."""
    name = "last10"

    def predict_mean(self, df):
        return self._floor(df[self.col("{s}_l10")])


class RateTimesMinutes(Model):
    """Recent per-minute rate times recent minutes."""
    name = "rate_x_minutes"

    def predict_mean(self, df):
        return self._floor(df[self.col("{s}_pm_ewm")].fillna(self.league_pm_) * df["min_ewm"])


class ContextGLM(Model):
    """Poisson regression on log rates, log minutes and game context (Benter stage 1)."""
    name = "context_glm"

    def _log_rate(self, df, template):
        return np.log(df[self.col(template)].fillna(self.league_pm_).clip(lower=0.005))

    def _design(self, df: pd.DataFrame) -> np.ndarray:
        min_ewm = df["min_ewm"].fillna(self.league_min_pg_)
        rest = df["rest_days"].fillna(3)
        return np.column_stack([
            self._log_rate(df, "{s}_pm_ewm"),
            self._log_rate(df, "season_{s}_pm"),
            self._log_rate(df, "career_{s}_pm"),
            np.log(min_ewm.clip(lower=1)),
            np.log(df["min_l5"].fillna(min_ewm).clip(lower=1)),
            np.log(df[self.col("opp_{s}_ratio")]),
            df["is_home"].astype(float),
            df["playoffs"].astype(float),
            df["rookie"].astype(float),
            (rest <= 1).astype(float),
            np.log1p(df["career_games"]),
        ])

    def _fit_mean(self, train):
        X = self._design(train)
        self.mean_ = X.mean(axis=0)
        self.std_ = X.std(axis=0) + 1e-9
        self.glm_ = PoissonRegressor(alpha=1e-4, max_iter=1000)
        self.glm_.fit((X - self.mean_) / self.std_, train[self.stat])

    def predict_mean(self, df):
        X = (self._design(df) - self.mean_) / self.std_
        return np.maximum(self.glm_.predict(X), MU_FLOOR)


PLUS_FEATURES = [
    "teammates_out_minutes", "teammates_out_stat", "team_games_last7",
    "returning", "days_since_last", "hot_streak",
]
# coach_tenure / new_coach were tested (Oct 2026 ablation, 2021-2026 folds) and moved
# nll by less than +/-0.0003 in every market and season, so they stay out of the model.


class ContextGLMPlus(ContextGLM):
    """context_glm + teammates out, schedule load, return from absence, hot streak.

    Compared against context_glm in the backtest, so each addition has to earn
    its place on out-of-sample data.
    """
    name = "context_glm_plus"

    def _design(self, df):
        base = super()._design(df)
        ewm = df[self.col("{s}_ewm")].fillna(self.league_pg_).clip(lower=0.1)
        hot = np.log(df[self.col("{s}_l5")].fillna(ewm).clip(lower=0.1) / ewm)
        return np.column_stack([
            base,
            np.log1p(df["out_minutes"]),
            np.log1p(df[self.col("out_{s}")]),
            df["team_games_last7"].astype(float),
            df["returning"].astype(float),
            np.log(df["days_since_last"].clip(lower=0.5)),
            hot,
        ])


class ContextGLMPlus2(ContextGLMPlus):
    """context_glm_plus + usage (possessions used per minute) + expected game pace."""
    name = "context_glm_plus2"

    def fit(self, train):
        med = train["usage_pm_ewm"].median()
        self.usage_fill_ = float(med) if pd.notna(med) else 0.5   # from training data only
        return super().fit(train)

    def _design(self, df):
        usage = df["usage_pm_ewm"].fillna(self.usage_fill_)
        return np.column_stack([
            super()._design(df),
            np.log(usage.clip(lower=0.05)),
            np.log(df["pace_ratio"].clip(lower=0.5)),
        ])


class ContextGLMPlus2O(ContextGLMPlus2):
    """context_glm_plus2 with out-of-sample dispersion: identical mean model, only alpha is fit on the last
    training season (see Model._oos_pairs). REJECTED in the v3 backtest (calibration slope did not move toward 1 and
    nll was worse than plus2 in all four markets, COMPUTE_PLAN.md); kept so that run can be reproduced."""
    name = "context_glm_plus2o"
    oos_alpha = True


class ContextGLMPlus2S(ContextGLMPlus2O):
    """plus2o + the previous-game starter flag and its playoff interaction.

    Playoff rotations tighten: the model under-projected starters and over-projected bench
    players (by starter_prev, points +0.77 / -0.94, PRA +1.20 / -1.66). `playoffs` is already in
    the design, so it carries the bench playoff effect; starter_prev and starter_prev*playoffs
    let starters differ. The two columns are appended after plus2's, so its indices are unchanged.
    Not adopted: plus2si has this mean model with plus2's in-sample dispersion and is at least as good.
    """
    name = "context_glm_plus2s"
    has_starter_terms = True

    def _design(self, df):
        sp = df["starter_prev"].astype(float)
        return np.column_stack([super()._design(df), sp, sp * df["playoffs"].astype(float)])


class ContextGLMPlus2SI(ContextGLMPlus2S):
    """plus2 + the previous-game starter terms of plus2s, with plus2's in-sample dispersion.

    Splits plus2s into its two changes: the starter_prev terms (a mean-model change) and
    out-of-sample alpha (a spread change, rejected for plus2o). It inherits plus2s's design, so the
    starter columns are the same code and the same last two columns after plus2's, and only turns
    `oos_alpha` back off. Compared against plus2 in the v3 backtest.
    """
    name = "context_glm_plus2si"
    oos_alpha = False


def alpha_method(model_cls: type[Model]) -> str:
    """How `model_cls` fits dispersion, in words (recorded in calibration.json's _meta)."""
    if model_cls.oos_alpha:
        return ("out_of_sample: dispersion fit on the training window's last season, mean fit on the seasons "
                "before it, then refit on the full window")
    return "in_sample: dispersion fit per fifth of the predicted mean on the training window's own residuals"


PRODUCTION_MODEL = "context_glm_plus2si"   # what project.py, compare.py and backtest.py use unless told otherwise


def registry() -> dict[str, type[Model]]:
    return {m.name: m for m in [SeasonAverage, Last10, RateTimesMinutes, ContextGLM, ContextGLMPlus, ContextGLMPlus2,
                                ContextGLMPlus2O, ContextGLMPlus2S, ContextGLMPlus2SI]}
