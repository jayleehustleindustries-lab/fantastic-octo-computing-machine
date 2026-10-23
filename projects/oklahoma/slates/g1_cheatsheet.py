"""WNBA Finals G1 (ATL @ GS, Sat Oct 17) Dabble cheat sheet. Research only; nothing places bets.
For each player-market: fair line and the most generous line at which MORE / LESS clears a pick'em
break-even after the Benter blend (0.3 model + 0.7 line), plus a safety tier."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1])
from oklahoma.models import prob_over
from oklahoma.calibrate import calibrate
from oklahoma.compare import blend, break_even
MODEL = "context_glm_plus2si"
SLIPS = {"2-pick": break_even(3, 2), "3-pick": break_even(6, 3), "5-pick": break_even(20, 5)}

def p_more(line, mu, alpha, market):
    return float(calibrate(prob_over(np.array([line]), np.array([mu]), alpha)[0], market, model=MODEL))

def cuts(r):
    lines = np.arange(max(0.5, np.floor(r.p10) - 3.5), np.ceil(r.p90) + 4, 1.0)   # .5 lines only
    pm = {L: p_more(L, r.mu, r.alpha, r.market) for L in lines}
    out = {}
    for name, be in SLIPS.items():
        more = [L for L, p in pm.items() if blend(p) >= be]
        less = [L for L, p in pm.items() if blend(1 - p) >= be]
        out[f"MORE_{name}"] = max(more) if more else None
        out[f"LESS_{name}"] = min(less) if less else None
    return out

ROLE_RISK = {"DeWanna Bonner": "bench risk if Gray plays", "Allisha Gray": "return from finger injury; hand-handle"}
rows = []
for scen, path in (("Gray OUT", sys.argv[2]), ("Gray IN", sys.argv[3])):
    d = pd.read_csv(path)
    for r in d.itertuples():
        sd = float(np.sqrt(r.mu + r.alpha * r.mu ** 2))
        c = cuts(r)
        tier = "A" if (r.market == "points" and r.recent_min >= 28) else \
               "B" if (r.market in ("pra", "rebounds") and r.recent_min >= 26) else "C"
        flag = ROLE_RISK.get(r.player, "")
        if r.recent_min < 20: flag = (flag + "; " if flag else "") + "bench minutes"
        if flag: tier = "C"
        rows.append(dict(scenario=scen, team=r.game[:3], player=r.player, market=r.market, proj=round(r.mu, 1),
                         fair=r.fair_line, sd=round(sd, 1), p10=r.p10, p90=r.p90, min=r.recent_min,
                         tier=tier, calibrated=r.market == "points", flag=flag, **c))
out = pd.DataFrame(rows)
out.to_csv(sys.argv[4], index=False)
tierord = {"A": 0, "B": 1, "C": 2}
for scen in ("Gray OUT", "Gray IN"):
    t = out[out.scenario == scen].copy()
    t["_k"] = t.tier.map(tierord); t["_cv"] = t.sd / t.proj.clip(lower=0.5)
    t = t.sort_values(["_k", "_cv"])
    print(f"\n===== {scen} | safest first (tier, then lowest spread relative to projection) =====")
    print(t[["tier", "team", "player", "market", "proj", "fair", "MORE_3-pick", "LESS_3-pick", "MORE_2-pick", "LESS_2-pick", "flag"]]
          .to_string(index=False))
