"""Price the owner's Dabble tennis board, Fri Oct 23 2026 (CT). Research only; nothing places bets.
Totals: cards.py simulators. Break points won: rough binomial on simulated holds (UNVALIDATED, flagged)."""
import sys, json, numpy as np
T = sys.argv[1]
sys.path.insert(0, T + "/wta"); sys.path.insert(0, T + "/atp")
import wta_mc as w, sim as atp
W = 0.3
M = [  # fav, dog, tour, p_fav (public no-vig / Kalshi), lines: (kind, who, line)
 ("Bouzkova", "Bejlek", "WTA", 0.61, [("total", None, 21.5), ("bp", "fav", 4.5)]),
 ("Siniakova", "Stoiana", "WTA", 0.69, [("total", None, 20.5)]),
 ("Alexandrova", "Fernandez", "WTA", 0.56, [("bp", "dog", 4.5)]),
 ("Boulter", "Ruzic", "WTA", 0.62, [("total", None, 21.5)]),
 ("Jovic", "Shnaider", "WTA", 0.51, [("total", None, 21.5), ("bp", "fav", 4.5), ("bp", "dog", 4.5)]),
 ("Basilashvili", "Mannarino", "ATP", 0.56, [("total", None, 22.5)]),
 ("Tsitsipas", "Duckworth", "ATP", 0.80, [("total", None, 22.5), ("bp", "dog", 0.5)]),
 ("Medvedev", "Atmane", "ATP", 0.80, [("bp", "fav", 2.5)]),
]
rng = np.random.default_rng(5)
def scen(tour, p, seed):
    if tour == "WTA":
        d = w.solve_symmetric(p, n=120000, seed=seed)
        r = w.simulate(w.MU + d, (1 - w.MU) + d, w.MU - d, (1 - w.MU) - d, n=200000, seed=seed + 1)
        sf, sd, hold, sig = w.MU + d, w.MU - d, w.game_hold, w.SIGMA_FORM
        tot = r["total"]
    else:
        p0 = atp.inv_hold(0.805); d0 = atp.calibrate_d0(p0, p0, p, 0.0205)
        _, _, ga, gb = atp.sim_match(p0, p0, d0, 0.0205, 200000, np.random.default_rng(seed + 1))
        tot = ga + gb; sf, sd, hold, sig = p0 + d0, p0 - d0, atp.hold_prob, 0.0205
    n = len(tot); f = rng.normal(0, sig, n) - rng.normal(0, sig, n)
    hf = hold(np.clip(sf + f, .3, .93)); hd = hold(np.clip(sd - f, .3, .93))
    ns = np.floor(tot / 2).astype(int)
    brk_by_fav = rng.binomial(ns, 1 - hd); brk_by_dog = rng.binomial(ns, 1 - hf)
    return tot, brk_by_fav, brk_by_dog
rows = []
for i, (fav, dog, tour, p, lines) in enumerate(M):
    S3 = [scen(tour, q, 10 + 7 * i + j) for j, q in enumerate((p - 0.04, p, p + 0.04))]
    for kind, who, L in lines:
        k = 0 if kind == "total" else (1 if who == "fav" else 2)
        pm = [float((s[k] > L).mean()) for s in S3]
        name = f"{fav}-{dog} total" if kind == "total" else f"{fav if who == 'fav' else dog} break pts won"
        med = float(np.median(S3[1][k]))
        for side, pv in (("MORE", pm), ("LESS", [1 - x for x in pm])):
            rows.append(dict(leg=f"{name} {side} {L}", tour=tour, p_fav=p, median=med, p_model_lo=round(min(pv), 3),
                             p_model=round(pv[1], 3), p_blend=round(W * pv[1] + (1 - W) * 0.5, 4),
                             p_blend_worst=round(W * min(pv) + (1 - W) * 0.5, 4), unvalidated=(kind == "bp")))
rows.sort(key=lambda r: -r["p_blend"])
json.dump(rows, open(sys.argv[2], "w"), indent=1)
print(f"break-even per leg: 3-pick 6x {6**(-1/3):.4f} | 2-pick 3x {3**-0.5:.4f}")
for r in rows[:16]:
    print(f"{r['leg']:44s} {r['tour']} med {r['median']:5.1f} model {r['p_model']:.3f} (worst {r['p_model_lo']:.3f}) blend {r['p_blend']:.4f} {'UNVALIDATED' if r['unvalidated'] else ''}")
