"""Same-match correlation for WTA pick'em legs (total games, games won). Research only."""
import sys, itertools, numpy as np
sys.path.insert(0, sys.argv[1]); import wta_mc as m
W = 0.3
PAY = {2: 3, 3: 6}
def run(p, seed):
    d = m.solve_symmetric(p, n=200000, seed=seed)
    return m.simulate(m.MU + d, (1 - m.MU) + d, m.MU - d, (1 - m.MU) - d, n=400000, seed=seed + 1)
for p in (0.50, 0.65):
    r = run(p, 5 if p == .5 else 9)
    T, F, D = r['total'], r['gamesA'], r['gamesB']
    tl = 21.5
    fl = float(np.median(F)) - 0.5   # line at the median -> each leg about 50/50
    dl = float(np.median(D)) - 0.5
    legs = {f"Total OVER {tl}": T > tl, f"Total UNDER {tl}": T < tl,
            f"Fav games OVER {fl}": F > fl, f"Fav games UNDER {fl}": F < fl,
            f"Dog games OVER {dl}": D > dl, f"Dog games UNDER {dl}": D < dl}
    print(f"\n=== p_fav {p}: marginals")
    for k, v in legs.items(): print(f"  {k:24s} {v.mean():.3f}")
    rows = []
    for n in (2, 3):
        for combo in itertools.combinations(legs, n):
            bases = {c.rsplit(' ', 2)[0] for c in combo}
            if len(bases) < n: continue          # no OVER+UNDER of the same prop
            hit = np.logical_and.reduce([legs[c] for c in combo])
            pj, prod = hit.mean(), np.prod([legs[c].mean() for c in combo])
            # conservative blend: shrink joint toward the independent-50/50 market price
            pb = W * pj + (1 - W) * 0.5 ** n
            rows.append((pj * PAY[n] - 1, n, combo, pj, prod, pb, pb * PAY[n] - 1))
    rows.sort(reverse=True)
    print("  top/bottom slips: legs | joint model | product | joint blended | EV model | EV blended")
    for ev, n, combo, pj, prod, pb, evb in rows[:5] + rows[-3:]:
        print(f"  {n}-pick {' + '.join(combo)} | {pj:.3f} | {prod:.3f} | {pb:.3f} | {ev:+.1%} | {evb:+.1%}")
