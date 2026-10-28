"""Men's (ATP best-of-3, hard) tour-level reference from the calibrated simulator, for men-vs-women comparison.
Assumption: tour-average hold 80.5% (NOT sourced), day-form sigma calibrated to 38% 3-set rate."""
import numpy as np, sim, json
SIGMA = 0.0205
p0 = sim.inv_hold(0.805)
rng = np.random.default_rng(5)
favs = [0.52, 0.58, 0.64, 0.70, 0.76, 0.82, 0.88, 0.94]
rows = []
allT = []; all3 = []; allfav = []; allstraightT = []; all3T = []
for f in favs:
    d0 = sim.calibrate_d0(p0, p0, f, SIGMA, n=40000)
    Aw, n3, GA, GB = sim.sim_match(p0, p0, d0, SIGMA, 200000, rng)
    T = GA + GB
    rows.append(dict(fav=f, p3=float(n3.mean()), mean=float(T.mean()), sd=float(T.std()),
                     p10=float(np.percentile(T,10)), p50=float(np.median(T)), p90=float(np.percentile(T,90)),
                     straightmean=float(T[~n3].mean()), threemean=float(T[n3].mean()),
                     over215=float((T>21.5).mean()), over225=float((T>22.5).mean()), over235=float((T>23.5).mean())))
    allT.append(T); all3.append(n3)
# equal-weight mix of favourite bands 0.52..0.88 (tour-like; mean ~0.70)
mixT = np.concatenate(allT[:7]); mix3 = np.concatenate(all3[:7])
mix = dict(p3=float(mix3.mean()), mean=float(mixT.mean()), sd=float(mixT.std()),
           p10=float(np.percentile(mixT,10)), p25=float(np.percentile(mixT,25)), p50=float(np.median(mixT)),
           p75=float(np.percentile(mixT,75)), p90=float(np.percentile(mixT,90)),
           straightmean=float(mixT[~mix3].mean()), threemean=float(mixT[mix3].mean()))
# hold-rate sanity: simulated hold of a 80.5% server
print("hold(p0)=", sim.hold_prob(p0))
for r in rows: print({k: round(v,3) for k,v in r.items()})
print("MIX", {k: round(v,3) for k,v in mix.items()})
json.dump(dict(rows=rows, mix=mix), open("tour_ref.json","w"), indent=1)
