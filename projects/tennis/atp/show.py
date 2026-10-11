import json
R = json.load(open("results.json"))
for r in R:
    print("==", r["id"], r["A"], "v", r["B"])
    print(" p_stats %.3f p_model %.3f p_mkt %.3f p_blend %.3f | simwin %.3f | P3 %.3f (alt %.3f) | straight fav %.3f" % (r["p_stats"], r["p_model"], r["p_mkt"], r["p_blend"], r["p_sim_win"], r["p3"], r["p3_alt"], r["straight_fav"]))
    print(" tot mean %.2f med %.0f | alt mean %.2f" % (r["tot_mean"], r["tot_median"], r["tot_mean_alt"]))
    print(" over:", {k: round(v,3) for k,v in r["over"].items()})
    print(" over_alt:", {k: round(v,3) for k,v in r["over_alt"].items()})
    print(" games won %s mean %.2f med %.0f | %s mean %.2f med %.0f" % (r["A"], r["ga_mean"], r["ga_med"], r["B"], r["gb_mean"], r["gb_med"]))
    print("  A over:", {k: round(v,3) for k,v in r["ga_over"].items()})
    print("  B over:", {k: round(v,3) for k,v in r["gb_over"].items()})
    for k in ("tot_pover","tot_pover_alt","tot_over_blend","tot_under_blend","tot_over_edge_110","tot_under_edge_110","sets_over25_blend","sets_over25_edge"):
        if k in r: print("  ", k, round(r[k],4))
    print("  ML edges A %+.3f B %+.3f ; qKelly A %.4f B %.4f ; decB %.2f" % (r["edgeA"], r["edgeB"], r["kellyA"], r["kellyB"], r["decB"]))
import numpy as np
print("mean market fav prob", np.mean([r["p_mkt"] for r in R]), "mean blended", np.mean([r["p_blend"] for r in R]))
print("mean sim 3-set", np.mean([r["p3"] for r in R]), "alt", np.mean([r["p3_alt"] for r in R]))
print("max |simwin - p_blend|", max(abs(r["p_sim_win"]-r["p_blend"]) for r in R))
