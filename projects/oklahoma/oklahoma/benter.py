"""Benter stages 2 and 3: blend the model with the market, then size bets.

Follows Bill Benter (1994), "Computer Based Horse Race Handicapping and
Wagering Systems: A Report":
  * Stage 1 (models.py) gives a fundamental probability from public data.
  * Stage 2 combines it with the market's own probability:
        logit(p_final) = c + a * logit(p_model) + b * logit(p_market)
    with a, b, c fit on past games. The market carries information the model
    lacks; Benter's fundamental model alone was not profitable, the blend was.
  * Stage 3 stakes a fraction of the Kelly criterion on the blended edge.

Prop markets are two-way (over/under), so the market probability is the
de-vigged over price.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import optimize

EPS = 1e-6


# ---------- odds ----------

def american_to_decimal(odds) -> np.ndarray:
    o = np.asarray(odds, dtype=float)
    return np.where(o > 0, 1 + o / 100, 1 + 100 / np.abs(o))


def implied_prob(odds) -> np.ndarray:
    """Raw implied probability of American odds, margin included."""
    return 1 / american_to_decimal(odds)


def devig(over_odds, under_odds, method: str = "power") -> np.ndarray:
    """Fair P(over) from a two-way market.

    multiplicative: scale both sides so they sum to 1.
    power: find k with p_over**k + p_under**k = 1. Puts more of the margin on
           the longshot side, which tends to match how books shade prices.
    """
    po, pu = implied_prob(over_odds), implied_prob(under_odds)
    if method == "multiplicative":
        return po / (po + pu)
    if method != "power":
        raise ValueError(f"unknown method {method!r}")

    def solve(a: float, b: float) -> float:
        if not (np.isfinite(a) and np.isfinite(b)):
            return np.nan
        k = optimize.brentq(lambda k: a**k + b**k - 1, 0.5, 5.0)
        return a**k

    return np.array([solve(a, b) for a, b in zip(np.atleast_1d(po), np.atleast_1d(pu))])


def margin(over_odds, under_odds) -> np.ndarray:
    """The book's margin (vig): how far the two implied probabilities exceed 1."""
    return implied_prob(over_odds) + implied_prob(under_odds) - 1


# ---------- stage 2: market blend ----------

def logit(p) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def sigmoid(x) -> np.ndarray:
    return 1 / (1 + np.exp(-np.asarray(x, dtype=float)))


class MarketBlend:
    """logit(p) = c + a*logit(p_model) + b*logit(p_market), fit by maximum likelihood."""

    def fit(self, p_model, p_market, went_over) -> "MarketBlend":
        X = np.column_stack([np.ones(len(p_model)), logit(p_model), logit(p_market)])
        y = np.asarray(went_over, dtype=float)

        def nll(w):
            z = X @ w
            return np.sum(np.logaddexp(0, z) - y * z)

        def grad(w):
            return X.T @ (sigmoid(X @ w) - y)

        res = optimize.minimize(nll, x0=np.array([0.0, 0.0, 1.0]), jac=grad, method="BFGS")
        self.c_, self.a_, self.b_ = res.x
        return self

    def predict(self, p_model, p_market) -> np.ndarray:
        return sigmoid(self.c_ + self.a_ * logit(p_model) + self.b_ * logit(p_market))


# ---------- stage 3: sizing ----------

def kelly_fraction(p, decimal_odds, fraction: float = 0.25, cap: float = 0.02) -> np.ndarray:
    """Share of bankroll to stake. Full Kelly is (p*d - 1) / (d - 1); we bet a
    fraction of it and cap any single bet. Zero when there is no edge."""
    p = np.asarray(p, dtype=float)
    d = np.asarray(decimal_odds, dtype=float)
    full = (p * d - 1) / (d - 1)
    return np.clip(fraction * full, 0.0, cap)


def best_side(p_over, over_odds, under_odds) -> pd.DataFrame:
    """For each row, the side with the larger expected value per unit staked."""
    d_over, d_under = american_to_decimal(over_odds), american_to_decimal(under_odds)
    p_over = np.asarray(p_over, dtype=float)
    ev_over = p_over * d_over - 1
    ev_under = (1 - p_over) * d_under - 1
    take_over = ev_over >= ev_under
    return pd.DataFrame({
        "side": np.where(take_over, "over", "under"),
        "p_win": np.where(take_over, p_over, 1 - p_over),
        "decimal_odds": np.where(take_over, d_over, d_under),
        "ev": np.where(take_over, ev_over, ev_under),
    })


# ---------- evaluation once real lines exist ----------

def blend_backtest(rows: pd.DataFrame, test_seasons: list[int], min_ev: float = 0.02,
                   kelly: float = 0.25, cap: float = 0.02) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Walk-forward stage 2 + 3 on rows that have a real line.

    rows needs: season, p_model, over_price, under_price, went_over
    (optionally close_p_over: de-vigged closing P(over), for closing-line value).
    Returns (per-bet rows, per-season summary).
    """
    rows = rows.dropna(subset=["p_model", "over_price", "under_price"]).copy()
    rows["p_market"] = devig(rows["over_price"], rows["under_price"])
    out = []
    for season in test_seasons:
        train = rows[rows["season"] < season]
        test = rows[rows["season"] == season].copy()
        if len(train) < 200 or test.empty:
            continue
        blend = MarketBlend().fit(train["p_model"], train["p_market"], train["went_over"])
        test["p_final"] = blend.predict(test["p_model"], test["p_market"])
        test["blend_a"], test["blend_b"] = blend.a_, blend.b_
        pick = best_side(test["p_final"], test["over_price"], test["under_price"])
        test = pd.concat([test.reset_index(drop=True), pick], axis=1)
        test["stake"] = np.where(
            test["ev"] >= min_ev, kelly_fraction(test["p_win"], test["decimal_odds"], kelly, cap), 0.0
        )
        won = np.where(test["side"] == "over", test["went_over"] == 1, test["went_over"] == 0)
        test["profit"] = np.where(won, test["stake"] * (test["decimal_odds"] - 1), -test["stake"])
        if "close_p_over" in test:
            close_p_side = np.where(test["side"] == "over", test["close_p_over"], 1 - test["close_p_over"])
            test["clv"] = close_p_side * test["decimal_odds"] - 1
        out.append(test)
    bets = pd.concat(out, ignore_index=True) if out else pd.DataFrame()
    if bets.empty:
        return bets, pd.DataFrame()

    def logloss(p, y):
        p = np.clip(p, EPS, 1 - EPS)
        return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))

    summary = []
    for season, b in bets.groupby("season"):
        placed = b[b["stake"] > 0]
        summary.append({
            "season": season,
            "rows": len(b),
            "logloss_market": logloss(b["p_market"], b["went_over"]),
            "logloss_model": logloss(b["p_model"], b["went_over"]),
            "logloss_blend": logloss(b["p_final"], b["went_over"]),
            "blend_a": b["blend_a"].iloc[0],
            "blend_b": b["blend_b"].iloc[0],
            "bets": len(placed),
            "staked": placed["stake"].sum(),
            "profit": placed["profit"].sum(),
            "roi": placed["profit"].sum() / placed["stake"].sum() if len(placed) else np.nan,
            "avg_clv": placed["clv"].mean() if "clv" in placed and len(placed) else np.nan,
        })
    return bets, pd.DataFrame(summary)
