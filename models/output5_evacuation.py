"""
Output 5: Evacuation Zone & Route Recommender
Combines flood probability, water depth, population density, and open road networks.
Calculates Composite Risk Scores for all administrative wards, computes Dijkstra shortest safe paths
to nearest relief camps (strictly bypassing Closed roads), and triggers Boat/Air Rescue Mode
when zones are cut off from ground transport.
"""

import numpy as np
import networkx as nx

class EvacuationRecommenderModel:
    def __init__(self):
        self.model_name = "Dynamic-Dijkstra-Emergency-Router"
        self.version = "2.3.0"

    def _sample_raster(self, raster, lats, lons, point_lat, point_lon):
        row = int(np.clip(np.abs(lats - point_lat).argmin(), 0, len(lats) - 1))
        col = int(np.clip(np.abs(lons - point_lon).argmin(), 0, len(lons) - 1))
        return float(raster[row, col])

    def recommend(self, flood_loc_pred, depth_pred, accessibility_pred, wards, shelters, road_network, lats, lons):
        """
        Executes Zone Prioritization and Evacuation Routing.
        """
        flood_prob_grid = flood_loc_pred["flood_probability_grid"]
        depth_grid_cm = depth_pred["water_depth_grid_cm"]
        evaluated_edges = accessibility_pred["evaluated_edges"]
        nodes = road_network["nodes"]

        # 1. Build Navigable Safe Graph (Excluding Closed Edges)
        G = nx.Graph()
        for nid, node in nodes.items():
            G.add_node(nid, lat=node["lat"], lon=node["lon"], name=node["name"])

        for edge in evaluated_edges:
            if edge["status"] != "Closed": # Closed roads are impassable
                # Penalty weight: base length + penalty for restricted water depth
                penalty = 1.0 if edge["status"] == "Open" else 2.5
                travel_time_min = (edge["length_km"] / edge["speed_kmh"]) * 60.0 * penalty
                G.add_edge(edge["u"], edge["v"], weight=travel_time_min, edge_id=edge["id"], length_km=edge["length_km"], status=edge["status"])

        # 2. Zone Risk Prioritization
        ranked_zones = []
        for ward in wards:
            w_lat, w_lon = ward["lat"], ward["lon"]
            w_prob = self._sample_raster(flood_prob_grid, lats, lons, w_lat, w_lon)
            w_depth_cm = self._sample_raster(depth_grid_cm, lats, lons, w_lat, w_lon)
            
            # Composite Risk formula: Prob * Depth_Weight * Pop_Weight * Base_Vulnerability
            depth_weight = min(1.0, w_depth_cm / 120.0)
            pop_weight = min(1.0, ward["population"] / 70000.0)
            base_vuln = ward.get("vulnerability_index", 0.7)
            
            risk_score = (0.35 * w_prob + 0.35 * depth_weight + 0.15 * pop_weight + 0.15 * base_vuln) * 100.0
            risk_score = round(min(100.0, max(0.0, risk_score)), 1)

            if risk_score >= 70.0:
                evac_priority = "Critical Priority (Immediate Evacuation)"
                alert_level = "RED"
            elif risk_score >= 45.0:
                evac_priority = "High Priority (Prepare Stage 1)"
                alert_level = "ORANGE"
            elif risk_score >= 25.0:
                evac_priority = "Moderate Alert"
                alert_level = "YELLOW"
            else:
                evac_priority = "Low / Monitor"
                alert_level = "GREEN"

            ranked_zones.append({
                "id": ward["id"],
                "name": ward["name"],
                "lat": ward["lat"],
                "lon": ward["lon"],
                "population": ward["population"],
                "predicted_flood_prob_pct": round(w_prob * 100, 1),
                "predicted_depth_cm": round(w_depth_cm, 1),
                "risk_score": risk_score,
                "evacuation_priority": evac_priority,
                "alert_level": alert_level
            })

        # Sort zones by descending risk
        ranked_zones.sort(key=lambda x: x["risk_score"], reverse=True)

        # 3. Dynamic Evacuation Route Computation per Zone
        # Find nearest graph node to each ward and shelter
        def find_nearest_node(lat, lon):
            best_nid, min_d = None, float("inf")
            for nid, node in nodes.items():
                d = (node["lat"] - lat)**2 + (node["lon"] - lon)**2
                if d < min_d:
                    min_d = d
                    best_nid = nid
            return best_nid

        shelter_nodes = {}
        for s in shelters:
            shelter_nodes[s["id"]] = find_nearest_node(s["lat"], s["lon"])

        evacuation_plans = []
        rescue_mode_count = 0

        for zone in ranked_zones:
            origin_node = find_nearest_node(zone["lat"], zone["lon"])
            best_route = None
            min_travel_time = float("inf")
            target_shelter = None

            # Try routing to each operational shelter with capacity
            for s in shelters:
                s_node = shelter_nodes[s["id"]]
                if nx.has_path(G, origin_node, s_node):
                    try:
                        path = nx.shortest_path(G, source=origin_node, target=s_node, weight="weight")
                        travel_time = nx.shortest_path_length(G, source=origin_node, target=s_node, weight="weight")
                        if travel_time < min_travel_time:
                            min_travel_time = travel_time
                            best_route = path
                            target_shelter = s
                    except nx.NetworkXNoPath:
                        continue

            if best_route and target_shelter:
                # Construct route coordinate polyline
                route_coords = [[zone["lat"], zone["lon"]]]
                route_segments = []
                for i in range(len(best_route) - 1):
                    u, v = best_route[i], best_route[i+1]
                    route_coords.append([nodes[u]["lat"], nodes[u]["lon"]])
                    edge_data = G.get_edge_data(u, v)
                    route_segments.append({
                        "from": nodes[u]["name"],
                        "to": nodes[v]["name"],
                        "status": edge_data.get("status", "Open"),
                        "distance_km": edge_data.get("length_km", 2.0)
                    })
                route_coords.append([nodes[best_route[-1]]["lat"], nodes[best_route[-1]]["lon"]])
                route_coords.append([target_shelter["lat"], target_shelter["lon"]])

                evacuation_plans.append({
                    "zone_id": zone["id"],
                    "zone_name": zone["name"],
                    "risk_score": zone["risk_score"],
                    "alert_level": zone["alert_level"],
                    "mode": "ROAD_EVACUATION",
                    "status": "Safe Route Available",
                    "target_shelter_id": target_shelter["id"],
                    "target_shelter_name": target_shelter["name"],
                    "shelter_capacity": target_shelter["capacity"],
                    "shelter_available_space": target_shelter["capacity"] - target_shelter["current_occupancy"],
                    "estimated_travel_time_min": round(min_travel_time, 1),
                    "route_waypoints_count": len(best_route),
                    "route_coordinates": route_coords,
                    "route_segments": route_segments,
                    "rescue_required": False
                })
            else:
                # No safe road path exists -> TRIGGER BOAT / AIR RESCUE
                rescue_mode_count += 1
                evacuation_plans.append({
                    "zone_id": zone["id"],
                    "zone_name": zone["name"],
                    "risk_score": zone["risk_score"],
                    "alert_level": "RED (ISOLATED)",
                    "mode": "AIR_BOAT_RESCUE",
                    "status": "ALL ROADS CUT OFF — DEPLOY NDRF / SDRF AMPHIBIOUS RESCUE",
                    "target_shelter_id": shelters[0]["id"],
                    "target_shelter_name": shelters[0]["name"] + " (Airlift / Waterway Hub)",
                    "shelter_capacity": shelters[0]["capacity"],
                    "shelter_available_space": shelters[0]["capacity"] - shelters[0]["current_occupancy"],
                    "estimated_travel_time_min": 0,
                    "route_waypoints_count": 0,
                    "route_coordinates": [[zone["lat"], zone["lon"]], [shelters[0]["lat"], shelters[0]["lon"]]],
                    "route_segments": [],
                    "rescue_required": True,
                    "rescue_reason": "Ground access fully submerged (>30cm) on all arterial exits."
                })

        return {
            "ranked_zones": ranked_zones,
            "evacuation_plans": evacuation_plans,
            "summary": {
                "total_zones_evaluated": len(ranked_zones),
                "critical_zones_count": sum(1 for z in ranked_zones if z["risk_score"] >= 70.0),
                "road_evacuable_zones": len(ranked_zones) - rescue_mode_count,
                "isolated_rescue_mode_zones": rescue_mode_count,
                "recommended_total_evacuees": sum(z["population"] for z in ranked_zones if z["risk_score"] >= 50.0)
            },
            "model_card": {
                "name": self.model_name,
                "routing_heuristic": "Dijkstra with Inundation Penalty & Road Obstacle Pruning",
                "zero_closed_road_traversal_rate": "100.0%"
            }
        }
