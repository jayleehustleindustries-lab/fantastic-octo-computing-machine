"""Probability recalibration: p' = sigmoid(a + b * logit(p)), fit per market.

Backtest finding (walk-forward, 2023-2026): the model's over/under probabilities are
overconfident for points and PRA (fitted slope b ~ 0.8, intercept ~ 0): lopsided calls
(e.g. 73%) should be pulled toward 50%. Applying the map trained only on earlier seasons
improved log loss in 14 of 16 market-seasons, mostly points and PRA. Rebounds and assists
showed no reliable gain at first. Oct 9 2026 re-check on context_glm_plus2's rows (walk-forward 2022-26,
game-clustered bootstrap slope 0.84): assists improved in 4 of 5 held-out seasons. Oct 10 2026, on the
production model context_glm_plus2si, the rule below kept POINTS ONLY (PRA 4 of 5 but pooled +0.0009 <
MIN_POOLED; assists and rebounds 3 of 5), which is what reports/calibration.json's _meta.apply_to says.
The APPLY_TO constant (points, pra, assists) is only the fallback for older files without _meta.

Which markets are calibrated: a calibration file may carry a "_meta" block (model, alpha_method,
fit_seasons, n, apply_to), written by backtest.py / jobs/j08_v3_eval.py from the rule below. When the
file has `apply_to`, that list decides (it was measured for that file's model); the module constant
APPLY_TO is only the fallback for older files without it.

The map belongs to the model it was fit on. A caller that names the model producing the probabilities
(effective_apply_to(model=...) / calibrate(..., model=...); project.py and compare.py always do) gets
NO calibration, plus a CalibrationModelMismatch warning, when the file's `_meta.model` names a different
model. compare.py then flags those rows UNCALIBRATED. Files without `_meta.model` cannot be checked and
keep the old behaviour.

The rule (fit_by_rule): for each market, fit on seasons < s and score season s, for every season after
the first; keep the market only if log loss improves in >= MIN_SEASONS held-out seasons AND the pooled
gain is >= MIN_POOLED nats per row.
"""
from __future__ import annotations

import json
import pathlib
import warnings

import numpy as np
from scipy import optimize

PATH = pathlib.Path(__file__).resolve().parent.parent / "reports" / "calibration.json"
APPLY_TO = ("points", "pra", "assists")      # fallback for calibration files without _meta.apply_to
EPS = 1e-4
MIN_SEASONS = 4              # the rule: improve log loss in at least this many held-out seasons ...
MIN_POOLED = 0.001           # ... and by at least this much per row, pooled over them


def _logit(p):
    p = np.clip(np.asarray(p, dtype=float), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def _sigmoid(z):
    return 1 / (1 + np.exp(-np.asarray(z, dtype=float)))


def fit(p, went_over) -> tuple[float, float]:
    """Maximum-likelihood (a, b) for p' = sigmoid(a + b*logit(p))."""
    X = np.column_stack([np.ones(len(p)), _logit(p)])
    y = np.asarray(went_over, dtype=float)
    nll = lambda w: np.sum(np.logaddexp(0, X @ w) - y * (X @ w))
    grad = lambda w: X.T @ (_sigmoid(X @ w) - y)
    a, b = optimize.minimize(nll, [0.0, 1.0], jac=grad, method="BFGS").x
    return float(a), float(b)


def apply(p, a: float, b: float):
    return _sigmoid(a + b * _logit(p))


META_KEY = "_meta"        # provenance block in a calibration file; never a market


def save(params: dict[str, tuple[float, float]], path: pathlib.Path | None = None, meta: dict | None = None) -> None:
    """Write {market: {a, b}}; `meta` (model, alpha_method, fit_seasons, n, apply_to) goes under "_meta".
    `path` defaults to PATH, looked up at call time (like load), so tests can redirect the module's file."""
    path = pathlib.Path(PATH if path is None else path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = {m: {"a": a, "b": b} for m, (a, b) in params.items()}
    if meta is not None:
        out[META_KEY] = meta
    path.write_text(json.dumps(out, indent=1))


def load(path: pathlib.Path | None = None) -> dict[str, tuple[float, float]]:
    """{market: (a, b)}. The "_meta" provenance block is not a market and is skipped."""
    path = pathlib.Path(PATH if path is None else path)
    if not path.exists():
        return {}
    return {m: (v["a"], v["b"]) for m, v in json.loads(path.read_text()).items() if m != META_KEY}


def load_meta(path: pathlib.Path | None = None) -> dict:
    """The "_meta" block of a calibration file ({} if absent), e.g. its own apply_to list."""
    path = pathlib.Path(PATH if path is None else path)
    return json.loads(path.read_text()).get(META_KEY, {}) if path.exists() else {}


class CalibrationModelMismatch(UserWarning):
    """The calibration file was fit on a different model's probabilities than the ones being calibrated."""


def effective_apply_to(path: pathlib.Path | None = None, model: str | None = None) -> tuple[str, ...]:
    """Markets to calibrate: the file's own `_meta.apply_to` when it has one, else the APPLY_TO fallback.

    `model` = the model producing the probabilities. If the file's `_meta.model` names another model the
    answer is () (calibrate nothing) and a CalibrationModelMismatch warning is emitted. model=None, or a
    file without `_meta.model`, skips the check."""
    meta = load_meta(path)
    fit_for = meta.get("model")
    if model is not None and fit_for is not None and fit_for != model:
        warnings.warn(f"calibration file was fit on {fit_for!r} probabilities, not {model!r}: "
                      "leaving every market uncalibrated", CalibrationModelMismatch, stacklevel=2)
        return ()
    return tuple(meta["apply_to"]) if "apply_to" in meta else APPLY_TO


def calibrate(p, market: str, params: dict | None = None, apply_to=None, model: str | None = None):
    """Calibrated probability if `market` is to be calibrated and has parameters, else p unchanged.

    With no `params` the production file is used, together with its own `_meta.apply_to` (and, when
    `model` is given, only if the file was fit for that model). Explicit `params` fall back to the
    APPLY_TO constant unless `apply_to` is given (callers that loaded the file themselves pass
    `effective_apply_to(model=...)`)."""
    if params is None:
        params = load()
        apply_to = effective_apply_to(model=model) if apply_to is None else apply_to
    elif apply_to is None:
        apply_to = APPLY_TO
    if market in apply_to and market in params:
        return apply(p, *params[market])
    return np.asarray(p, dtype=float)


# ---------- the keep-or-drop rule ----------

def logloss(p, went_over):
    """Per-row binary log loss (probabilities clipped to [1e-6, 1 - 1e-6])."""
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    y = np.asarray(went_over, dtype=float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def walk_forward_check(p, went_over, season) -> dict:
    """Does the map help out of sample? Fit on seasons < s, apply to s, for each season after the first.

    Returns per-season log-loss gains (raw minus calibrated; positive = the map helped), how many
    seasons improved, the pooled per-row gain and `apply`: whether the rule (MIN_SEASONS, MIN_POOLED)
    keeps this market. A season's own rows never enter its map."""
    p, y, season = np.asarray(p, dtype=float), np.asarray(went_over, dtype=float), np.asarray(season)
    held_out = []
    for s in sorted(set(season.tolist()))[1:]:
        tr, te = season < s, season == s
        a, b = fit(p[tr], y[tr])
        raw, cal = logloss(p[te], y[te]), logloss(apply(p[te], a, b), y[te])
        held_out.append({"season": int(s), "gain": float(raw.mean() - cal.mean()), "n": int(te.sum()),
                         "total": float(raw.sum() - cal.sum())})
    improved = sum(r["gain"] > 0 for r in held_out)
    pooled = sum(r["total"] for r in held_out) / max(sum(r["n"] for r in held_out), 1)
    return {"per_season": held_out, "seasons_improved": improved, "of": len(held_out), "pooled_gain": pooled,
            "apply": bool(improved >= MIN_SEASONS and pooled >= MIN_POOLED)}


def fit_by_rule(rows, model: str, alpha_method: str) -> tuple[dict, dict, dict]:
    """Calibration for one model's walk-forward rows (columns market, season, p_over, went_over).

    Returns ({market: (a, b)} fit on all the rows, the "_meta" block for save(), {market: check}).
    `apply_to` in the meta lists the markets whose check passed."""
    params, checks, n = {}, {}, {}
    for market, d in rows.groupby("market"):
        params[market] = fit(d["p_over"].to_numpy(), d["went_over"].to_numpy())
        checks[market] = walk_forward_check(d["p_over"].to_numpy(), d["went_over"].to_numpy(), d["season"].to_numpy())
        n[market] = int(len(d))
    meta = {"model": model, "alpha_method": alpha_method, "fit_seasons": sorted(int(s) for s in set(rows["season"])),
            "n": n, "apply_to": [m for m in sorted(checks) if checks[m]["apply"]]}
    return params, meta, checks
