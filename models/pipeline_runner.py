"""
End-to-End Flood Risk Prediction Pipeline Runner
Enforces strict sequential dependency execution:
[1] Rainfall -> [2] Flood Location -> [3] Water Depth -> [4] Road Accessibility -> [5] Evacuation Recommendation
"""

import time
import numpy as np
from core.mosdac_connector import MosdacConnector
from core.fusion_engine import FusionEngine
from models.output1_rainfall import RainfallPredictionModel
from models.output2_flood_location import FloodLocationModel
from models.output3_water_depth import WaterDepthModel
from models.output4_accessibility import RoadAccessibilityModel
from models.output5_evacuation import EvacuationRecommenderModel

class FloodPredictionPipeline:
    def __init__(self, region_id="chennai_basin"):
        self.region_id = region_id
        self.mosdac = MosdacConnector()
        self.fusion = FusionEngine(region_id=region_id)
        
        # Instantiate 5 Output Models
        self.model_out1 = RainfallPredictionModel()
        self.model_out2 = FloodLocationModel()
        self.model_out3 = WaterDepthModel()
        self.model_out4 = RoadAccessibilityModel()
        self.model_out5 = EvacuationRecommenderModel()

    def set_region(self, region_id):
        if region_id != self.region_id:
            self.region_id = region_id
            self.fusion = FusionEngine(region_id=region_id)

    def run(self, lead_time="t60m", severity=1.0, river_gauge_m=None, storm_vector=(0.002, 0.003)):
        """
        Executes the 5 outputs sequentially and packages full response for GIS dashboard and APIs.
        """
        t0 = time.time()
        
        if river_gauge_m is None:
            # Scale default river level by severity
            base_lvl = self.fusion.region_meta["baseline_river_level_m"]
            danger_lvl = self.fusion.region_meta["danger_river_level_m"]
            river_gauge_m = base_lvl + (danger_lvl - base_lvl) * (severity * 0.75)

        # 1. Ingest MOSDAC satellite & radar telemetry
        sat_data = self.mosdac.fetch_live_or_simulated_satellite_grid(
            region_bounds=self.fusion.bounds,
            grid_shape=self.fusion.shape,
            intensity_scale=severity
        )
        sat_rain = np.array(sat_data["satellite_rain_rate_mmh"])
        radar_rain = sat_rain * 1.05 + np.random.normal(0, 1.0, self.fusion.shape)
        radar_rain = np.maximum(0, radar_rain)
        nwp_rain = sat_rain * 0.95

        # 2. Fuse Features & Apply Static Vulnerability
        fused = self.fusion.fuse_features(
            satellite_rain=sat_rain,
            radar_reflectivity=radar_rain,
            nwp_rain=nwp_rain,
            river_gauge_m=river_gauge_m,
            scenario_severity=severity
        )

        # 3. [OUTPUT 1] Rainfall Prediction
        out1_rainfall = self.model_out1.predict(
            initial_rain_grid=fused["fused_rain_mmh"],
            storm_vector=storm_vector,
            severity=severity,
            lead_time=lead_time
        )

        # 4. [OUTPUT 2] Flood Location Prediction
        out2_location = self.model_out2.predict(
            rainfall_pred=out1_rainfall,
            static_layers=fused["static_layers"],
            river_excess_ratio=fused["river_excess_ratio"]
        )

        # 5. [OUTPUT 3] Water Depth Prediction
        out3_depth = self.model_out3.predict(
            rainfall_pred=out1_rainfall,
            flood_location_pred=out2_location,
            static_layers=fused["static_layers"],
            river_excess_ratio=fused["river_excess_ratio"]
        )

        # 6. [OUTPUT 4] Road Accessibility Model
        out4_roads = self.model_out4.evaluate_accessibility(
            depth_pred=out3_depth,
            road_network=self.fusion.road_network,
            lats=fused["lats"],
            lons=fused["lons"]
        )

        # 7. [OUTPUT 5] Evacuation Recommendation
        out5_evacuation = self.model_out5.recommend(
            flood_loc_pred=out2_location,
            depth_pred=out3_depth,
            accessibility_pred=out4_roads,
            wards=self.fusion.wards,
            shelters=self.fusion.shelters,
            road_network=self.fusion.road_network,
            lats=fused["lats"],
            lons=fused["lons"]
        )

        exec_time_ms = round((time.time() - t0) * 1000, 1)

        # Convert numpy matrices to clean serializable formats for frontend GIS mapping
        return {
            "metadata": {
                "region_id": self.region_id,
                "region_name": self.fusion.region_meta["name"],
                "bounds": self.fusion.bounds,
                "center": self.fusion.region_meta["center"],
                "default_zoom": self.fusion.region_meta["default_zoom"],
                "lead_time": lead_time,
                "severity_multiplier": severity,
                "river_gauge_m": round(river_gauge_m, 2),
                "execution_time_ms": exec_time_ms,
                "grid_shape": list(self.fusion.shape)
            },
            "output1_rainfall": {
                "lead_time": out1_rainfall["lead_time"],
                "peak_intensity_mmh": out1_rainfall["peak_intensity_mmh"],
                "mean_intensity_mmh": out1_rainfall["mean_intensity_mmh"],
                "peak_accumulated_mm": out1_rainfall["peak_accumulated_mm"],
                "imd_category": out1_rainfall["imd_category"],
                "uncertainty_range_percent": out1_rainfall["uncertainty_range_percent"],
                "model_card": out1_rainfall["model_card"],
                "raster_grid": np.round(out1_rainfall["intensity_p50_mmh"], 2).tolist(),
                "accumulated_grid": np.round(out1_rainfall["accumulated_mm"], 2).tolist(),
                "uncertainty_p10_grid": np.round(out1_rainfall["intensity_p10_mmh"], 2).tolist(),
                "uncertainty_p90_grid": np.round(out1_rainfall["intensity_p90_mmh"], 2).tolist()
            },
            "output2_flood_location": {
                "flooded_area_sqkm": out2_location["flooded_area_sqkm"],
                "inundation_percentage": out2_location["inundation_percentage"],
                "peak_probability": out2_location["peak_probability"],
                "high_risk_cells_count": out2_location["high_risk_cells_count"],
                "model_card": out2_location["model_card"],
                "probability_grid": np.round(out2_location["flood_probability_grid"], 3).tolist(),
                "extent_mask": out2_location["flood_extent_mask"].tolist()
            },
            "output3_water_depth": {
                "max_depth_cm": out3_depth["max_depth_cm"],
                "max_depth_m": out3_depth["max_depth_m"],
                "mean_flooded_depth_cm": out3_depth["mean_flooded_depth_cm"],
                "depth_distribution": out3_depth["depth_distribution"],
                "model_card": out3_depth["model_card"],
                "depth_grid_cm": np.round(out3_depth["water_depth_grid_cm"], 1).tolist()
            },
            "output4_road_accessibility": out4_roads,
            "output5_evacuation": out5_evacuation,
            "static_gis_layers": {
                "shelters": self.fusion.shelters,
                "wards": self.fusion.wards,
                "dem_elevation": np.round(fused["static_layers"]["elevation_dem"], 1).tolist(),
                "vulnerability_index": np.round(fused["static_layers"]["composite_vulnerability"], 2).tolist(),
                "lats": fused["lats"].tolist(),
                "lons": fused["lons"].tolist()
            }
        }
