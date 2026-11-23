import time
from models.pipeline_runner import FloodPredictionPipeline
from core.backtester import BacktestingSuite
from core.mosdac_connector import MosdacConnector

def run_live_demonstration():
    print("=====================================================================")
    print(">> REAL-TIME FLOOD RISK PREDICTION SYSTEM - LIVE DEMONSTRATION")
    print(">> Satellite (MOSDAC) + Radar + NWP + DEM + OSM GIS + AI/ML Pipeline")
    print("=====================================================================\n")

    # Step 0: MOSDAC Configuration Check
    print("[PHASE 0 & 1] Checking MOSDAC Ingestion Bridge & Dataset Settings...")
    mosdac = MosdacConnector("config.json")
    status = mosdac.get_status()
    print(f"  * Configured Status : {'LOADED' if status['configured'] else 'NOT FOUND'}")
    print(f"  * Active Dataset ID : {status['dataset_id']}")
    print(f"  * Ingestion Channel : {status['username']}")
    print(f"  * Telemetry Source  : INSAT-3DR / HEM Hydro-Estimator Satellite Feed\n")

    # Step 1: Initialize Pipeline
    print("[PHASE 2] Initializing Multi-Source Fusion Engine & Pilot Domain...")
    pipeline = FloodPredictionPipeline(region_id="chennai_basin")
    print(f"  * Pilot Domain      : {pipeline.fusion.region_meta['name']}")
    print(f"  * Grid Dimensions   : 45 x 45 (0.01 deg Resolution ~1km Grid Cells)")
    print(f"  * Static Layers     : DEM Elevation, Slope, Drainage Trenches, OSM Road Graph, Shelters\n")

    # Step 2: Sequential 5-Output Pipeline Execution
    print("[PHASE 3] Executing Sequential 5-Output Pipeline Chain (Lead Time: T+60m)...")
    t_start = time.time()
    res = pipeline.run(lead_time="t60m", severity=1.3)
    duration_ms = round((time.time() - t_start) * 1000, 1)

    out1 = res["output1_rainfall"]
    print("\n---------------------------------------------------------------------")
    print("[OUTPUT 1] Spatio-Temporal Rainfall Prediction (Nowcast + Uncertainty)")
    print(f"  * Peak Rain Rate    : {out1['peak_intensity_mmh']} mm/hr")
    print(f"  * IMD Alert Category: {out1['imd_category']}")
    print(f"  * Uncertainty Bounds: P10 / P50 / P90 (+/-{out1['uncertainty_range_percent']}% Confidence Envelope)")
    print(f"  * Model Architecture: {out1['model_card']['name']}")

    out2 = res["output2_flood_location"]
    print("\n---------------------------------------------------------------------")
    print("[OUTPUT 2] Flood Location Prediction ('Where')")
    print(f"  * Inundation Extent : {out2['flooded_area_sqkm']} km2 ({out2['inundation_percentage']}% of domain)")
    print(f"  * High Risk Cells   : {out2['high_risk_cells_count']} cells with >75% flood probability")
    print(f"  * Sentinel-1 SAR IoU: {out2['model_card']['extent_IoU_val']}")

    out3 = res["output3_water_depth"]
    print("\n---------------------------------------------------------------------")
    print("[OUTPUT 3] Water Depth Prediction ('How Deep')")
    print(f"  * Peak Water Depth  : {out3['max_depth_cm']} cm ({out3['max_depth_m']} meters)")
    print(f"  * Mean Flooded Depth: {out3['mean_flooded_depth_cm']} cm")
    print(f"  * Depth Distribution: >1m Deep: {out3['depth_distribution']['deep_gt_1m_cells']} cells | Impassable (30cm-1m): {out3['depth_distribution']['impassable_30cm_to_1m_cells']} cells")

    out4 = res["output4_road_accessibility"]
    print("\n---------------------------------------------------------------------")
    print("[OUTPUT 4] Road & Area Accessibility Model ('What is Blocked')")
    print(f"  * Road Network Stats: {out4['summary']['total_segments']} Total Segments Evaluated")
    print(f"  * Open (<15cm)      : {out4['summary']['open_count']} segments (Green)")
    print(f"  * Restricted (15-30): {out4['summary']['restricted_count']} segments (Yellow - High Clearance Only)")
    print(f"  * Closed (>30cm)    : {out4['summary']['closed_count']} segments (Red - Impassable)")
    print(f"  * Impassable Length : {out4['summary']['total_impassable_length_km']} km of flooded arterial links")

    out5 = res["output5_evacuation"]
    print("\n---------------------------------------------------------------------")
    print("[OUTPUT 5] Evacuation Zone & Safe Route Recommendation")
    print(f"  * Critical Wards    : {out5['summary']['critical_zones_count']} wards flagged for immediate evacuation")
    print(f"  * Priority Evacuees : {out5['summary']['recommended_total_evacuees']:,} citizens")
    print("\n  Top High-Risk Priority Zones & Routing Plans:")
    for i, plan in enumerate(out5["evacuation_plans"][:4], 1):
        mode_str = "[RESCUE MODE: AIR/BOAT]" if plan["mode"] == "AIR_BOAT_RESCUE" else "[SAFE ROAD ROUTE]"
        print(f"    {i}. Zone: {plan['zone_name']} (Risk: {plan['risk_score']}/100) -> {mode_str}")
        print(f"       Status : {plan['status']}")
        print(f"       Shelter: {plan['target_shelter_name']} (Free Space: {plan['shelter_available_space']})")
        if plan["mode"] == "ROAD_EVACUATION":
            print(f"       Route  : {plan['estimated_travel_time_min']} mins via {plan['route_waypoints_count']} open waypoints")
        else:
            print(f"       Notice : {plan.get('rescue_reason')}")

    print("\n=====================================================================")
    print(f">> PIPELINE PERFORMANCE: Executed all 5 outputs end-to-end in {duration_ms} ms")
    print(f">> Mission Command Dashboard live at: http://127.0.0.1:8000")
    print("=====================================================================\n")

if __name__ == "__main__":
    run_live_demonstration()
