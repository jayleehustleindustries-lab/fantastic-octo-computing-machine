"""Leakage test: corrupt every result from (2023, week 10) onward; predictions for all earlier-or-same-week games must be unchanged."""
import sys; sys.path.insert(0, ".")
import json, numpy as np
import nfl_model as M
P = json.load(open("params.json"))
g, teams, qbs = M.load(); nt = len(teams)
pm, _ = M.run_margin(g, P["margin"], nt)
pt, ph, pa, _ = M.run_totals(g, P["totals"], nt)
g2 = g.copy()
cut = (g2.season > 2023) | ((g2.season == 2023) & (g2.week >= 10))
rng = np.random.default_rng(0)
mask = cut & g2.played
g2.loc[mask, "result"] = g2.loc[mask, "result"] + rng.normal(0, 40, mask.sum())
g2.loc[mask, "hp"] = g2.loc[mask, "hp"] + rng.normal(0, 30, mask.sum())
g2.loc[mask, "ap"] = g2.loc[mask, "ap"] + rng.normal(0, 30, mask.sum())
pm2, _ = M.run_margin(g2, P["margin"], nt)
pt2, _, _, _ = M.run_totals(g2, P["totals"], nt)
before = ((g.season < 2023) | ((g.season == 2023) & (g.week <= 10))).values  # includes week 10 itself (predicted before its own results)
after = (~before)
print(f"max |diff| margin preds for games up to and incl. 2023 wk10: {np.abs(pm - pm2)[before].max():.3e}")
print(f"max |diff| total  preds for games up to and incl. 2023 wk10: {np.abs(pt - pt2)[before].max():.3e}")
print(f"max |diff| margin preds after (should be large): {np.abs(pm - pm2)[after].max():.3f}")
