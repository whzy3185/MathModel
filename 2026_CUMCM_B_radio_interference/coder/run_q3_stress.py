from __future__ import annotations
import json, math, random, statistics, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from offline_simulator import OfflineSimulator, Source
from q3_policy import run_q3_policy


def make_case(seed,n,spatial,receive):
    rng=random.Random(seed)
    channels=rng.sample(range(1,21),n)
    pts=[]
    if spatial=='uniform':
        for _ in channels:
            rho=1800*math.sqrt(rng.random()); phi=2*math.pi*rng.random(); pts.append((rho*math.cos(phi),rho*math.sin(phi)))
    elif spatial=='boundary':
        for _ in channels:
            rho=rng.uniform(1700,1800); phi=2*math.pi*rng.random(); pts.append((rho*math.cos(phi),rho*math.sin(phi)))
    elif spatial=='clustered':
        cr=1200*math.sqrt(rng.random()); cp=2*math.pi*rng.random(); cx,cy=cr*math.cos(cp),cr*math.sin(cp)
        for _ in channels:
            for _try in range(1000):
                x=cx+rng.gauss(0,180);y=cy+rng.gauss(0,180)
                if x*x+y*y<=1800**2: break
            pts.append((x,y))
    elif spatial=='ring':
        off=rng.random()*2*math.pi
        for i,_ in enumerate(channels):
            phi=off+2*math.pi*i/n; pts.append((1799*math.cos(phi),1799*math.sin(phi)))
    else: raise ValueError(spatial)
    out=[]
    for ch,(x,y) in zip(channels,pts):
        R=1000.0 if receive=='min' else rng.uniform(1000,1500)
        out.append(Source(ch,x,y,R,None))
    return out


def run_one(seed,n,spatial,receive,error_mode):
    sim=OfflineSimulator(make_case(seed,n,spatial,receive),seed^0x55AA,error_mode=error_mode)
    sim.enter(); st=run_q3_policy(sim,defer_localization_until_scan_complete=True,opportunistic_until_localized=True)
    cleared=sum(s.cleared for s in sim.sources.values())
    return cleared/n,sim.virtual_time_s,st.measure_calls,len(st.anomalies)


def main():
    scenarios=[
        ('uniform','mixed','hash_uniform'),
        ('boundary','min','endpoint_hash'),
        ('clustered','min','plus_one'),
        ('ring','min','minus_one'),
    ]
    out={}
    for si,(spatial,receive,error_mode) in enumerate(scenarios):
        rows=[]
        for k in range(50):
            n=10+(k%7); rows.append(run_one(20261000+si*100+k,n,spatial,receive,error_mode))
        key=f'{spatial}|R={receive}|error={error_mode}'
        out[key]={
            'cases':50,
            'full_clear_cases':sum(r[0]==1.0 for r in rows),
            'mean_clear_ratio':statistics.mean(r[0] for r in rows),
            'mean_virtual_time_s':statistics.mean(r[1] for r in rows),
            'p95_virtual_time_s':sorted(r[1] for r in rows)[47],
            'mean_measure_calls':statistics.mean(r[2] for r in rows),
            'total_anomalies':sum(r[3] for r in rows),
        }
    out['note']='Offline bounded-error stress tests only; not official simulator evidence.'
    p=ROOT/'results'/'q3_stress_v0.1.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
