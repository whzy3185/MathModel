from __future__ import annotations
import json,math,random,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from offline_simulator import OfflineSimulator,Source
from q4_policy import run_q4_policy


def case(seed,n,directed_fraction=1.0,Rmin=True):
    rng=random.Random(seed);chs=rng.sample(range(1,21),n);out=[]
    for i,ch in enumerate(chs):
        rho=rng.uniform(0,1800) if i%2 else rng.uniform(1650,1800)
        ph=2*math.pi*rng.random();direction=(rng.uniform(0,360) if rng.random()<directed_fraction else None)
        R=1000.0 if Rmin else rng.uniform(1000,1500)
        out.append(Source(ch,rho*math.cos(ph),rho*math.sin(ph),R,direction))
    return out


def run(seed,n,frac,error):
    sim=OfflineSimulator(case(seed,n,frac,True),seed^0x7777,error_mode=error);sim.enter();st=run_q4_policy(sim)
    c=sum(s.cleared for s in sim.sources.values())
    return c/n,sim.virtual_time_s,st.measure_calls,st.fallback_steps,len(st.anomalies)


def main():
    scenarios=[(0.0,'endpoint_hash'),(0.5,'endpoint_hash'),(1.0,'endpoint_hash'),(1.0,'plus_one'),(1.0,'minus_one')]
    out={}
    for si,(frac,error) in enumerate(scenarios):
        rows=[]
        for k in range(20):
            n=10+(k%7);rows.append(run(20262000+si*100+k,n,frac,error))
        out[f'directed={frac}|R=1000|error={error}']={
            'cases':20,'full_clear_cases':sum(r[0]==1 for r in rows),'mean_clear_ratio':statistics.mean(r[0] for r in rows),
            'mean_virtual_time_s':statistics.mean(r[1] for r in rows),'max_virtual_time_s':max(r[1] for r in rows),
            'mean_measure_calls':statistics.mean(r[2] for r in rows),'mean_fallback_steps':statistics.mean(r[3] for r in rows),
            'total_anomalies':sum(r[4] for r in rows)}
    out['note']='Offline worst-radius bounded-error stress only; not official simulator evidence.'
    p=ROOT/'results'/'q4_stress_v0.1.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
