#!/usr/bin/env python
"""WTA best-of-3 Monte Carlo (hard court, tiebreak at 6-6 in every set).

Model
-----
* Each player has a serve-points-won (spw) probability vs the specific opponent:
      spwA = spA - (rpB - (1 - MU))      spwB = spB - (rpA - (1 - MU))
  where sp = player's service-points-won vs an average returner, rp = return-points-won
  vs an average server, MU = tour-average service-points-won (WTA hard, assumption).
* Day-form noise: each match, each player draws f ~ N(0, SIGMA_FORM); it shifts BOTH their serve and
  return point probabilities (spwA += fA - fB, spwB += fB - fA).  This fattens the tails of the
  win-prob / total-games distribution relative to a plain iid-point model.
* Games are won with the exact point-level hold probability G(spw) (identical in distribution to
  playing the points one by one).  Tiebreaks use iid points with p = avg(own serve, own return)
  and an exact race-to-7-win-by-2 formula.  Server alternation and next-set first-server rules are
  followed.
* Vectorised over N matches with numpy.

CLI example:
  python wta_mc.py --pwin 0.60 --names Andreeva Zheng --lines 21.5 --n 400000
  python wta_mc.py --spA .60 --rpA .45 --spB .57 --rpB .42 --names A B
"""
import argparse
import json
import math
import numpy as np

# ---- tour-level assumptions (see report; MU/SIGMA/TAU calibrated in calibrate()) ----
MU = 0.560           # WTA hard-court avg service points won (assumption, tuned to ~64-65% hold)
SIGMA_FORM = 0.026   # day-form sd on point-win prob (calibrated: pop. 3-set rate ~35%, fav win 69.4%)


def game_hold(p):
    """P(server wins game) given iid point prob p (exact, incl. deuce)."""
    q = 1.0 - p
    return p**4 * (1 + 4*q + 10*q**2) + 20 * p**3 * q**3 * (p**2 / (p**2 + q**2))


def tb_win(p):
    """P(A wins tiebreak to 7, win by 2) with iid point prob p for A."""
    q = 1.0 - p
    from math import comb
    s = sum(comb(6 + k, k) * p**7 * q**k for k in range(0, 6))
    s += comb(12, 6) * p**6 * q**6 * (p**2 / (p**2 + q**2))
    return s


def simulate(spA, rpA, spB, rpB, n=200000, mu=MU, sigma=SIGMA_FORM, seed=1, rng=None):
    rng = rng or np.random.default_rng(seed)
    fA = rng.normal(0, sigma, n)
    fB = rng.normal(0, sigma, n)
    spwA = np.clip(spA - (rpB - (1 - mu)) + fA - fB, 0.2, 0.9)
    spwB = np.clip(spB - (rpA - (1 - mu)) + fB - fA, 0.2, 0.9)
    hA = game_hold(spwA)
    hB = game_hold(spwB)
    pA_tb = 0.5 * (spwA + (1 - spwB))
    # vectorised tb_win
    q = 1 - pA_tb
    from math import comb
    tbA = sum(comb(6 + k, k) * pA_tb**7 * q**k for k in range(0, 6)) + comb(12, 6) * pA_tb**6 * q**6 * (pA_tb**2 / (pA_tb**2 + q**2))

    first = rng.integers(0, 2, n)  # 0 = A serves first in set 1
    setsA = np.zeros(n, int)
    setsB = np.zeros(n, int)
    gamesA = np.zeros(n, int)
    gamesB = np.zeros(n, int)
    nsets = np.zeros(n, int)
    tbs = np.zeros(n, int)
    set_scores = []  # per set arrays (gA, gB, played mask)
    live = np.ones(n, bool)
    for s in range(3):
        live = (setsA < 2) & (setsB < 2)
        if not live.any():
            break
        gA = np.zeros(n, int)
        gB = np.zeros(n, int)
        over = ~live
        for i in range(12):
            act = ~over
            if not act.any():
                break
            server = first ^ ((gA + gB) & 1)  # 0 -> A serves
            u = rng.random(n)
            hold_p = np.where(server == 0, hA, hB)
            sw = u < hold_p
            a_wins = np.where(server == 0, sw, ~sw)
            gA = gA + (act & a_wins)
            gB = gB + (act & ~a_wins)
            mx = np.maximum(gA, gB)
            df = np.abs(gA - gB)
            over = over | (act & (mx >= 6) & (df >= 2))
        tie = ~over & live
        u = rng.random(n)
        a_tb = u < tbA
        gA = gA + (tie & a_tb)
        gB = gB + (tie & ~a_tb)
        tbs += tie
        nG = gA + gB
        last_server = first ^ ((nG - 1) & 1)
        first_next = 1 - last_server
        first = np.where(live, first_next, first)
        aw = live & (gA > gB)
        bw = live & (gB > gA)
        setsA += aw
        setsB += bw
        gamesA += np.where(live, gA, 0)
        gamesB += np.where(live, gB, 0)
        nsets += live
        set_scores.append((gA.copy(), gB.copy(), live.copy()))
    return dict(winA=(setsA > setsB), gamesA=gamesA, gamesB=gamesB, total=gamesA + gamesB,
                nsets=nsets, tbs=tbs, hA=hA, hB=hB, spwA=spwA, spwB=spwB)


def solve_symmetric(pwin, n=300000, seed=7, mu=MU, sigma=SIGMA_FORM):
    """Find a rating gap d (A: sp=mu+d, rp=(1-mu)+d ; B: -d) giving P(A wins match) = pwin."""
    lo, hi = -0.12, 0.12
    for _ in range(22):
        mid = (lo + hi) / 2
        r = simulate(mu + mid, (1 - mu) + mid, mu - mid, (1 - mu) - mid, n=n, seed=seed, mu=mu, sigma=sigma)
        if r['winA'].mean() < pwin:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def summarize(r, names=("A", "B"), lines=(18.5, 19.5, 20.5, 21.5, 22.5, 23.5, 24.5)):
    out = {}
    out['P_win_' + names[0]] = float(r['winA'].mean())
    out['P_win_' + names[1]] = 1 - out['P_win_' + names[0]]
    out['P_3sets'] = float((r['nsets'] == 3).mean())
    out['P_any_tiebreak'] = float((r['tbs'] > 0).mean())
    out['E_total'] = float(r['total'].mean())
    out['SD_total'] = float(r['total'].std())
    out['E_games_' + names[0]] = float(r['gamesA'].mean())
    out['E_games_' + names[1]] = float(r['gamesB'].mean())
    out['hold_' + names[0]] = float(r['hA'].mean())
    out['hold_' + names[1]] = float(r['hB'].mean())
    out['P_over'] = {str(L): float((r['total'] > L).mean()) for L in lines}
    out['P_total_hist'] = {int(k): float((r['total'] == k).mean()) for k in range(12, 37)}
    out['P_games_' + names[0] + '_over'] = {str(L): float((r['gamesA'] > L).mean()) for L in (8.5, 9.5, 10.5, 11.5, 12.5, 13.5)}
    out['P_games_' + names[1] + '_over'] = {str(L): float((r['gamesB'] > L).mean()) for L in (8.5, 9.5, 10.5, 11.5, 12.5, 13.5)}
    # game handicap A (A games - B games)
    diff = r['gamesA'] - r['gamesB']
    out['P_handicap_cover_' + names[0]] = {str(h): float((diff + h > 0).mean()) for h in (-5.5, -4.5, -3.5, -2.5, -1.5, 1.5, 2.5, 3.5, 4.5, 5.5)}
    return out


def calibrate(n=400000, seed=11):
    """Population calibration: draw rating gaps so the model favourite wins ~69.4% (Opta WTA 2023),
    report hold, 3-set rate, total-games moments, and tiebreak rate. Grid over SIGMA_FORM."""
    rng = np.random.default_rng(seed)
    rows = []
    for sigma in (0.0, 0.010, 0.015, 0.018, 0.022, 0.026):
        # choose tau (sd of rating gap in point-prob units) so favourite win rate ~ 0.694
        lo, hi = 0.005, 0.12
        for _ in range(14):
            tau = (lo + hi) / 2
            gap = np.abs(rng.normal(0, tau, 120000))
            # one sim per match with its own gap: simulate in chunks by vectorising spA/rpA arrays
            r = simulate(MU + gap / 2, (1 - MU) + gap / 2, MU - gap / 2, (1 - MU) - gap / 2,
                         n=len(gap), mu=MU, sigma=sigma, seed=seed)
            fav = r['winA'].mean()
            if fav < 0.694:
                lo = tau
            else:
                hi = tau
        gap = np.abs(rng.normal(0, tau, n))
        r = simulate(MU + gap / 2, (1 - MU) + gap / 2, MU - gap / 2, (1 - MU) - gap / 2, n=n, mu=MU, sigma=sigma, seed=seed + 1)
        hold_all = 0.5 * (r['hA'].mean() + r['hB'].mean())
        rows.append(dict(sigma=sigma, tau=round(tau, 4), fav_win=round(float(r['winA'].mean()), 4),
                         hold=round(float(hold_all), 4), three_set=round(float((r['nsets'] == 3).mean()), 4),
                         E_total=round(float(r['total'].mean()), 2), SD_total=round(float(r['total'].std()), 2),
                         tb_rate=round(float((r['tbs'] > 0).mean()), 4)))
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument('--pwin', type=float, help='pre-match P(A wins) (e.g. blended); solves a symmetric rating gap')
    ap.add_argument('--spA', type=float); ap.add_argument('--rpA', type=float)
    ap.add_argument('--spB', type=float); ap.add_argument('--rpB', type=float)
    ap.add_argument('--names', nargs=2, default=['A', 'B'])
    ap.add_argument('--lines', nargs='*', type=float, default=[18.5, 19.5, 20.5, 21.5, 22.5, 23.5, 24.5])
    ap.add_argument('--n', type=int, default=400000)
    ap.add_argument('--sigma', type=float, default=SIGMA_FORM)
    ap.add_argument('--mu', type=float, default=MU)
    ap.add_argument('--calibrate', action='store_true')
    a = ap.parse_args()
    if a.calibrate:
        for row in calibrate():
            print(row)
    else:
        if a.pwin is not None:
            d = solve_symmetric(a.pwin, mu=a.mu, sigma=a.sigma)
            spA, rpA, spB, rpB = a.mu + d, (1 - a.mu) + d, a.mu - d, (1 - a.mu) - d
            print(f"solved rating gap d={d:.4f} -> spA={spA:.3f} rpA={rpA:.3f} spB={spB:.3f} rpB={rpB:.3f}")
        else:
            spA, rpA, spB, rpB = a.spA, a.rpA, a.spB, a.rpB
        r = simulate(spA, rpA, spB, rpB, n=a.n, mu=a.mu, sigma=a.sigma)
        print(json.dumps(summarize(r, tuple(a.names), tuple(a.lines)), indent=1))
