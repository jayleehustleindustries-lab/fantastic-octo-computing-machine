"""
Walk-forward NFL fundamental model (no market inputs, no leakage).

Margin model : team rating + QB rating (additive, online SGD / Elo-style), home field (online),
               rest differential.  Predicts home margin (home_score - away_score).
Totals model : team offence + team defence + QB-offence ratings (online SGD on points), league
               scoring level (online), dome/wind/cold environment terms.  Predicts game total.

Hyper-parameters are fit ONLY on 2010-2019 (2007-2009 is rating burn-in).  Ratings keep updating
game-by-game (week-batched: every game in a (season, week) is predicted before any result of that
week is used) through 2020-2026, parameters stay frozen.

Run:  python nfl_model.py          -> writes params.json and preds.csv
"""
import json, sys
import numpy as np
import pandas as pd
from scipy.optimize import minimize

TEAM_MAP = {"OAK": "LV", "SD": "LAC", "STL": "LA"}
FIT_START, FIT_END = 2010, 2019   # hyper-parameter fitting window (scored)
BURN_START = 2007                 # rating burn-in start
H_PTS = 1.1                       # per-team home points in the totals model (cancels in the total)


def load(path="games.csv"):
    g = pd.read_csv(path)
    g = g[g.season >= BURN_START].copy()
    for c in ["home_team", "away_team"]:
        g[c] = g[c].replace(TEAM_MAP)
    g["gametime"] = g["gametime"].fillna("00:00")
    g = g.sort_values(["season", "week", "gameday", "gametime", "game_id"]).reset_index(drop=True)
    g["played"] = g.result.notna()
    g["neutral"] = (g.location == "Neutral").astype(int)
    teams = sorted(set(g.home_team) | set(g.away_team))
    tix = {t: i for i, t in enumerate(teams)}
    g["h"] = g.home_team.map(tix)
    g["a"] = g.away_team.map(tix)
    qbs = sorted(set(g.home_qb_id.dropna()) | set(g.away_qb_id.dropna()))
    qix = {q: i for i, q in enumerate(qbs)}
    # unknown QB -> per-team placeholder id (never matches a real QB)
    g["hq"] = [qix.get(q, -1 - h) if isinstance(q, str) else -1 - h for q, h in zip(g.home_qb_id, g.h)]
    g["aq"] = [qix.get(q, -1 - a) if isinstance(q, str) else -1 - a for q, a in zip(g.away_qb_id, g.a)]
    g["rest_diff"] = (g.home_rest - g.away_rest).clip(-7, 7).fillna(0.0)
    roof = g.roof.fillna("outdoors")
    g["dome"] = roof.isin(["dome", "closed"]).astype(float)
    g["windx"] = np.where(g.dome == 0, (g.wind.fillna(0) - 10).clip(lower=0) / 10.0, 0.0)
    g["cold"] = np.where((g.dome == 0) & (g.temp.fillna(60) < 32), 1.0, 0.0)
    g["hp"] = g.home_score
    g["ap"] = g.away_score
    return g, teams, qbs


# ----------------------------------------------------------------------------------------------
# Margin model
# ----------------------------------------------------------------------------------------------
MARGIN_DEFAULT = dict(Kt=0.06, Kq=0.03, rho_t=0.75, rho_q=0.85, hfa0=2.3, hfa_lr=0.002,
                      qnew=-1.5, c_rest=0.25, cap=24.0)


def run_margin(g, p, n_teams):
    """Returns (pred_margin array, final_state). Week-batched walk-forward."""
    n = len(g)
    season = g.season.values; week = g.week.values
    H = g.h.values; A = g.a.values; HQ = g.hq.values; AQ = g.aq.values
    res = g.result.values.astype(float); neutral = g.neutral.values; rd = g.rest_diff.values
    played = g.played.values
    r = [0.0] * n_teams
    u = {}
    hfa = p["hfa0"]
    pred = np.zeros(n)
    Kt, Kq, rho_t, rho_q = p["Kt"], p["Kq"], p["rho_t"], p["rho_q"]
    qnew, c_rest, cap, hfa_lr = p["qnew"], p["c_rest"], p["cap"], p["hfa_lr"]
    i = 0
    prev_season = season[0]
    while i < n:
        j = i
        while j < n and season[j] == season[i] and week[j] == week[i]:
            j += 1
        if season[i] != prev_season:  # new season -> regress ratings
            r = [x * rho_t for x in r]
            for k in u:
                u[k] *= rho_q
            prev_season = season[i]

        def predict(k):
            uh = u.get(HQ[k], qnew); ua = u.get(AQ[k], qnew)
            return (r[H[k]] + uh - r[A[k]] - ua + (0.0 if neutral[k] else hfa) + c_rest * rd[k])

        for k in range(i, j):
            if played[k]:
                pred[k] = predict(k)
        for k in range(i, j):
            if played[k]:
                err = max(-cap, min(cap, res[k])) - pred[k]
                r[H[k]] += Kt * err; r[A[k]] -= Kt * err
                u[HQ[k]] = u.get(HQ[k], qnew) + Kq * err
                u[AQ[k]] = u.get(AQ[k], qnew) - Kq * err
                if not neutral[k]:
                    hfa += hfa_lr * err
        for k in range(i, j):
            if not played[k]:
                pred[k] = predict(k)
        i = j
    return pred, dict(r=r, u=u, hfa=hfa)


# ----------------------------------------------------------------------------------------------
# Totals model (offence / defence / QB-offence)
# ----------------------------------------------------------------------------------------------
TOTALS_DEFAULT = dict(Ko=0.04, Kd=0.04, Kqo=0.02, rho_o=0.7, rho_d=0.6, rho_qo=0.85, kL=0.01,
                      qnew_o=-0.5, c_dome=0.8, c_wind=-1.0, c_cold=-0.8, L0=22.0)


def run_totals(g, p, n_teams):
    n = len(g)
    season = g.season.values; week = g.week.values
    H = g.h.values; A = g.a.values; HQ = g.hq.values; AQ = g.aq.values
    hp = g.hp.values.astype(float); ap = g.ap.values.astype(float)
    played = g.played.values
    dome = g.dome.values; windx = g.windx.values; cold = g.cold.values
    O = [0.0] * n_teams; Dd = [0.0] * n_teams
    uo = {}
    L = p["L0"]
    pred_tot = np.zeros(n); pred_h = np.zeros(n); pred_a = np.zeros(n)
    Ko, Kd, Kqo = p["Ko"], p["Kd"], p["Kqo"]
    rho_o, rho_d, rho_qo, kL, qn = p["rho_o"], p["rho_d"], p["rho_qo"], p["kL"], p["qnew_o"]
    cd, cw, cc = p["c_dome"], p["c_wind"], p["c_cold"]
    i = 0
    prev_season = season[0]
    while i < n:
        j = i
        while j < n and season[j] == season[i] and week[j] == week[i]:
            j += 1
        if season[i] != prev_season:
            O = [x * rho_o for x in O]; Dd = [x * rho_d for x in Dd]
            for k in uo:
                uo[k] *= rho_qo
            prev_season = season[i]

        def predict(k):
            env = (cd * dome[k] + cw * windx[k] + cc * cold[k]) * 0.5
            ph = L + H_PTS + O[H[k]] + Dd[A[k]] + uo.get(HQ[k], qn) + env
            pa = L - H_PTS + O[A[k]] + Dd[H[k]] + uo.get(AQ[k], qn) + env
            return ph, pa

        for k in range(i, j):
            if played[k]:
                ph, pa = predict(k)
                pred_h[k] = ph; pred_a[k] = pa; pred_tot[k] = ph + pa
        dL = 0.0; cnt = 0
        for k in range(i, j):
            if played[k]:
                eh = hp[k] - pred_h[k]; ea = ap[k] - pred_a[k]
                O[H[k]] += Ko * eh; Dd[A[k]] += Kd * eh; uo[HQ[k]] = uo.get(HQ[k], qn) + Kqo * eh
                O[A[k]] += Ko * ea; Dd[H[k]] += Kd * ea; uo[AQ[k]] = uo.get(AQ[k], qn) + Kqo * ea
                dL += (eh + ea) / 2.0; cnt += 1
        if cnt:
            L += kL * dL / cnt
        for k in range(i, j):
            if not played[k]:
                ph, pa = predict(k)
                pred_h[k] = ph; pred_a[k] = pa; pred_tot[k] = ph + pa
        i = j
    return pred_tot, pred_h, pred_a, dict(O=O, D=Dd, uo=uo, L=L)


# ----------------------------------------------------------------------------------------------
# Fitting (2010-2019 only)
# ----------------------------------------------------------------------------------------------
def mask_fit(g):
    return ((g.season >= FIT_START) & (g.season <= FIT_END) & g.played).values


MARGIN_BOUNDS = dict(Kt=(0.0, 0.3), Kq=(0.0, 0.3), rho_t=(0.3, 1.0), rho_q=(0.3, 1.0), hfa0=(0.5, 4.5),
                     hfa_lr=(0.0, 0.02), qnew=(-6.0, 2.0), c_rest=(-1.0, 1.5))
TOTALS_BOUNDS = dict(Ko=(0.0, 0.2), Kd=(0.0, 0.2), Kqo=(0.0, 0.2), rho_o=(0.3, 1.0), rho_d=(0.0, 1.0),
                     rho_qo=(0.3, 1.0), kL=(0.0, 0.1), qnew_o=(-4.0, 2.0), c_dome=(-4.0, 6.0),
                     c_wind=(-6.0, 2.0), c_cold=(-6.0, 3.0))


def _pack(p, bounds):
    return np.array([p[k] for k in bounds])


def _unpack(x, base, bounds):
    q = dict(base)
    for v, (k, (lo, hi)) in zip(x, bounds.items()):
        q[k] = float(min(hi, max(lo, v)))
    return q


def fit_margin(g, nt, cap):
    m = mask_fit(g); y = g.result.values
    base = dict(MARGIN_DEFAULT, cap=cap)

    def obj(x):
        q = _unpack(x, base, MARGIN_BOUNDS)
        pr, _ = run_margin(g, q, nt)
        return float(np.mean((y[m] - pr[m]) ** 2))

    x0 = _pack(base, MARGIN_BOUNDS)
    best = minimize(obj, x0, method="Nelder-Mead", options=dict(maxiter=900, xatol=1e-3, fatol=1e-4))
    return _unpack(best.x, base, MARGIN_BOUNDS), best.fun


def fit_totals(g, nt):
    m = mask_fit(g); y = g.total.values
    base = dict(TOTALS_DEFAULT)

    def obj(x):
        q = _unpack(x, base, TOTALS_BOUNDS)
        pr, _, _, _ = run_totals(g, q, nt)
        return float(np.mean((y[m] - pr[m]) ** 2))

    x0 = _pack(base, TOTALS_BOUNDS)
    best = minimize(obj, x0, method="Nelder-Mead", options=dict(maxiter=1400, xatol=1e-3, fatol=1e-4))
    # restart once from the optimum (Nelder-Mead stalls easily)
    best = minimize(obj, best.x, method="Nelder-Mead", options=dict(maxiter=800, xatol=1e-3, fatol=1e-5))
    return _unpack(best.x, base, TOTALS_BOUNDS), best.fun


def main():
    g, teams, qbs = load()
    nt = len(teams)
    m = mask_fit(g)
    y = g.result.values
    print(f"games loaded: {len(g)}  fit games (2010-2019): {int(m.sum())}")
    best = None
    for cap in [14.0, 21.0, 28.0, 100.0]:
        p, mse = fit_margin(g, nt, cap)
        print(f"margin cap={cap:5.0f}  fit MSE={mse:.3f}  RMSE={np.sqrt(mse):.3f}")
        if best is None or mse < best[1]:
            best = (p, mse, cap)
    pm, mse_m, cap = best
    print("chosen margin params:", json.dumps(pm))
    pt, mse_t = fit_totals(g, nt)
    print(f"totals fit MSE={mse_t:.3f} RMSE={np.sqrt(mse_t):.3f}")
    print("chosen totals params:", json.dumps(pt))

    pred_m, st_m = run_margin(g, pm, nt)
    pred_t, pred_h, pred_a, st_t = run_totals(g, pt, nt)
    g["m_elo"] = pred_m
    g["t_od"] = pred_t
    g["m_od"] = pred_h - pred_a

    # ensemble weight between the two margin predictors, fit on 2010-2019 only
    best_w, best_mse = 1.0, 1e9
    for w in np.linspace(0, 1, 21):
        mm = w * pred_m + (1 - w) * (pred_h - pred_a)
        e = np.mean((y[m] - mm[m]) ** 2)
        if e < best_mse:
            best_w, best_mse = w, e
    print(f"ensemble weight on Elo+QB margin (fit 2010-19): {best_w:.2f}  MSE={best_mse:.3f}")
    g["m_model"] = best_w * g.m_elo + (1 - best_w) * g.m_od
    g["t_model"] = g.t_od

    # residual sd (fit window) for converting point predictions to probabilities
    sd_m = float(np.std(y[m] - g.m_model.values[m]))
    sd_t = float(np.std(g.total.values[m] - g.t_model.values[m]))
    # bias correction of totals (mean error over fit window; ~0 after optimisation)
    out = dict(margin=pm, totals=pt, w_elo=float(best_w), sd_margin=sd_m, sd_total=sd_t,
               fit_mse_margin=float(mse_m), fit_mse_totals=float(mse_t))
    json.dump(out, open("params.json", "w"), indent=1)
    keep = ["game_id", "season", "week", "game_type", "gameday", "gametime", "away_team", "home_team",
            "away_qb_name", "home_qb_name", "result", "total", "spread_line", "total_line",
            "home_moneyline", "away_moneyline", "home_spread_odds", "away_spread_odds",
            "over_odds", "under_odds", "m_elo", "m_od", "m_model", "t_model", "played", "neutral", "roof", "temp", "wind"]
    g[keep].to_csv("preds.csv", index=False)
    print("wrote params.json, preds.csv")

    # quick scoreboard
    for lo, hi, nm in [(2010, 2019, "fit 2010-19"), (2020, 2022, "blend 2020-22"), (2023, 2025, "holdout 2023-25")]:
        s = g[(g.season >= lo) & (g.season <= hi) & g.played & g.spread_line.notna()]
        rm = lambda e: float(np.sqrt(np.mean(e ** 2)))
        print(f"{nm:16s} n={len(s)}  margin RMSE model={rm(s.result - s.m_model):.3f} elo={rm(s.result - s.m_elo):.3f} "
              f"market={rm(s.result - s.spread_line):.3f} | total RMSE model={rm(s.total - s.t_model):.3f} market={rm(s.total - s.total_line):.3f}")


if __name__ == "__main__":
    main()
