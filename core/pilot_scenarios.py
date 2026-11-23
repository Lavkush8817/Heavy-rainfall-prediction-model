"""
Pilot Scenarios Module
Defines realistic geographic domains with Digital Elevation Models (DEM),
river drainage networks, road transport topologies, population census wards, and shelter registries.
"""

import numpy as np

PILOT_REGIONS = {
    "chennai_basin": {
        "id": "chennai_basin",
        "name": "Adyar & Cooum River Delta (Chennai Basin)",
        "state": "Tamil Nadu",
        "bounds": [12.92, 80.12, 13.15, 80.30], # [lat_min, lon_min, lat_max, lon_max]
        "center": [13.04, 80.21],
        "default_zoom": 12,
        "grid_shape": [45, 45],
        "primary_river": "Adyar River / Buckingham Canal",
        "baseline_river_level_m": 4.2,
        "danger_river_level_m": 8.5,
        "description": "High-density urban delta prone to extreme monsoon inundation, reservoir discharge surges, and coastal backwater effects.",
        "shelters": [
            {"id": "S1", "name": "Anna University Indoor Stadium Relief Camp", "lat": 13.0110, "lon": 80.2350, "capacity": 3500, "current_occupancy": 450, "medical_unit": True, "boat_access": True},
            {"id": "S2", "name": "Jawaharlal Nehru Stadium Emergency Center", "lat": 13.0830, "lon": 80.2740, "capacity": 5000, "current_occupancy": 1200, "medical_unit": True, "boat_access": False},
            {"id": "S3", "name": "Tambaram Sanatorium Community Center", "lat": 12.9350, "lon": 80.1420, "capacity": 2200, "current_occupancy": 310, "medical_unit": True, "boat_access": True},
            {"id": "S4", "name": "Guindy Race Course High-Ground Camp", "lat": 13.0080, "lon": 80.2120, "capacity": 4000, "current_occupancy": 890, "medical_unit": True, "boat_access": True},
            {"id": "S5", "name": "Koyambedu High Ground Shelter Zone", "lat": 13.0710, "lon": 80.1920, "capacity": 3000, "current_occupancy": 520, "medical_unit": False, "boat_access": False}
        ],
        "wards": [
            {"id": "W-01", "name": "Saidapet Lowland Ward", "lat": 13.021, "lon": 80.222, "population": 48500, "vulnerability_index": 0.88, "base_elev_m": 6.5},
            {"id": "W-02", "name": "Kotturpuram Riverside Ward", "lat": 13.015, "lon": 80.241, "population": 36200, "vulnerability_index": 0.92, "base_elev_m": 5.2},
            {"id": "W-03", "name": "Velachery Lake Catchment", "lat": 12.978, "lon": 80.221, "population": 62000, "vulnerability_index": 0.95, "base_elev_m": 4.8},
            {"id": "W-04", "name": "Mylapore Heritage Ward", "lat": 13.036, "lon": 80.267, "population": 54000, "vulnerability_index": 0.45, "base_elev_m": 12.0},
            {"id": "W-05", "name": "T. Nagar Commercial Basin", "lat": 13.041, "lon": 80.233, "population": 71000, "vulnerability_index": 0.76, "base_elev_m": 8.1},
            {"id": "W-06", "name": "Adyar Estuary Settlement", "lat": 13.003, "lon": 80.258, "population": 29000, "vulnerability_index": 0.89, "base_elev_m": 3.9},
            {"id": "W-07", "name": "Tambaram Basin South", "lat": 12.928, "lon": 80.125, "population": 43000, "vulnerability_index": 0.81, "base_elev_m": 9.2},
            {"id": "W-08", "name": "Pallikaranai Marshland Edge", "lat": 12.939, "lon": 80.211, "population": 38000, "vulnerability_index": 0.96, "base_elev_m": 4.1},
            {"id": "W-09", "name": "Nungambakkam Central Ward", "lat": 13.060, "lon": 80.240, "population": 51000, "vulnerability_index": 0.52, "base_elev_m": 11.5},
            {"id": "W-10", "name": "Guindy Industrial Corridor", "lat": 13.009, "lon": 80.203, "population": 32000, "vulnerability_index": 0.68, "base_elev_m": 10.1}
        ]
    },
    "assam_brahmaputra": {
        "id": "assam_brahmaputra",
        "name": "Brahmaputra Valley & Kaziranga Floodplain",
        "state": "Assam",
        "bounds": [26.45, 92.80, 26.85, 93.40],
        "center": [26.65, 93.10],
        "default_zoom": 11,
        "grid_shape": [45, 45],
        "primary_river": "Brahmaputra River Mainstem",
        "baseline_river_level_m": 62.0,
        "danger_river_level_m": 71.5,
        "description": "High-discharge braided river basin with seasonal embankment breaches and critical wildlife/human settlement displacement.",
        "shelters": [
            {"id": "S-AS1", "name": "Bokakhat Higher Secondary Relief Camp", "lat": 26.620, "lon": 93.590, "capacity": 2500, "current_occupancy": 300, "medical_unit": True, "boat_access": True},
            {"id": "S-AS2", "name": "Tezpur University High Ground Campus", "lat": 26.700, "lon": 92.830, "capacity": 4500, "current_occupancy": 650, "medical_unit": True, "boat_access": True},
            {"id": "S-AS3", "name": "Kaliabor Central College Camp", "lat": 26.540, "lon": 93.020, "capacity": 3000, "current_occupancy": 400, "medical_unit": True, "boat_access": True}
        ],
        "wards": [
            {"id": "W-AS1", "name": "Silghat Riparian Settlement", "lat": 26.610, "lon": 92.930, "population": 18500, "vulnerability_index": 0.94, "base_elev_m": 58.0},
            {"id": "W-AS2", "name": "Bhuragaon Lowland Cluster", "lat": 26.550, "lon": 92.880, "population": 22400, "vulnerability_index": 0.91, "base_elev_m": 56.5},
            {"id": "W-AS3", "name": "Jakhalabandha Junction", "lat": 26.580, "lon": 93.005, "population": 31000, "vulnerability_index": 0.72, "base_elev_m": 66.0},
            {"id": "W-AS4", "name": "Kaziranga Buffer West", "lat": 26.590, "lon": 93.150, "population": 14200, "vulnerability_index": 0.96, "base_elev_m": 55.0}
        ]
    }
}

def generate_elevation_dem(bounds, shape=(45, 45), region_id="chennai_basin"):
    """
    Generates synthetic high-resolution DEM raster matching topography
    of the river basin (valleys along river courses, gentle rises inland).
    """
    lat_min, lon_min, lat_max, lon_max = bounds
    lats = np.linspace(lat_min, lat_max, shape[0])
    lons = np.linspace(lon_min, lon_max, shape[1])
    lon_grid, lat_grid = np.meshgrid(lons, lats)

    if region_id == "chennai_basin":
        # Coast is to the east (lon_max), inland elevated hills to the west (lon_min)
        # Main Adyar river runs from SW to NE into Bay of Bengal (~lat 13.00, lon 80.26)
        base_slope = 28.0 * (1.0 - (lon_grid - lon_min) / (lon_max - lon_min))
        
        # River trench 1: Adyar River corridor
        river1_lat = 12.96 + 0.45 * (lon_grid - lon_min) / (lon_max - lon_min)
        dist_river1 = np.abs(lat_grid - river1_lat)
        trench1 = 9.0 * np.exp(- (dist_river1 / 0.015)**2)

        # River trench 2: Cooum River corridor (northern)
        river2_lat = 13.07 + 0.15 * (lon_grid - lon_min) / (lon_max - lon_min)
        dist_river2 = np.abs(lat_grid - river2_lat)
        trench2 = 7.0 * np.exp(- (dist_river2 / 0.012)**2)

        # Lake depressions (Velachery / Pallikaranai)
        lake_dep = 6.0 * np.exp(- ((lat_grid - 12.95)**2 + (lon_grid - 80.21)**2) / 0.0006)

        dem = np.maximum(2.0, base_slope - trench1 - trench2 - lake_dep + np.random.normal(0, 0.4, shape))
    else:
        # Brahmaputra floodplain
        base_elev = 60.0 + 25.0 * (lat_grid - lat_min) / (lat_max - lat_min)
        river_channel = 14.0 * np.exp(- ((lat_grid - 26.62)**2) / 0.003)
        dem = np.maximum(50.0, base_elev - river_channel + np.random.normal(0, 0.8, shape))

    return dem

def generate_road_network(region_id="chennai_basin"):
    """
    Returns realistic graph nodes and edges representing major transit corridors,
    arterial roads, and secondary relief access routes.
    """
    if region_id == "chennai_basin":
        nodes = {
            "N1": {"id": "N1", "name": "Tambaram Junction", "lat": 12.925, "lon": 80.125, "elev_m": 14.0},
            "N2": {"id": "N2", "name": "Chromepet Link", "lat": 12.952, "lon": 80.142, "elev_m": 12.5},
            "N3": {"id": "N3", "name": "Airport / Meenambakkam", "lat": 12.985, "lon": 80.165, "elev_m": 11.0},
            "N4": {"id": "N4", "name": "Guindy Kathipara Flyover", "lat": 13.007, "lon": 80.203, "elev_m": 12.2},
            "N5": {"id": "N5", "name": "Saidapet Bridge Lower Arterial", "lat": 13.020, "lon": 80.224, "elev_m": 5.8}, # Low elevation bridge
            "N6": {"id": "N6", "name": "Kotturpuram River Road", "lat": 13.016, "lon": 80.240, "elev_m": 4.9}, # High flood risk
            "N7": {"id": "N7", "name": "Adyar Signal Junction", "lat": 13.006, "lon": 80.256, "elev_m": 5.2},
            "N8": {"id": "N8", "name": "Velachery 100ft Bypass", "lat": 12.978, "lon": 80.219, "elev_m": 4.2}, # Low lying road
            "N9": {"id": "N9", "name": "OMR Tidel Park Elevated Link", "lat": 12.990, "lon": 80.245, "elev_m": 9.5},
            "N10": {"id": "N10", "name": "T. Nagar Panagal Park", "lat": 13.040, "lon": 80.233, "elev_m": 8.0},
            "N11": {"id": "N11", "name": "Mylapore Luz Corner", "lat": 13.035, "lon": 80.268, "elev_m": 12.1},
            "N12": {"id": "N12", "name": "Koyambedu CMBT Hub", "lat": 13.069, "lon": 80.194, "elev_m": 10.4},
            "N13": {"id": "N13", "name": "Central Railway Corridor", "lat": 13.082, "lon": 80.275, "elev_m": 8.9},
            "N14": {"id": "N14", "name": "Pallikaranai Radial Road", "lat": 12.938, "lon": 80.205, "elev_m": 4.6}
        }
        edges = [
            {"id": "E1", "u": "N1", "v": "N2", "name": "GST Road Sector 1", "type": "National Highway", "speed_kmh": 60, "length_km": 3.4},
            {"id": "E2", "u": "N2", "v": "N3", "name": "GST Road Sector 2", "type": "National Highway", "speed_kmh": 60, "length_km": 4.1},
            {"id": "E3", "u": "N3", "v": "N4", "name": "GST Road North (Airport to Guindy)", "type": "National Highway", "speed_kmh": 50, "length_km": 4.8},
            {"id": "E4", "u": "N4", "v": "N5", "name": "Anna Salai - Saidapet River Causeway", "type": "Arterial Road", "speed_kmh": 40, "length_km": 2.6},
            {"id": "E5", "u": "N5", "v": "N6", "name": "Kotturpuram Lowland Link", "type": "Secondary Road", "speed_kmh": 30, "length_km": 1.9},
            {"id": "E6", "u": "N6", "v": "N7", "name": "Gandhi Mandapam River Road", "type": "Arterial Road", "speed_kmh": 35, "length_km": 2.2},
            {"id": "E7", "u": "N4", "v": "N8", "name": "Inner Ring Road to Velachery", "type": "Arterial Road", "speed_kmh": 45, "length_km": 3.8},
            {"id": "E8", "u": "N8", "v": "N9", "name": "Velachery-Taramani Link", "type": "Secondary Road", "speed_kmh": 30, "length_km": 3.1},
            {"id": "E9", "u": "N9", "v": "N7", "name": "OMR Rajiv Gandhi IT Expressway", "type": "Expressway", "speed_kmh": 65, "length_km": 2.5},
            {"id": "E10", "u": "N5", "v": "N10", "name": "Anna Salai to T. Nagar", "type": "Arterial Road", "speed_kmh": 35, "length_km": 2.4},
            {"id": "E11", "u": "N10", "v": "N11", "name": "Venkatnarayana to Mylapore", "type": "Secondary Road", "speed_kmh": 30, "length_km": 4.2},
            {"id": "E12", "u": "N4", "v": "N12", "name": "Jawaharlal Nehru Inner Ring (High Ground)", "type": "Highway", "speed_kmh": 60, "length_km": 7.5},
            {"id": "E13", "u": "N12", "v": "N13", "name": "EVR Periyar High Road", "type": "Arterial Road", "speed_kmh": 40, "length_km": 8.9},
            {"id": "E14", "u": "N11", "v": "N13", "name": "Kamarajar Promenade Road", "type": "Coastal Road", "speed_kmh": 45, "length_km": 5.6},
            {"id": "E15", "u": "N2", "v": "N14", "name": "Pallavaram-Thoraipakkam Radial", "type": "Arterial Road", "speed_kmh": 50, "length_km": 6.8},
            {"id": "E16", "u": "N14", "v": "N8", "name": "Pallikaranai Marsh Crossing", "type": "Secondary Road", "speed_kmh": 25, "length_km": 4.3}
        ]
    else:
        nodes = {
            "AN1": {"id": "AN1", "name": "Bokakhat Hub", "lat": 26.618, "lon": 93.588, "elev_m": 72.0},
            "AN2": {"id": "AN2", "name": "Jakhalabandha", "lat": 26.582, "lon": 93.004, "elev_m": 68.0},
            "AN3": {"id": "AN3", "name": "Silghat Ghat Link", "lat": 26.612, "lon": 92.932, "elev_m": 57.0},
            "AN4": {"id": "AN4", "name": "Tezpur Bridge South", "lat": 26.698, "lon": 92.835, "elev_m": 74.0}
        }
        edges = [
            {"id": "AE1", "u": "AN1", "v": "AN2", "name": "NH-715 Kaziranga Arterial", "type": "National Highway", "speed_kmh": 55, "length_km": 28.0},
            {"id": "AE2", "u": "AN2", "v": "AN3", "name": "Silghat Riparian Access", "type": "State Highway", "speed_kmh": 40, "length_km": 9.2},
            {"id": "AE3", "u": "AN2", "v": "AN4", "name": "Kolia Bhomora Bridge Link", "type": "National Highway", "speed_kmh": 50, "length_km": 22.5}
        ]

    return {"nodes": nodes, "edges": edges}
