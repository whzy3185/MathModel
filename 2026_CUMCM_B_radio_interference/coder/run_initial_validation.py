from __future__ import annotations
import json, math, random, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from geometry import localization_region, point_satisfies_region, diameter_circle_covers
from q2_candidate_region import recommend_second_point, robust_symmetric_second_points, conservative_max_distance
from search_policy import omni_guaranteed_scan_points, triangular_directional_scan_points


def main():
    rng=random.Random(20260910)
    contain_ok=0
    bounded=0
    for _ in range(300):
        # True source well inside target disk; sensors on a surrounding ring with varied geometry.
        rr=1500*math.sqrt(rng.random()); ph=2*math.pi*rng.random()
        g=(rr*math.cos(ph),rr*math.sin(ph))
        sensors=[]; bearings=[]
        for k in range(3):
            ang=2*math.pi*(k/3)+rng.uniform(-0.2,0.2)
            s=(1200*math.cos(ang),1200*math.sin(ang))
            true=math.degrees(math.atan2(g[1]-s[1],g[0]-s[0]))%360
            err=rng.uniform(-1,1)
            sensors.append(s); bearings.append((true+err)%360)
        reg=localization_region(sensors,bearings,1.0)
        if reg.status=='BOUNDED':
            bounded+=1
        if reg.status!='EMPTY' and point_satisfies_region(g,reg,1e-6):
            contain_ok+=1
    best, top = recommend_second_point((0.0,0.0),35.0,n_source_samples=1200,min_guarantee_rate=0.6)
    rp, rm = robust_symmetric_second_points((0.0,0.0),35.0)
    output={
        'seed':20260910,
        'q1_random_cases':300,
        'q1_true_source_contained':contain_ok,
        'q1_bounded_regions':bounded,
        'q2_demo':{
            'S1':[0.0,0.0],
            'bearing_deg':35.0,
            'recommended_S2':[round(best.point[0],3),round(best.point[1],3)],
            'score':round(best.score,6),
            'guaranteed_detection_rate_under_R1000':round(best.guaranteed_detection_rate,6),
            'q10_crossing_angle_deg':round(best.q10_angle_deg,3),
            'median_crossing_angle_deg':round(best.median_angle_deg,3),
            'move_distance_m':round(best.move_distance,3),
            'note':'Q2 demo depends on an explicitly declared design prior; it is not an official-simulator result.'
        },
        'q2_distribution_free':{
            'candidate_plus':[round(rp[0],3),round(rp[1],3)],
            'candidate_minus':[round(rm[0],3),round(rm[1],3)],
            'move_distance_m':round(math.hypot(rp[0],rp[1]),3),
            'worst_distance_to_conservative_sector_m':round(conservative_max_distance((0.0,0.0),35.0,rp),6),
            'guaranteed_omni_detection_under_Rmin1000':True,
            'note':'Distribution-free conservative construction; primary Q2 evidence.'
        },
        'q3_guaranteed_scan_points':len(omni_guaranteed_scan_points()),
        'q4_safe_triangular_patch_points_s1000':len(triangular_directional_scan_points(spacing=1000.0)),
    }
    p=ROOT/'results'/'initial_validation.json'
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(output,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
