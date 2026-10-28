"""Run slate: Benter blend + MC totals for ATP Shanghai Masters R32 (China-date Oct 11, 2026).
Inputs are from public snippets (see report.md for sources). Serve/return profiles are ASSUMPTIONS (not found in snippets)."""
import numpy as np, json, sim

W = 0.3
SIGMA = 0.0205          # calibrated: tour-like mix -> ~38% three-set rate (calib_sigma.py)
SIGMA_ALT = 0.027       # sensitivity: ~35% three-set rate (Tennis Abstract tour ~35-36%)
N_FINAL = 400000
LINES = [19.5, 20.5, 21.5, 22.5, 23.5, 24.5, 25.5]
spw_tour = sim.inv_hold(0.805); rpw_tour = 1 - spw_tour

# A = market favourite. hold/brk = ASSUMED hard-court hold% / break% (general knowledge; NOT found in snippets).
M = [
 dict(id="ZVE-HAL", A="Zverev", B="Halys", rnd="R32", surface="Hard (outdoor)",
      holdA=.86, brkA=.23, holdB=.80, brkB=.17,
      decA=1.17, decB=5.00, mkt_src="wincomparator decimal odds (book unspecified)", mkt_override=None,
      third=[0.83], third_note="wincomparator model 83%",
      total_line=20.5, total_src="Stats Zone tip 'Over 20.5 games' (book/price not stated)"),
 dict(id="SHE-GEA", A="Shelton", B="Gea", rnd="R32", surface="Hard (outdoor)",
      holdA=.89, brkA=.17, holdB=.80, brkB=.17,
      decA=1.36, decB=3.20, mkt_src="wincomparator decimal odds (book unspecified)", mkt_override=None,
      third=[0.84], third_note="Elo-derived (stringtension snapshots: Shelton hard ~2009/1981 vs Gea hard 1719 -> ~0.82-0.85); wincomparator's own 59% excluded (inconsistent with its odds)",
      total_line=None, total_src="not found (ats.io model projects 2-0, 23 games)"),
 dict(id="DEM-SAK", A="De Minaur", B="Sakamoto", rnd="R32", surface="Hard (outdoor)",
      holdA=.80, brkA=.26, holdB=.85, brkB=.13,
      decA=1.29, decB=3.75, mkt_src="avg of Kalshi 68% and wincomparator no-vig (1.29/3.75)", mkt_override=None,
      third=[0.60], third_note="wincomparator model 59.7-61.3%",
      total_line=None, total_src="not found (MediaPronos: De Minaur -3 games)"),
 dict(id="DF-TIA", A="Tiafoe", B="Davidovich Fokina", rnd="R32", surface="Hard (outdoor)",
      holdA=.85, brkA=.19, holdB=.79, brkB=.22,
      decA=1.73, decB=None, mkt_src="wincomparator Tiafoe 1.73; DF price NOT FOUND -> ASSUMED 4.5% overround", mkt_override=None,
      third=[0.562, 0.62, 0.503], third_note="wincomparator 56.2%; stringtension Elo 62.0% / 50.3% (two snapshots)",
      total_line=None, total_src="not found"),
 dict(id="CER-MEN", A="Mensik", B="F. Cerundolo", rnd="R32", surface="Hard (outdoor)",
      holdA=.87, brkA=.17, holdB=.80, brkB=.22,
      decA=1.62, decB=2.30, mkt_src="wincomparator decimal odds (Mensik 1.62 / Cerundolo 2.30; book unspecified)", mkt_override=None,
      third=[0.437, 0.69], third_note="wincomparator model has Cerundolo 56.3% (Mensik 43.7%); stringtension hard Elo 1933 (Mensik) favours Mensik ~0.69; H2H Cerundolo 2-0/3-0 and 6-3 6-3 last week at Beijing",
      total_line=None, total_src="sets market: Over 2.5 sets +110 (Sportytrader pick, Caesars)"),
 dict(id="KHA-MAN", A="Khachanov", B="Mannarino", rnd="R32", surface="Hard (outdoor)",
      holdA=.85, brkA=.18, holdB=.78, brkB=.18,
      decA=1.30, decB=3.50, mkt_src="wincomparator decimal odds (book unspecified)", mkt_override=None,
      third=[0.704, 0.60, 0.638], third_note="wincomparator 70.4%; ats.io 60%; stringtension Elo 63.8%",
      total_line=22.5, total_src="wincomparator o/u 22.5 (book unspecified); ats.io projects 20 games, UNDER"),
 dict(id="HUR-ZHO", A="Hurkacz", B="Zhou Yi", rnd="R32", surface="Hard (outdoor)",
      holdA=.89, brkA=.14, holdB=.78, brkB=.14,
      decA=1.11, decB=6.50, mkt_src="wincomparator decimal odds (book unspecified)", mkt_override=None,
      third=[0.808], third_note="wincomparator model 80.8%",
      total_line=21.5, total_src="ats.io o/u 21.5 (model-implied; projects 6-4 6-4 = 20 games, UNDER)"),
]

def nv(decA, decB):
    a, b = 1/decA, 1/decB
    return a/(a+b)

rng_seed = 2026
out = []
for m in M:
    spwA = sim.inv_hold(m["holdA"]); spwB = sim.inv_hold(m["holdB"])
    rpwA = 1 - sim.inv_hold(1 - m["brkA"]); rpwB = 1 - sim.inv_hold(1 - m["brkB"])
    pA0 = spwA - (rpwB - rpw_tour); pB0 = spwB - (rpwA - rpw_tour)
    p_stats = sim.win_prob(pA0, pB0, 0.0, SIGMA, n=150000, seed=3)
    # market
    if m["id"] == "DEM-SAK":
        p_mkt = 0.5 * (0.68 + nv(m["decA"], m["decB"])); decB = m["decB"]
    elif m["decB"] is None:
        pA_raw = 1/m["decA"]; over = 1.045
        p_mkt = pA_raw/over; decB = 1/((1-p_mkt)*over)
    else:
        p_mkt = nv(m["decA"], m["decB"]); decB = m["decB"]
    p_model = float(np.mean(m["third"] + [p_stats]))
    p_blend = W*p_model + (1-W)*p_mkt
    # ML edges
    edgeA = p_blend*m["decA"] - 1; edgeB = (1-p_blend)*decB - 1
    kellyA = max(0, edgeA/(m["decA"]-1))/4; kellyB = max(0, edgeB/(decB-1))/4
    # calibrate sim to p_blend, run finals
    d0 = sim.calibrate_d0(pA0, pB0, p_blend, SIGMA, n=60000)
    rng = np.random.default_rng(rng_seed)
    Aw, n3, GA, GB = sim.sim_match(pA0, pB0, d0, SIGMA, N_FINAL, rng)
    T = GA + GB
    d0b = sim.calibrate_d0(pA0, pB0, p_blend, SIGMA_ALT, n=60000)
    Aw2, n32, GA2, GB2 = sim.sim_match(pA0, pB0, d0b, SIGMA_ALT, N_FINAL, np.random.default_rng(rng_seed+1))
    T2 = GA2 + GB2
    res = dict(id=m["id"], A=m["A"], B=m["B"], rnd=m["rnd"], decA=m["decA"], decB=decB,
               holdA=m["holdA"], holdB=m["holdB"], brkA=m["brkA"], brkB=m["brkB"],
               p_stats=p_stats, third=m["third"], p_model=p_model, p_mkt=p_mkt, p_blend=p_blend,
               edgeA=edgeA, edgeB=edgeB, kellyA=kellyA, kellyB=kellyB,
               p_sim_win=float(Aw.mean()), p3=float(n3.mean()), p3_alt=float(n32.mean()),
               tot_mean=float(T.mean()), tot_median=float(np.median(T)), tot_mean_alt=float(T2.mean()),
               over={str(L): float((T > L).mean()) for L in LINES},
               over_alt={str(L): float((T2 > L).mean()) for L in LINES},
               ga_mean=float(GA.mean()), gb_mean=float(GB.mean()), ga_med=float(np.median(GA)), gb_med=float(np.median(GB)),
               ga_over={str(k+0.5): float((GA > k+0.5).mean()) for k in range(6, 14)},
               gb_over={str(k+0.5): float((GB > k+0.5).mean()) for k in range(6, 14)},
               straight_fav=float(((Aw) & (~n3)).mean()),
               total_line=m["total_line"], total_src=m["total_src"], mkt_src=m["mkt_src"], third_note=m["third_note"])
    if m["total_line"]:
        L = m["total_line"]
        po = float((T > L).mean()); po_alt = float((T2 > L).mean())
        res["tot_pover"] = po; res["tot_pover_alt"] = po_alt
        res["tot_over_blend"] = W*po + (1-W)*0.5
        res["tot_under_blend"] = W*(1-po) + (1-W)*0.5
        res["tot_over_edge_110"] = res["tot_over_blend"]*(1+100/110) - 1
        res["tot_under_edge_110"] = res["tot_under_blend"]*(1+100/110) - 1
    if m["id"] == "CER-MEN":
        res["p_3sets"] = res["p3"]
        res["sets_over25_blend"] = W*res["p3"] + (1-W)*(1/2.10)   # market raw implied 47.6% (vig-inclusive)
        res["sets_over25_edge"] = res["sets_over25_blend"]*2.10 - 1
    out.append(res)
    print(f"{m['id']}: p_stats={p_stats:.3f} p_model={p_model:.3f} p_mkt={p_mkt:.3f} p_blend={p_blend:.3f} simwin={Aw.mean():.3f} "
          f"3set={n3.mean():.3f}(alt {n32.mean():.3f}) totMean={T.mean():.2f} med={np.median(T):.0f} | edgeA={edgeA:+.3f} edgeB={edgeB:+.3f}")
    print("   P(over):", {k: round(v, 3) for k, v in res["over"].items()})
json.dump(out, open("results.json", "w"), indent=1)
