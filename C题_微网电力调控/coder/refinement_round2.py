#!/usr/bin/env python3
"""Round-2 refinement for Q3 settlement ambiguity and causal Q4 price information.

Produces:
- state/q3_alt_penalty.npz: sensitivity under positive-only 50% downward breach fee
- state/q4_2_causal.npz: Q4-2 using a causal 7-day-lag price forecast for dispatch
- state/q4_3_causal.npz: Q4-3 using a causal 7-day-lag price forecast for dispatch
- coder/logs/refinement_round2.json

The official Q3 interpretation retained by the main model is the settlement form
  p*min(g_plan,g_adj) + 0.5*p*(g_plan-g_adj)_+ + 1.5*p*(g_adj-g_plan)_+
which algebraically equals p*g_plan - 0.5*p*down + 1.5*p*up.
The alternative here treats 0.5*p*down as an additional penalty on top of the
entire plan cost. It is included only as a robustness/sensitivity interpretation.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from scipy.optimize import linprog

import solve_microgrid as m

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
LOGS = ROOT / "coder" / "logs"


def solve_adjust_general(price, safe_net_power, soc0, g_plan_ref, down_coeff=-0.5):
    p=np.asarray(price,float); net=np.asarray(safe_net_power,float); g0=np.asarray(g_plan_ref,float)
    T=len(p); n=6*T
    G,C,D,E,UP,DN=0,T,2*T,3*T,4*T,5*T
    obj=np.zeros(n); obj[UP:UP+T]=1.5*p; obj[DN:DN+T]=down_coeff*p
    Aeq=np.zeros((2*T,n)); beq=np.zeros(2*T)
    for t in range(T):
        Aeq[t,E+t]=1; Aeq[t,C+t]=-m.ETA; Aeq[t,D+t]=1/m.ETA
        if t==0: beq[t]=soc0
        else: Aeq[t,E+t-1]=-1
        rr=T+t
        Aeq[rr,G+t]=1; Aeq[rr,UP+t]=-1; Aeq[rr,DN+t]=1; beq[rr]=g0[t]
    Aub=np.zeros((T,n)); bub=-net*m.DT
    for t in range(T):
        Aub[t,G+t]=-1; Aub[t,C+t]=1; Aub[t,D+t]=-1
    bounds=( [(0,None)]*T + [(0,m.STEP_MAX)]*T + [(0,m.STEP_MAX)]*T +
             [(m.E_MIN,m.E_MAX)]*T + [(0,None)]*T + [(0,None)]*T )
    r=linprog(obj,A_ub=Aub,b_ub=bub,A_eq=Aeq,b_eq=beq,bounds=bounds,method="highs")
    if not r.success: raise RuntimeError(r.message)
    x=r.x
    return x[G:G+T],x[C:C+T],x[D:D+T],np.r_[soc0,x[E:E+T]],x[UP:UP+T],x[DN:DN+T]


def simulate_q3_custom(dispatch_prices, settlement_prices, down_coeff=-0.5):
    """Q3 simulation with dispatch price forecast and realized settlement prices."""
    soc=6000.0
    out={k:[] for k in ["g_plan","g_final","ch","dis","soc0","soc1","emerg","plan_cost","adj_delta","em_cost","cost"]}
    bounds=[(0,35,0),(35,71,1),(71,107,2),(107,144,3)]
    for day in range(365):
        p_dec=np.asarray(dispatch_prices[day],float)
        p_set=np.asarray(settlement_prices[day],float)
        safe0=m.NET_REF[day,0]+m.reserve_q3(0,day,np.arange(144))
        g0,c0,d0,s0,_=m.solve_net(p_dec,safe0,soc)
        gf,cf,df=g0.copy(),c0.copy(),d0.copy(); current_soc=soc
        for bi,(a,b,ki) in enumerate(bounds):
            if bi==0:
                for t in range(a,b): current_soc += m.ETA*cf[t]-df[t]/m.ETA
            else:
                rem=np.arange(a,144)
                safe=m.NET_REF[day,ki,rem]+m.reserve_q3(ki,day,rem)
                ga,ca,da,sp,up,dn=solve_adjust_general(p_dec[rem],safe,current_soc,g0[rem],down_coeff=down_coeff)
                n=b-a
                gf[a:b],cf[a:b],df[a:b]=ga[:n],ca[:n],da[:n]
                for j in range(n): current_soc += m.ETA*ca[j]-da[j]/m.ETA
        emerg=np.maximum(m.NET_ACTUAL[day]*m.DT-(gf+df-cf),0)
        up=np.maximum(gf-g0,0); dn=np.maximum(g0-gf,0)
        pcost=float((p_set*g0).sum())
        adj=float((1.5*p_set*up + down_coeff*p_set*dn).sum())
        emc=float((5*p_set*emerg).sum())
        total=pcost+adj+emc
        vals=dict(g_plan=g0,g_final=gf,ch=cf,dis=df,soc0=soc,soc1=current_soc,emerg=emerg,
                  plan_cost=pcost,adj_delta=adj,em_cost=emc,cost=total)
        for k,v in vals.items(): out[k].append(v)
        soc=float(current_soc)
        if (day+1)%50==0: print(f"q3 custom day {day+1}/365",flush=True)
    return {k:np.array(v) for k,v in out.items()}


def build_causal_price_forecast():
    pred=np.zeros_like(m.PRICE_VAR)
    for d in range(365):
        pred[d]=m.PRICE_VAR[d-7] if d>=7 else m.A1_PRICE
    return pred


def simulate_q2_causal(price_pred):
    soc=6000.0
    out={k:[] for k in ["g","ch","dis","soc0","soc1","emerg","cost","plan_cost","reserve_mean"]}
    for day in range(365):
        p_dec=price_pred[day]; p_set=m.PRICE_VAR[day]
        r=m.reserve_from(m.RESID,day,np.arange(144)); safe=m.NET_PRED[day]+r
        g,c,d,s,_=m.solve_net(p_dec,safe,soc)
        emerg=np.maximum(m.NET_ACTUAL[day]*m.DT-(g+d-c),0)
        pcost=float((p_set*g).sum()); cost=pcost+float((5*p_set*emerg).sum())
        vals=dict(g=g,ch=c,dis=d,soc0=soc,soc1=s[-1],emerg=emerg,cost=cost,plan_cost=pcost,reserve_mean=r.mean())
        for k,v in vals.items(): out[k].append(v)
        soc=float(s[-1])
    return {k:np.array(v) for k,v in out.items()}


def metrics(x):
    sl=slice(31,None)
    return {
      "total_cost_feb_dec":float(x["cost"][sl].sum()),
      "plan_cost_feb_dec":float(x["plan_cost"][sl].sum()),
      "emergency_cost_feb_dec":float(x["em_cost"][sl].sum()) if "em_cost" in x else float((x["cost"][sl]-x["plan_cost"][sl]).sum()),
      "emergency_kwh_feb_dec":float(x["emerg"][sl].sum()),
      "purchase_kwh_feb_dec":float((x["g_final"][sl] if "g_final" in x else x["g"][sl]).sum())
    }


def main():
    price_pred=build_causal_price_forecast()
    err=m.PRICE_VAR[31:]-price_pred[31:]
    price_metrics={"mae":float(np.abs(err).mean()),"rmse":float(np.sqrt(np.mean(err**2))),"corr":float(np.corrcoef(m.PRICE_VAR[31:].ravel(),price_pred[31:].ravel())[0,1])}

    p_fixed=np.tile(m.A1_PRICE,(365,1))
    q3_alt=simulate_q3_custom(p_fixed,p_fixed,down_coeff=+0.5)
    np.savez_compressed(STATE/"q3_alt_penalty.npz",**q3_alt)

    q42=simulate_q2_causal(price_pred)
    np.savez_compressed(STATE/"q4_2_causal.npz",**q42)
    q43=simulate_q3_custom(price_pred,m.PRICE_VAR,down_coeff=-0.5)
    np.savez_compressed(STATE/"q4_3_causal.npz",**q43)

    oracle42=np.load(STATE/"q4_2.npz"); oracle43=np.load(STATE/"q4_3.npz")
    out={
      "price_forecast_lag7":price_metrics,
      "q3_alt_positive_down_penalty":metrics(q3_alt),
      "q4_2_causal":metrics(q42),
      "q4_3_causal":metrics(q43),
      "q4_2_oracle":metrics(oracle42),
      "q4_3_oracle":metrics(oracle43),
    }
    out["q4_2_causal_premium_vs_oracle_pct"]=100*(out["q4_2_causal"]["total_cost_feb_dec"]/out["q4_2_oracle"]["total_cost_feb_dec"]-1)
    out["q4_3_causal_premium_vs_oracle_pct"]=100*(out["q4_3_causal"]["total_cost_feb_dec"]/out["q4_3_oracle"]["total_cost_feb_dec"]-1)
    out["q4_causal_q3_saving_vs_q2_pct"]=100*(1-out["q4_3_causal"]["total_cost_feb_dec"]/out["q4_2_causal"]["total_cost_feb_dec"])
    (LOGS/"refinement_round2.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
