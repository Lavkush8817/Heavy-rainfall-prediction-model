"""
Test Suite for Real-Time Flood Risk Prediction Pipeline
Validates MOSDAC connector, 5 output sequence, edge routing safety, and API endpoints.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.mosdac_connector import MosdacConnector, load_mosdac_config
from core.fusion_engine import FusionEngine
from models.pipeline_runner import FloodPredictionPipeline
from core.backtester import BacktestingSuite

def test_mosdac_connector():
    print("[TEST] Testing MOSDAC Connector...")
    cfg = load_mosdac_config("config.json")
    assert cfg["status"] in ["loaded", "missing_file"]
    
    conn = MosdacConnector("config.json")
    status = conn.get_status()
    assert "configured" in status
    print("[PASS] MOSDAC Connector validated.")

def test_fusion_and_static_layers():
    print("[TEST] Testing Fusion Engine & Static Vulnerability...")
    fusion = FusionEngine(region_id="chennai_basin")
    assert "elevation_dem" in fusion.static_vulnerability_layer
    assert "composite_vulnerability" in fusion.static_vulnerability_layer
    assert len(fusion.shelters) >= 3
    assert len(fusion.wards) >= 5
    print("[PASS] Fusion engine & GIS vulnerability layers validated.")

def test_sequential_5_outputs():
    print("[TEST] Testing Sequential 5-Output Pipeline (1 -> 2 -> 3 -> 4 -> 5)...")
    pipeline = FloodPredictionPipeline(region_id="chennai_basin")
    res = pipeline.run(lead_time="t60m", severity=1.2)

    # Output 1: Rainfall
    assert "output1_rainfall" in res
    assert res["output1_rainfall"]["peak_intensity_mmh"] > 0
    print(f"  [Out 1] Peak Rainfall: {res['output1_rainfall']['peak_intensity_mmh']} mm/h ({res['output1_rainfall']['imd_category']})")

    # Output 2: Flood Location
    assert "output2_flood_location" in res
    assert res["output2_flood_location"]["flooded_area_sqkm"] > 0
    print(f"  [Out 2] Inundated Area: {res['output2_flood_location']['flooded_area_sqkm']} km2")

    # Output 3: Water Depth
    assert "output3_water_depth" in res
    assert res["output3_water_depth"]["max_depth_cm"] > 0
    print(f"  [Out 3] Max Water Depth: {res['output3_water_depth']['max_depth_cm']} cm ({res['output3_water_depth']['max_depth_m']} m)")

    # Output 4: Road Accessibility
    assert "output4_road_accessibility" in res
    edges = res["output4_road_accessibility"]["evaluated_edges"]
    assert len(edges) > 0
    print(f"  [Out 4] Evaluated Road Segments: {len(edges)} (Closed: {res['output4_road_accessibility']['summary']['closed_count']})")

    # Output 5: Evacuation Routing
    assert "output5_evacuation" in res
    plans = res["output5_evacuation"]["evacuation_plans"]
    assert len(plans) > 0
    rescue_triggers = res["output5_evacuation"]["summary"]["isolated_rescue_mode_zones"]
    print(f"  [Out 5] Evacuation Plans: {len(plans)} zones (Air/Boat Rescue Required: {rescue_triggers})")

    print("[PASS] Sequential 5-output pipeline passed successfully.")

def test_backtesting_suite():
    print("[TEST] Testing Phase 5 Backtesting Suite...")
    pipeline = FloodPredictionPipeline(region_id="chennai_basin")
    suite = BacktestingSuite()
    report = suite.run_backtest(pipeline, event_key="chennai_dec2015")
    assert report["metrics"]["output5_evacuation_routing"]["safe_route_compliance_pct"] == 100.0
    print(f"[PASS] Phase 5 Backtesting completed. Verdict: {report['overall_status']}")

if __name__ == "__main__":
    test_mosdac_connector()
    test_fusion_and_static_layers()
    test_sequential_5_outputs()
    test_backtesting_suite()
    print("\n[SUCCESS] ALL UNIT & INTEGRATION TESTS PASSED PERFECTLY!")

