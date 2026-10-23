import sys, numpy as np, pandas as pd
sys.path.insert(0, '/tmp/claude-0/-home-user-fantastic-octo-computing-machine/fd837da0-fc17-5f70-a6ad-c31478ee2717/scratchpad/nfl/props')
from common import p_over, p_push
P = pd.read_pickle('/tmp/claude-0/-home-user-fantastic-octo-computing-machine/fd837da0-fc17-5f70-a6ad-c31478ee2717/scratchpad/nfl/props/proj_final.pkl')
W=0.30
def dec(a): return 1 + (a/100 if a>0 else 100/-a)
cases = [
 ('Jayden Daniels','WAS','pass_yds',[(198.5,-114,-114),(202.5,-115,-115),(210.5,-110,-110)]),
 ('Cam Ward','TEN','pass_yds',[(190.5,-114,-114),(193.5,-110,-110),(195.5,-110,-110),(199.5,-110,-110)]),
 ('C.J. Stroud','HOU','pass_yds',[(239.5,-112,-112),(239.5,-114,-114),(243.5,-110,-110)]),
 ('Chase Brown','CIN','rush_yds',[(61.5,-110,-110),(64.5,-115,-115),(65.5,-110,-110),(67.5,-110,-110),(69.5,-110,-110)]),
]
for n,t,s,lines in cases:
    r = P[(P.name==n)&(P.team==t)&(P.stat==s)].iloc[0]
    print(f"\n{n} {s}: mu={r.mu:.1f} median={r['median']} alpha={r.alpha:.3f} eff_n={r.eff_n:.1f} g26={r.g26} avg26={r.avg26}")
    for L,po,pu in lines:
        pov=float(p_over(r.mu,r.alpha,L)); pun=1-pov
        # no vig
        io,iu=1/dec(po),1/dec(pu); nv_u=iu/(io+iu)
        for w in (0.30,0.15,0.0):
            pb=w*pun+(1-w)*nv_u
            d=dec(pu); be=1/d
            print(f"  line {L} U{pu}: p_model_under={pun:.3f} nv_u={nv_u:.3f} w={w:.2f} p_blend={pb:.3f} BE={be:.3f} edge={pb*d-1:+.3f}")
