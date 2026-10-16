"""Adversarial re-check of 3 underdog ML picks. Inputs copied from analyst report.md (labelled there as snippet/assumption)."""
def nv(a,b):
    x,y=1/a,1/b; return y/(x+y)   # no-vig prob of the SECOND price (dog)
picks = {
 "Sakamoto ML 3.75": dict(dec=3.75, fav=1.29, mkt_book=nv(1.29,3.75), kalshi_dog=0.32, model_dog=1-0.636, claimed=0.311),
 "Zhou Yi ML 6.50":  dict(dec=6.50, fav=1.11, mkt_book=nv(1.11,6.50), kalshi_dog=None, model_dog=1-0.779, claimed=0.169),
 "Mannarino ML 3.50":dict(dec=3.50, fav=1.30, mkt_book=nv(1.30,3.50), kalshi_dog=None, model_dog=1-0.650, claimed=0.294),
}
flb = {"Sakamoto ML 3.75":0.005,"Zhou Yi ML 6.50":0.010,"Mannarino ML 3.50":0.005}  # favourite-longshot haircut (assumption)
for k,v in picks.items():
    d=v["dec"]; be=1/d
    print(f"\n== {k}: break-even {be:.3%}, book no-vig dog {v['mkt_book']:.3%}, claimed p {v['claimed']:.3%}")
    print(f"  EV at book-only no-vig (pure vig): {v['mkt_book']*d-1:+.1%}")
    for w in (0.0,0.1,0.15,0.3):
        pb = w*v['model_dog']+(1-w)*v['mkt_book']
        print(f"  w={w:.2f} book-only market: p={pb:.3%} edge={pb*d-1:+.1%} | after FLB haircut p={pb-flb[k]:.3%} edge={(pb-flb[k])*d-1:+.1%}")
    if v['kalshi_dog']:
        mk=(v['mkt_book']+v['kalshi_dog'])/2
        for w in (0.15,0.3):
            pb=w*v['model_dog']+(1-w)*mk
            print(f"  w={w:.2f} book+Kalshi avg market ({mk:.1%}): p={pb:.3%} edge={pb*d-1:+.1%}")
    # decomposition of claimed edge
    mk_used = v['claimed']-0.3*(v['model_dog']-0)  # not used
print("\nSlate-level bias: mean p_model(fav) vs mean p_market(fav)")
pm=[79.4,77.9,63.6,56.6,56.3,65.0,77.9]; pk=[81.0,70.2,71.2,55.3,58.7,72.9,85.4]; ps=[75.8,71.8,67.3,57.8,56.2,66.0,74.9]
print(sum(pm)/7, sum(pk)/7, sum(ps)/7)
print("gaps model-market:",[round(a-b,1) for a,b in zip(pm,pk)])
