"""Point-by-point-equivalent Monte Carlo for best-of-3 ATP matches (iid points per server + day-form noise).
Regular games: exact game-hold probability from iid point prob (equivalent to point-by-point iid).
Tiebreaks: simulated point by point (server pattern 1-2-2-2...). Final-set tiebreak at 6-6 (Masters rule).
"""
import numpy as np

def hold_prob(p):
    q = 1 - p
    return p**4 * (1 + 4*q + 10*q**2) + 20 * p**3 * q**3 * (p**2 / (p**2 + q**2))

def inv_hold(h, lo=0.3, hi=0.95):
    a, b = lo, hi
    for _ in range(60):
        m = (a + b) / 2
        if hold_prob(m) < h: a = m
        else: b = m
    return (a + b) / 2

def sim_tiebreak(pA, pB, firstA, rng):
    """pA/pB: prob of winning a point on own serve (arrays). firstA: bool array, A serves 1st point.
    Returns bool array: A wins TB."""
    n = pA.shape[0]
    a = np.zeros(n, int); b = np.zeros(n, int)
    done = np.zeros(n, bool)
    k = 0
    while not done.all() and k < 400:
        # server for point k
        if k == 0:
            srvFirst = np.ones(n, bool)
        else:
            srvFirst = (((k - 1) // 2) % 2 == 1)
            srvFirst = np.full(n, srvFirst)
        srvA = np.where(srvFirst, firstA, ~firstA)
        pw = np.where(srvA, pA, 1 - pB)          # prob A wins this point
        u = rng.random(n)
        aw = u < pw
        act = ~done
        a += (aw & act); b += ((~aw) & act)
        done = done | (((a >= 7) | (b >= 7)) & (np.abs(a - b) >= 2))
        k += 1
    return a > b

def sim_set(pA, pB, firstA, rng):
    """returns gA, gB (TB set => 7-6/6-7), nGames(for serve-order carryover)."""
    n = pA.shape[0]
    hA = hold_prob(pA); hB = hold_prob(pB)
    gA = np.zeros(n, int); gB = np.zeros(n, int)
    for g in range(12):
        decided = ((gA >= 6) | (gB >= 6)) & (np.abs(gA - gB) >= 2)
        act = ~decided
        srvA = firstA if g % 2 == 0 else ~firstA
        pwin = np.where(srvA, hA, 1 - hB)   # prob A wins the game
        aw = rng.random(n) < pwin
        gA += (aw & act); gB += ((~aw) & act)
    tb = (gA == 6) & (gB == 6)
    if tb.any():
        idx = np.where(tb)[0]
        res = sim_tiebreak(pA[idx], pB[idx], firstA[idx], rng)
        gA[idx] += res; gB[idx] += ~res
    ng = gA + gB - tb.astype(int) * 12 + tb.astype(int) * 13 - tb.astype(int) * 0
    # games played count: normal sets gA+gB ; tiebreak sets 13
    ng = np.where(tb, 13, gA + gB)
    return gA, gB, ng

def sim_match(pA0, pB0, d0, sigma, n, rng):
    """pA0,pB0: baseline serve-point win probs (scalars). d0: calibration shift (A edge) applied pA+d0, pB-d0.
    sigma: sd of each player's day-form shift (point-prob units), shift persists across the match."""
    dA = rng.normal(0, sigma, n); dB = rng.normal(0, sigma, n)
    pA = np.clip(pA0 + d0 + dA - dB, 0.30, 0.93)
    pB = np.clip(pB0 - d0 + dB - dA, 0.30, 0.93)
    firstA = rng.random(n) < 0.5
    g1A, g1B, n1 = sim_set(pA, pB, firstA, rng)
    f2 = np.where(n1 % 2 == 0, firstA, ~firstA)
    g2A, g2B, n2 = sim_set(pA, pB, f2, rng)
    w1 = g1A > g1B; w2 = g2A > g2B
    need3 = (w1 != w2)
    f3 = np.where(n2 % 2 == 0, f2, ~f2)
    g3A, g3B, n3 = sim_set(pA, pB, f3, rng)
    g3A = np.where(need3, g3A, 0); g3B = np.where(need3, g3B, 0)
    w3 = g3A > g3B
    Awin = np.where(need3, w3, w1)
    GA = g1A + g2A + g3A; GB = g1B + g2B + g3B
    return Awin, need3, GA, GB

def win_prob(pA0, pB0, d0, sigma, n=60000, seed=1):
    rng = np.random.default_rng(seed)
    Aw, _, _, _ = sim_match(pA0, pB0, d0, sigma, n, rng)
    return Aw.mean()

def calibrate_d0(pA0, pB0, target, sigma, n=60000):
    lo, hi = -0.15, 0.15
    for _ in range(14):
        mid = (lo + hi) / 2
        if win_prob(pA0, pB0, mid, sigma, n, seed=7) < target: lo = mid
        else: hi = mid
    return (lo + hi) / 2
