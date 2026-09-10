#!/usr/bin/env python3
"""Reproduce the C-problem numerical states from processed NPZ data.

Inputs
------
../data/processed/microgrid_data.npz

Outputs
-------
../state/q1.npz, q2.npz, q3.npz, q4_2.npz, q4_3.npz
../coder/logs/solver_summary.json

The script intentionally keeps the optimization linear and deterministic.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[1]
DATA = np.load(ROOT / "data" / "processed" / "microgrid_data.npz")
STATE = ROOT / "state"
LOGS = ROOT / "coder" / "logs"
STATE.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

DT = 1.0 / 6.0
ETA = 0.9
E_MIN = 1200.0
E_MAX = 10800.0
STEP_MAX = 5000.0 * DT
Q = 0.8
WINDOW = 28

A1_PRICE = DATA["a1_price"]
A1_LOAD = DATA["a1_load"]
A1_PV = DATA["a1_pv"]
LOAD = DATA["load"]
PV = DATA["pv"]
PRICE_VAR = DATA["price_var"]
FORECAST_HR = DATA["forecast"]
NET_ACTUAL = LOAD - PV


def solve_net(price: np.ndarray, net_power: np.ndarray, soc0: float, terminal_soc=None):
    p = np.asarray(price, float); net = np.asarray(net_power, float); T = len(p)
    n = 4 * T; obj = np.r_[p, np.zeros(3 * T)]
    neq = T + (1 if terminal_soc is not None else 0)
    Aeq = np.zeros((neq, n)); beq = np.zeros(neq)
    for t in range(T):
        Aeq[t, 3*T+t] = 1.0; Aeq[t, T+t] = -ETA; Aeq[t, 2*T+t] = 1.0 / ETA
        if t == 0: beq[t] = soc0
        else: Aeq[t, 3*T+t-1] = -1.0
    if terminal_soc is not None:
        Aeq[T, 4*T-1] = 1.0; beq[T] = float(terminal_soc)
    Aub = np.zeros((T, n)); bub = -net * DT
    for t in range(T):
        Aub[t, t] = -1.0; Aub[t, T+t] = 1.0; Aub[t, 2*T+t] = -1.0
    bounds = ([(0.0, None)] * T + [(0.0, STEP_MAX)] * T + [(0.0, STEP_MAX)] * T + [(E_MIN, E_MAX)] * T)
    r = linprog(obj, A_ub=Aub, b_ub=bub, A_eq=Aeq, b_eq=beq, bounds=bounds, method="highs")
    if not r.success: raise RuntimeError(r.message)
    x = r.x
    return x[:T], x[T:2*T], x[2*T:3*T], np.r_[soc0, x[3*T:]], float(r.fun)


def solve_adjust(price, safe_net_power, soc0, g_plan_ref):
    p = np.asarray(price, float); net = np.asarray(safe_net_power, float); g0 = np.asarray(g_plan_ref, float); T = len(p)
    n = 6 * T; G, C, D, E, UP, DN = 0, T, 2*T, 3*T, 4*T, 5*T
    obj = np.zeros(n); obj[UP:UP+T] = 1.5 * p; obj[DN:DN+T] = -0.5 * p
    Aeq = np.zeros((2*T, n)); beq = np.zeros(2*T)
    for t in range(T):
        Aeq[t, E+t] = 1.0; Aeq[t, C+t] = -ETA; Aeq[t, D+t] = 1.0 / ETA
        if t == 0: beq[t] = soc0
        else: Aeq[t, E+t-1] = -1.0
        rr = T + t; Aeq[rr, G+t] = 1.0; Aeq[rr, UP+t] = -1.0; Aeq[rr, DN+t] = 1.0; beq[rr] = g0[t]
    Aub = np.zeros((T, n)); bub = -net * DT
    for t in range(T):
        Aub[t, G+t] = -1.0; Aub[t, C+t] = 1.0; Aub[t, D+t] = -1.0
    bounds = ([(0.0, None)] * T + [(0.0, STEP_MAX)] * T + [(0.0, STEP_MAX)] * T + [(E_MIN, E_MAX)] * T + [(0.0, None)] * T + [(0.0, None)] * T)
    r = linprog(obj, A_ub=Aub, b_ub=bub, A_eq=Aeq, b_eq=beq, bounds=bounds, method="highs")
    if not r.success: raise RuntimeError(r.message)
    x = r.x
    return x[G:G+T], x[C:C+T], x[D:D+T], np.r_[soc0, x[E:E+T]], x[UP:UP+T], x[DN:DN+T], float(r.fun)


def build_q2_forecasts():
    load_pred = np.zeros_like(LOAD); pv_pred = np.zeros_like(PV)
    for d in range(365):
        if d < 7:
            load_pred[d] = A1_LOAD; pv_pred[d] = A1_PV
        else:
            load_pred[d] = LOAD[d-7]
            hist = PV[d-7:d]
            w = np.array([0.5 ** ((6-i)/3.0) for i in range(7)], float); w /= w.sum()
            pv_pred[d] = (hist * w[:, None]).sum(axis=0)
    net_pred = load_pred - pv_pred; resid = NET_ACTUAL - net_pred
    return load_pred, pv_pred, net_pred, resid


LOAD_PRED, PV_HIST, NET_PRED, RESID = build_q2_forecasts()


def reserve_from(resid, d, idx, q=Q):
    if d <= 0: return np.zeros(len(idx))
    hist = resid[max(0, d-WINDOW):d][:, idx]
    return np.quantile(hist, q, axis=0)


def solve_q1():
    g,c,d,s,cost = solve_net(A1_PRICE, A1_LOAD-A1_PV, 6000.0, terminal_soc=6000.0)
    baseline_g = np.maximum((A1_LOAD-A1_PV)*DT, 0.0)
    baseline_cost = float((A1_PRICE * baseline_g).sum())
    np.savez_compressed(STATE/"q1.npz", g=g,ch=c,dis=d,soc=s,cost=np.array(cost), baseline_g=baseline_g,baseline_cost=np.array(baseline_cost))
    return {"cost":cost,"baseline_cost":baseline_cost}


def simulate_q2(price_matrix=None):
    soc = 6000.0
    out = {k:[] for k in ["g","ch","dis","soc0","soc1","emerg","cost","plan_cost","reserve_mean"]}
    for day in range(365):
        p = A1_PRICE if price_matrix is None else price_matrix[day]
        r = reserve_from(RESID, day, np.arange(144)); safe = NET_PRED[day] + r
        g,c,d,s,pcost = solve_net(p, safe, soc)
        emerg = np.maximum(NET_ACTUAL[day]*DT - (g+d-c), 0.0)
        cost = pcost + float((5.0*p*emerg).sum())
        out["g"].append(g); out["ch"].append(c); out["dis"].append(d); out["soc0"].append(soc); out["soc1"].append(s[-1]); out["emerg"].append(emerg); out["cost"].append(cost); out["plan_cost"].append(pcost); out["reserve_mean"].append(r.mean())
        soc = float(s[-1])
    return {k:np.array(v) for k,v in out.items()}


ISSUE_HOURS = [0,6,12,18]
START_IDX = {0:0,6:35,12:71,18:107}
SEGMENT_END = {0:144,6:71,12:107,18:144}


def build_external_10min_forecasts():
    out = np.full((365,4,144), np.nan); mins = np.arange(1,145)*10.0
    for day in range(365):
        for ki,issue in enumerate(ISSUE_HOURS):
            current = (PV[day-1,143] if day>0 else 0.0) if issue==0 else PV[day,issue*6-1]
            max_h = min(24,24-issue)
            at = np.array([issue*60] + [(issue+h)*60 for h in range(1,max_h+1)], float)
            av = np.array([current] + [FORECAST_HR[day,ki,h-1] for h in range(1,max_h+1)], float)
            mask = mins >= issue*60; out[day,ki,mask] = np.interp(mins[mask], at, av)
    return out


PV_EXT = build_external_10min_forecasts()


def build_q3_refined_forecasts():
    pv_ref = np.full_like(PV_EXT, np.nan); load_ref = np.full_like(PV_EXT, np.nan); source_ext = np.zeros((365,4), bool)
    for day in range(365):
        for ki,issue in enumerate(ISSUE_HOURS):
            st = START_IDX[issue]; idx_all = np.arange(st,144); eval_idx = np.arange(0,144) if issue==0 else np.arange(st,SEGMENT_END[issue])
            if day < 7: choose = True
            else:
                lo = max(0, day-WINDOW)
                mae_e = np.nanmean(np.abs(PV_EXT[lo:day,ki,:][:,eval_idx]-PV[lo:day][:,eval_idx]))
                mae_h = np.nanmean(np.abs(PV_HIST[lo:day][:,eval_idx]-PV[lo:day][:,eval_idx]))
                choose = bool(mae_e <= mae_h)
            source_ext[day,ki] = choose
            pv_ref[day,ki,idx_all] = PV_EXT[day,ki,idx_all] if choose else PV_HIST[day,idx_all]
            base = LOAD_PRED[day].copy()
            if issue > 0:
                end = st; obs_st = max(0,end-36)
                ratio = float(np.median(LOAD[day,obs_st:end] / (base[obs_st:end] + 1e-9))); ratio = float(np.clip(ratio,0.85,1.15)); base *= ratio
            load_ref[day,ki,idx_all] = base[idx_all]
    net_ref = load_ref - pv_ref; resid_ref = NET_ACTUAL[:,None,:] - net_ref
    return pv_ref,load_ref,net_ref,resid_ref,source_ext


PV_REF, LOAD_REF, NET_REF, RESID_REF, SOURCE_EXT = build_q3_refined_forecasts()


def reserve_q3(ki, day, idx):
    if day <= 0: return np.zeros(len(idx))
    hist = RESID_REF[max(0,day-WINDOW):day,ki,:][:,idx]
    return np.nanquantile(hist,Q,axis=0)


def simulate_q3(price_matrix=None):
    soc = 6000.0
    out = {k:[] for k in ["g_plan","g_final","ch","dis","soc0","soc1","emerg","plan_cost","adj_delta","em_cost","cost"]}
    bounds = [(0,35,0),(35,71,1),(71,107,2),(107,144,3)]
    for day in range(365):
        p = A1_PRICE if price_matrix is None else price_matrix[day]
        safe0 = NET_REF[day,0] + reserve_q3(0,day,np.arange(144))
        g0,c0,d0,s0,pcost = solve_net(p,safe0,soc)
        gf,cf,df = g0.copy(),c0.copy(),d0.copy(); current_soc = soc
        for bi,(a,b,ki) in enumerate(bounds):
            if bi == 0:
                for t in range(a,b): current_soc += ETA*cf[t] - df[t]/ETA
            else:
                rem = np.arange(a,144); safe = NET_REF[day,ki,rem] + reserve_q3(ki,day,rem)
                ga,ca,da,sp,up,dn,_ = solve_adjust(p[rem],safe,current_soc,g0[rem]); n = b-a
                gf[a:b],cf[a:b],df[a:b] = ga[:n],ca[:n],da[:n]
                for j in range(n): current_soc += ETA*ca[j] - da[j]/ETA
        emerg = np.maximum(NET_ACTUAL[day]*DT - (gf+df-cf),0.0)
        up = np.maximum(gf-g0,0.0); dn = np.maximum(g0-gf,0.0)
        adj = float((1.5*p*up - 0.5*p*dn).sum()); emc = float((5.0*p*emerg).sum()); total = pcost + adj + emc
        vals = dict(g_plan=g0,g_final=gf,ch=cf,dis=df,soc0=soc,soc1=current_soc,emerg=emerg,plan_cost=pcost,adj_delta=adj,em_cost=emc,cost=total)
        for k,v in vals.items(): out[k].append(v)
        soc = float(current_soc)
    return {k:np.array(v) for k,v in out.items()}


def main():
    q1 = solve_q1(); q2 = simulate_q2(); q3 = simulate_q3(); q42 = simulate_q2(PRICE_VAR); q43 = simulate_q3(PRICE_VAR)
    np.savez_compressed(STATE/"q2.npz", **q2); np.savez_compressed(STATE/"q3.npz", **q3); np.savez_compressed(STATE/"q4_2.npz", **q42); np.savez_compressed(STATE/"q4_3.npz", **q43)
    summary = {"q1_cost": q1["cost"], "q1_baseline_cost": q1["baseline_cost"], "q2_feb_dec_cost": float(q2["cost"][31:].sum()), "q3_feb_dec_cost": float(q3["cost"][31:].sum()), "q42_feb_dec_cost": float(q42["cost"][31:].sum()), "q43_feb_dec_cost": float(q43["cost"][31:].sum())}
    (LOGS/"solver_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8"); print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
