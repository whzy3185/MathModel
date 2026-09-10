from __future__ import annotations
import json, math, random, statistics, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from offline_simulator import OfflineSimulator, Source
from q3_policy import run_q3_policy


def make_case(seed:int,n:int):
    rng=random.Random(seed)
    channels=rng.sample(range(1,21),n)
    out=[]
    for ch in channels:
        rho=1800.0*math.sqrt(rng.random())
        phi=2*math.pi*rng.random()
        out.append(Source(ch,rho*math.cos(phi),rho*math.sin(phi),rng.uniform(1000,1500),None))
    return out


def one(seed:int,n:int,defer:bool,skip_detected:bool=False,harvest:bool=False,opportunistic:bool=False):
    sim=OfflineSimulator(make_case(seed,n),seed=seed^0xA5A5)
    sim.enter()
    st=run_q3_policy(sim,defer_localization_until_scan_complete=defer,skip_detected_during_cover=skip_detected,harvest_localization_during_cover=harvest,opportunistic_until_localized=opportunistic)
    cleared=sum(s.cleared for s in sim.sources.values())
    return {"cleared":cleared,"n":n,"ratio":cleared/n,"virtual_time_s":sim.virtual_time_s,
            "avg_clear_time_s":sim.virtual_time_s/max(cleared,1),"measure_calls":st.measure_calls,
            "clear_calls":st.clear_calls,"anomalies":len(st.anomalies)}


def main():
    rows={"event_driven":[],"scan_then_clear":[],"discover_once_then_clear":[],"harvest_then_clear":[],"opportunistic_then_clear":[]}
    for k in range(100):
        n=10+(k%7)
        seed=20260910+k
        rows["event_driven"].append(one(seed,n,False))
        rows["scan_then_clear"].append(one(seed,n,True,False))
        rows["discover_once_then_clear"].append(one(seed,n,True,True))
        rows["harvest_then_clear"].append(one(seed,n,True,False,True))
        rows["opportunistic_then_clear"].append(one(seed,n,True,False,False,True))
    out={}
    for name,rs in rows.items():
        out[name]={
            "cases":len(rs),
            "full_clear_cases":sum(r["ratio"]==1 for r in rs),
            "mean_clear_ratio":statistics.mean(r["ratio"] for r in rs),
            "mean_virtual_time_s":statistics.mean(r["virtual_time_s"] for r in rs),
            "median_virtual_time_s":statistics.median(r["virtual_time_s"] for r in rs),
            "mean_avg_clear_time_s":statistics.mean(r["avg_clear_time_s"] for r in rs),
            "mean_measure_calls":statistics.mean(r["measure_calls"] for r in rs),
            "mean_clear_calls":statistics.mean(r["clear_calls"] for r in rs),
            "total_anomalies":sum(r["anomalies"] for r in rs),
        }
    out["note"]="Offline development simulator only; not official-test evidence. Same 100 hidden cases are paired between strategies."
    p=ROOT/'results'/'q3_monte_carlo_v0.1.json'
    p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
