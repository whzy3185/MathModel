import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from offline_simulator import OfflineSimulator, Source


class OfflineSimulatorTests(unittest.TestCase):
    def test_timing_and_channel_semantics(self):
        sim=OfflineSimulator([Source(3,300,0,1200,None)])
        self.assertTrue(sim.enter()["accepted"])
        r=sim.measure(300,400,1)
        self.assertAlmostEqual(r["virtual_time_s"],105.0)
        r=sim.measure(300,400,2)
        self.assertAlmostEqual(r["virtual_time_s"],111.0)
        r=sim.clear(300,0,3)
        self.assertEqual(r["clear_result"],"success")
        # move 400/5 + success clear 5 = 85 => 196
        self.assertAlmostEqual(r["virtual_time_s"],196.0)
        # /clear did not change current measure channel (still 2)
        r=sim.measure(300,0,2)
        self.assertAlmostEqual(r["virtual_time_s"],201.0)

    def test_directional_visibility_and_clear_independence(self):
        # Source points east; receiver west is blind, east is visible.
        sim=OfflineSimulator([Source(5,0,0,1000,0.0)])
        sim.enter()
        self.assertEqual(sim.measure(-100,0,5)["measure_result"],"no_signal")
        self.assertEqual(sim.measure(100,0,5)["measure_result"],"direction")
        # Clear ignores directional coverage.
        self.assertEqual(sim.clear(-10,0,5)["clear_result"],"success")


if __name__ == "__main__":
    unittest.main()
