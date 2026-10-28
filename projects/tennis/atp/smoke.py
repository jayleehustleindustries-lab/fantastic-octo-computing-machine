import sim, numpy as np
print('hold(0.64)=',sim.hold_prob(0.64),'inv(0.805)=',sim.inv_hold(0.805))
rng=np.random.default_rng(1)
p=sim.inv_hold(0.805)
for s in (0.0,0.02,0.04):
    Aw,n3,GA,GB=sim.sim_match(p,p,0.0,s,100000,rng)
    print('even match sigma',s,': win',Aw.mean().round(3),'3set',n3.mean().round(3),'tot games mean',(GA+GB).mean().round(2))
