"""Joint distribution of points, rebounds and assists for one player-game (Gaussian copula).

Why: combo props (P+R, P+A, R+A) were priced by adding independent distributions. Stats of one player in
one game are correlated (minutes, pace, usage move them together), so independence misstates the spread
of the sum. A copula keeps each stat's own negative-binomial margin and adds the dependence.
"""
from __future__ import annotations

import json
import pathlib

import numpy as np
from scipy import stats

CORR_PATH = pathlib.Path(__file__).resolve().parent.parent / "reports" / "copula.json"


def _cdf_pair(y, mu, alpha):
    """P(Y<=y-1) and P(Y<=y) for Poisson (alpha~0) or NB with mean mu."""
    y = np.asarray(y, dtype=float); mu = np.asarray(mu, dtype=float); alpha = np.broadcast_to(np.asarray(alpha, dtype=float), mu.shape)
    lo, hi = np.empty_like(mu), np.empty_like(mu)
    pois = alpha <= 1e-8
    lo[pois], hi[pois] = stats.poisson.cdf(y[pois] - 1, mu[pois]), stats.poisson.cdf(y[pois], mu[pois])
    n = 1.0 / np.maximum(alpha[~pois], 1e-6); p = n / (n + mu[~pois])
    lo[~pois], hi[~pois] = stats.nbinom.cdf(y[~pois] - 1, n, p), stats.nbinom.cdf(y[~pois], n, p)
    return lo, hi


def normal_scores(y, mu, alpha, rng) -> np.ndarray:
    """Randomized probability-integral transform -> standard normal scores (exact under a correct model)."""
    lo, hi = _cdf_pair(y, mu, alpha)
    u = np.clip(lo + rng.random(len(lo)) * (hi - lo), 1e-6, 1 - 1e-6)
    return stats.norm.ppf(u)


def fit_corr(z: np.ndarray) -> np.ndarray:
    """z: (rows, k) normal scores -> k x k correlation matrix (made positive definite)."""
    c = np.corrcoef(z, rowvar=False)
    w, v = np.linalg.eigh(c); w = np.clip(w, 1e-4, None)
    c = (v * w) @ v.T
    d = np.sqrt(np.diag(c)); return c / np.outer(d, d)


def simulate(mu, alpha, corr, n: int, rng) -> np.ndarray:
    """mu, alpha: length-k. Returns (n, k) integer draws with NB margins and the given dependence."""
    mu = np.asarray(mu, dtype=float); alpha = np.broadcast_to(np.asarray(alpha, dtype=float), mu.shape)
    L = np.linalg.cholesky(corr)
    u = stats.norm.cdf(rng.standard_normal((n, len(mu))) @ L.T)
    out = np.empty((n, len(mu)))
    for j in range(len(mu)):
        if alpha[j] <= 1e-8:
            out[:, j] = stats.poisson.ppf(u[:, j], mu[j])
        else:
            nn = 1.0 / alpha[j]; out[:, j] = stats.nbinom.ppf(u[:, j], nn, nn / (nn + mu[j]))
    return out


def save(corr_by_group: dict[str, np.ndarray], path=CORR_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({k: np.asarray(v).round(4).tolist() for k, v in corr_by_group.items()}, indent=1))


def load(path=CORR_PATH) -> dict[str, np.ndarray] | None:
    if not path.exists():
        return None
    return {k: np.array(v) for k, v in json.loads(path.read_text()).items()}
