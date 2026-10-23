"""Calibrate day-form noise sigma so a tour-like mix of matchups gives ~38% three-set rate."""
import numpy as np, sim, json
rng = np.random.default_rng(11)
h = 0.805
p0 = sim.inv_hold(h)
favs = [0.52, 0.58, 0.64, 0.70, 0.76, 0.82, 0.88]   # reference mix of fav win probs (mean ~0.70)
def three_set_rate(sigma, n=40000):
    out = []
    for f in favs:
        d0 = sim.calibrate_d0(p0, p0, f, sigma, n=30000)
        Aw, n3, GA, GB = sim.sim_match(p0, p0, d0, sigma, n, rng)
        out.append((n3.mean(), (GA+GB).mean(), Aw.mean()))
    o = np.array(out)
    return o[:,0].mean(), o[:,1].mean(), o
res = {}
for s in (0.02, 0.03, 0.04, 0.05):
    r3, tg, o = three_set_rate(s)
    res[s] = (r3, tg)
    print(f"sigma={s}: avg 3-set rate {r3:.3f}, avg total games {tg:.2f}")
json.dump({str(k): v for k, v in res.items()}, open("sigma_calib.json", "w"))
