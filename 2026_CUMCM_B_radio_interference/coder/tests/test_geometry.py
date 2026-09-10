import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from geometry import diameter_circle_covers, localization_region, minimum_enclosing_circle, point_satisfies_region, polygon_diameter
from search_policy import omni_guaranteed_scan_points, triangular_directional_scan_points
from q2_candidate_region import conservative_max_distance, robust_symmetric_second_points


class GeometryTests(unittest.TestCase):
    def test_two_station_contains_true_source(self):
        g = (500.0, 600.0)
        sensors = [(0.0, 0.0), (1000.0, 0.0)]
        bearings = [math.degrees(math.atan2(g[1], g[0])), math.degrees(math.atan2(g[1], g[0]-1000.0))]
        reg = localization_region(sensors, bearings, 1.0)
        self.assertEqual(reg.status, "BOUNDED")
        self.assertTrue(point_satisfies_region(g, reg))
        self.assertGreater(reg.diameter, 0.0)

    def test_nearly_parallel_can_be_unbounded(self):
        reg = localization_region([(0,0),(0,100)], [0,0], 1.0)
        self.assertEqual(reg.status, "UNBOUNDED")
        self.assertTrue(math.isinf(reg.diameter))

    def test_diameter_circle_not_always_cover(self):
        D = 100.0
        tri = [(0.0,0.0),(D,0.0),(D/2,math.sqrt(3)*D/2)]
        d,_ = polygon_diameter(tri)
        self.assertAlmostEqual(d,D,places=8)
        ok,_,r = diameter_circle_covers(tri)
        self.assertFalse(ok)
        self.assertAlmostEqual(r,D/2,places=8)

    def test_rectangle_diameter_circle_does_cover(self):
        rect=[(0,0),(4,0),(4,2),(0,2)]
        ok,_,_=diameter_circle_covers(rect)
        self.assertTrue(ok)

    def test_minimum_enclosing_circle_triangle(self):
        D=100.0
        tri=[(0.0,0.0),(D,0.0),(D/2,math.sqrt(3)*D/2)]
        _,r=minimum_enclosing_circle(tri)
        self.assertAlmostEqual(r,D/math.sqrt(3),places=7)

    def test_q2_robust_second_points_guarantee_receive(self):
        p1,p2=robust_symmetric_second_points((0.0,0.0),35.0)
        for p in (p1,p2):
            self.assertLessEqual(math.hypot(*p),1000.000001)
            self.assertLessEqual(conservative_max_distance((0.0,0.0),35.0,p),1000.000001)

    def test_q3_seven_point_cover_dense_grid(self):
        pts=omni_guaranteed_scan_points()
        for ir in range(0,181,2):
            rho=10.0*ir
            for k in range(360):
                phi=2*math.pi*k/360
                p=(rho*math.cos(phi),rho*math.sin(phi))
                self.assertLessEqual(min(math.hypot(p[0]-q[0],p[1]-q[1]) for q in pts),1000.000001)

    def test_q4_triangular_patch_halfplane_visibility(self):
        pts=triangular_directional_scan_points(spacing=1000.0)
        # Dense source/orientation test.  This numerically checks the analytic convex-hull proof.
        for rho in [0,300,900,1500,1799]:
            for ak in range(0,360,15):
                g=(rho*math.cos(math.radians(ak)),rho*math.sin(math.radians(ak)))
                nearby=[p for p in pts if math.hypot(p[0]-g[0],p[1]-g[1])<=1000.000001]
                self.assertTrue(nearby)
                for dk in range(0,360,15):
                    d=(math.cos(math.radians(dk)),math.sin(math.radians(dk)))
                    self.assertTrue(any(d[0]*(p[0]-g[0])+d[1]*(p[1]-g[1])>=-1e-8 for p in nearby))


if __name__ == "__main__":
    unittest.main()
