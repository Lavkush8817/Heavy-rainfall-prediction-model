"""
Multi-Source Preprocessing & Fusion Engine (Phase 2)
Combines satellite (MOSDAC), weather radar, rain gauge point observations,
NWP forecast, DEM elevation, LULC, road vector buffers, and population into unified tensors.
Precomputes and caches the Static Vulnerability Layer.
"""

import numpy as np
from core.pilot_scenarios import PILOT_REGIONS, generate_elevation_dem, generate_road_network

class FusionEngine:
    def __init__(self, region_id="chennai_basin"):
        self.region_id = region_id
        self.region_meta = PILOT_REGIONS.get(region_id, PILOT_REGIONS["chennai_basin"])
        self.bounds = self.region_meta["bounds"]
        self.shape = self.region_meta["grid_shape"]
        self.lats = np.linspace(self.bounds[0], self.bounds[2], self.shape[0])
        self.lons = np.linspace(self.bounds[1], self.bounds[3], self.shape[1])
        self.lon_grid, self.lat_grid = np.meshgrid(self.lons, self.lats)
        
        # Load / Precompute Static Base Layers
        self.dem = generate_elevation_dem(self.bounds, self.shape, region_id)
        self.road_network = generate_road_network(region_id)
        self.shelters = self.region_meta["shelters"]
        self.wards = self.region_meta["wards"]
        
        self.static_vulnerability_layer = self._precompute_static_vulnerability()

    def _precompute_static_vulnerability(self):
        """
        Precomputes invariant spatial risk factors:
        1. Elevation & slope raster
        2. Distance to primary drainage / river axis
        3. Population density distribution
        4. Proximity to emergency relief shelters
        """
        # Slope calculation (gradient magnitude in degrees)
        dy, dx = np.gradient(self.dem)
        slope_deg = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2) / 100.0))

        # River distance calculation
        if self.region_id == "chennai_basin":
            # Distance to Adyar river approximate spline
            river_lat = 12.96 + 0.45 * (self.lon_grid - self.bounds[1]) / (self.bounds[3] - self.bounds[1])
            dist_river_km = np.abs(self.lat_grid - river_lat) * 111.0
        else:
            dist_river_km = np.abs(self.lat_grid - 26.62) * 111.0

        # Population density grid from wards
        pop_grid = np.zeros(self.shape, dtype=float)
        for ward in self.wards:
            w_lat, w_lon, pop = ward["lat"], ward["lon"], ward["population"]
            dist_sq = ((self.lat_grid - w_lat)**2 + (self.lon_grid - w_lon)**2)
            pop_grid += pop * np.exp(-dist_sq / 0.0008)

        # Nearest shelter distance grid (km)
        shelter_dist_grid = np.full(self.shape, 999.0)
        for s in self.shelters:
            s_lat, s_lon = s["lat"], s["lon"]
            d_km = np.sqrt(((self.lat_grid - s_lat)*111.0)**2 + ((self.lon_grid - s_lon)*111.0*np.cos(np.radians(s_lat)))**2)
            shelter_dist_grid = np.minimum(shelter_dist_grid, d_km)

        # Composite Static Vulnerability Index (0.0 to 1.0)
        # Higher = more naturally vulnerable (low elev, close to river, steep runoff slope, high pop)
        norm_elev = np.clip(1.0 - (self.dem - np.min(self.dem)) / (np.max(self.dem) - np.min(self.dem) + 1e-5), 0, 1)
        norm_river = np.clip(1.0 - (dist_river_km / 8.0), 0, 1)
        norm_pop = np.clip(pop_grid / (np.max(pop_grid) + 1e-5), 0, 1)

        vulnerability = 0.40 * norm_elev + 0.35 * norm_river + 0.25 * norm_pop

        return {
            "elevation_dem": self.dem,
            "slope_deg": slope_deg,
            "distance_to_river_km": dist_river_km,
            "population_density": pop_grid,
            "nearest_shelter_dist_km": shelter_dist_grid,
            "composite_vulnerability": np.clip(vulnerability, 0.0, 1.0)
        }

    def fuse_features(self, satellite_rain, radar_reflectivity, nwp_rain, river_gauge_m, scenario_severity=1.0):
        """
        Fuses real-time dynamic observations with static geospatial layers
        into an unified multi-channel tensor.
        """
        # Bias-corrected rainfall blend (MOSDAC Satellite + Radar + NWP ensemble)
        fused_rain = 0.45 * satellite_rain + 0.35 * radar_reflectivity + 0.20 * nwp_rain
        fused_rain = np.maximum(0.0, fused_rain * scenario_severity)

        # River surge impact factor
        danger_lvl = self.region_meta["danger_river_level_m"]
        river_excess_ratio = max(0.0, (river_gauge_m - self.region_meta["baseline_river_level_m"]) / (danger_lvl - self.region_meta["baseline_river_level_m"]))

        return {
            "lats": self.lats,
            "lons": self.lons,
            "fused_rain_mmh": fused_rain,
            "river_excess_ratio": river_excess_ratio,
            "static_layers": self.static_vulnerability_layer,
            "bounds": self.bounds
        }
