/**
 * GIS Map Manager for Real-Time Flood Risk Prediction System
 * Integrates Google Maps API (Satellite, Hybrid, Terrain, Roadmap) + Leaflet GIS Overlays
 */

class GISMapManager {
  constructor(mapContainerId) {
    this.containerId = mapContainerId;
    this.map = null;
    this.googleApiKey = "YOUR_GOOGLE_MAPS_API_KEY";
    this.currentBasemapKey = "google_hybrid";
    
    this.basemaps = {};
    this.layers = {
      rainfall: L.layerGroup(),
      floodExtent: L.layerGroup(),
      waterDepth: L.layerGroup(),
      roads: L.layerGroup(),
      evacRoutes: L.layerGroup(),
      shelters: L.layerGroup(),
      wards: L.layerGroup()
    };
    
    this.activeLayers = {
      rainfall: true,
      floodExtent: true,
      waterDepth: true,
      roads: true,
      evacRoutes: true,
      shelters: true,
      wards: true
    };
    
    this.currentData = null;
    this.onInspectCallback = null;
  }

  init(center = [13.04, 80.21], zoom = 12) {
    if (this.map) {
      this.map.remove();
    }

    this.map = L.map(this.containerId, {
      center: center,
      zoom: zoom,
      zoomControl: false,
      maxZoom: 20
    });

    L.control.zoom({ position: 'bottomright' }).addTo(this.map);

    // Google Maps Tile Layers using Google API Key
    const key = this.googleApiKey;
    this.basemaps = {
      google_hybrid: L.tileLayer(`https://mt{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}&key=${key}`, {
        subdomains: '0123',
        maxZoom: 20,
        attribution: '&copy; Google Maps &copy; ISRO MOSDAC'
      }),
      google_satellite: L.tileLayer(`https://mt{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}&key=${key}`, {
        subdomains: '0123',
        maxZoom: 20,
        attribution: '&copy; Google Maps Satellite'
      }),
      google_terrain: L.tileLayer(`https://mt{s}.google.com/vt/lyrs=p&x={x}&y={y}&z={z}&key=${key}`, {
        subdomains: '0123',
        maxZoom: 20,
        attribution: '&copy; Google Maps Terrain & Elevation'
      }),
      google_roadmap: L.tileLayer(`https://mt{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}&key=${key}`, {
        subdomains: '0123',
        maxZoom: 20,
        attribution: '&copy; Google Maps'
      }),
      carto_dark: L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        subdomains: 'abcd',
        maxZoom: 19,
        attribution: '&copy; Carto Dark Matter &copy; OpenStreetMap'
      })
    };

    // Set default basemap (Google Hybrid)
    this.basemaps[this.currentBasemapKey].addTo(this.map);

    // Add all analytical overlay layer groups
    Object.values(this.layers).forEach(layer => layer.addTo(this.map));

    // Map click inspect listener
    this.map.on('click', (e) => {
      if (this.onInspectCallback) {
        this.onInspectCallback(e.latlng);
      }
    });
  }

  setBasemap(basemapKey) {
    if (this.basemaps[basemapKey]) {
      // Remove current basemap
      if (this.basemaps[this.currentBasemapKey] && this.map.hasLayer(this.basemaps[this.currentBasemapKey])) {
        this.map.removeLayer(this.basemaps[this.currentBasemapKey]);
      }
      this.currentBasemapKey = basemapKey;
      this.basemaps[basemapKey].addTo(this.map);
      this.basemaps[basemapKey].bringToBack();
    }
  }

  setInspectCallback(cb) {
    this.onInspectCallback = cb;
  }

  toggleLayer(layerKey, isVisible) {
    this.activeLayers[layerKey] = isVisible;
    if (this.layers[layerKey]) {
      if (isVisible) {
        if (!this.map.hasLayer(this.layers[layerKey])) {
          this.layers[layerKey].addTo(this.map);
        }
      } else {
        if (this.map.hasLayer(this.layers[layerKey])) {
          this.map.removeLayer(this.layers[layerKey]);
        }
      }
    }
  }

  updateAllLayers(data) {
    this.currentData = data;
    
    // Clear previous elements
    Object.values(this.layers).forEach(layer => layer.clearLayers());

    const meta = data.metadata;
    const lats = data.static_gis_layers.lats;
    const lons = data.static_gis_layers.lons;
    const numRows = lats.length;
    const numCols = lons.length;
    const latStep = (lats[numRows - 1] - lats[0]) / (numRows - 1);
    const lonStep = (lons[numCols - 1] - lons[0]) / (numCols - 1);

    // 1. Render Rainfall Raster Heatmap
    const rainGrid = data.output1_rainfall.raster_grid;
    for (let r = 0; r < numRows; r += 2) {
      for (let c = 0; c < numCols; c += 2) {
        const val = rainGrid[r][c];
        if (val > 5.0) {
          const lat = lats[r];
          const lon = lons[c];
          const color = val > 65 ? '#dc2626' : val > 35 ? '#ea580c' : val > 15 ? '#ca8a04' : '#0284c7';
          const opacity = Math.min(0.65, val / 110.0);

          const rect = L.rectangle([
            [lat - latStep, lon - lonStep],
            [lat + latStep, lon + lonStep]
          ], {
            color: 'transparent',
            fillColor: color,
            fillOpacity: opacity,
            interactive: false
          });
          this.layers.rainfall.addLayer(rect);
        }
      }
    }

    // 2. Render Inundation Extent & Depth 2D Raster
    const depthGrid = data.output3_water_depth.depth_grid_cm;
    const floodProbGrid = data.output2_flood_location.probability_grid;

    for (let r = 0; r < numRows; r++) {
      for (let c = 0; c < numCols; c++) {
        const depthCm = depthGrid[r][c];
        const prob = floodProbGrid[r][c];

        if (depthCm > 5.0 && prob > 0.3) {
          const lat = lats[r];
          const lon = lons[c];

          // High visibility hydrodynamic color palette
          let depthColor = '#38bdf8'; // <15cm Cyan
          if (depthCm > 100.0) depthColor = '#991b1b'; // >1m Maroon
          else if (depthCm > 50.0) depthColor = '#dc2626'; // 50cm-1m Crimson
          else if (depthCm > 30.0) depthColor = '#f97316'; // 30-50cm Orange
          else if (depthCm > 15.0) depthColor = '#eab308'; // 15-30cm Amber

          const opacity = Math.min(0.85, 0.40 + (depthCm / 140.0));

          const cellRect = L.rectangle([
            [lat - latStep / 2, lon - lonStep / 2],
            [lat + latStep / 2, lon + lonStep / 2]
          ], {
            color: 'transparent',
            fillColor: depthColor,
            fillOpacity: opacity
          });

          cellRect.bindPopup(`
            <div style="font-family: 'Outfit', sans-serif; font-size: 12px; color: #111; padding: 4px;">
              <strong style="color: #0369a1;">🌊 Water Depth:</strong> ${depthCm.toFixed(1)} cm (${(depthCm/100).toFixed(2)} m)<br>
              <strong>Probability:</strong> ${(prob * 100).toFixed(1)}%<br>
              <strong>Terrain Elevation:</strong> ${data.static_gis_layers.dem_elevation[r][c]} m
            </div>
          `);

          this.layers.waterDepth.addLayer(cellRect);
        }
      }
    }

    // 3. Render Road Network Segments
    const edges = data.output4_road_accessibility.evaluated_edges;
    edges.forEach(edge => {
      const weight = edge.status === 'Closed' ? 6 : edge.status === 'Restricted' ? 5 : 4;
      const dash = edge.status === 'Closed' ? '6, 6' : null;

      const polyline = L.polyline([edge.u_coords, edge.v_coords], {
        color: edge.color,
        weight: weight,
        opacity: 0.95,
        dashArray: dash
      });

      polyline.bindPopup(`
        <div style="font-family: 'Outfit', sans-serif; font-size: 12px; color: #111; padding: 4px;">
          <h4 style="margin: 0 0 4px 0; color: #0f172a;">${edge.name}</h4>
          <strong>Type:</strong> ${edge.type}<br>
          <strong>Status:</strong> <span style="color: ${edge.color}; font-weight: bold;">${edge.status.toUpperCase()}</span><br>
          <strong>Max Water Depth:</strong> ${edge.max_water_depth_cm} cm<br>
          <strong>Access:</strong> ${edge.vehicle_access}
        </div>
      `);

      this.layers.roads.addLayer(polyline);
    });

    // 4. Render Evacuation Routes
    const plans = data.output5_evacuation.evacuation_plans;
    plans.forEach(plan => {
      if (plan.mode === 'ROAD_EVACUATION' && plan.route_coordinates.length > 1) {
        const routeLine = L.polyline(plan.route_coordinates, {
          color: '#10b981',
          weight: 5,
          opacity: 0.95,
          dashArray: '8, 8'
        });

        routeLine.bindPopup(`
          <div style="font-family: 'Outfit', sans-serif; font-size: 12px; color: #111; padding: 4px;">
            <strong style="color: #059669;">🛣️ Safe Evacuation Route</strong><br>
            <strong>Origin:</strong> ${plan.zone_name}<br>
            <strong>Shelter:</strong> ${plan.target_shelter_name}<br>
            <strong>Travel Time:</strong> ${plan.estimated_travel_time_min} mins
          </div>
        `);

        this.layers.evacRoutes.addLayer(routeLine);
      } else if (plan.mode === 'AIR_BOAT_RESCUE') {
        const rescueIcon = L.divIcon({
          className: 'rescue-pulsing-icon',
          html: `<div style="background: #ec4899; color: white; font-weight: bold; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 16px #ec4899; border: 2px solid white; font-size: 15px;">🚁</div>`,
          iconSize: [30, 30],
          iconAnchor: [15, 15]
        });

        const rescueMarker = L.marker(plan.route_coordinates[0], { icon: rescueIcon });
        rescueMarker.bindPopup(`
          <div style="font-family: 'Outfit', sans-serif; font-size: 12px; color: #111; padding: 4px;">
            <strong style="color: #be123c;">⚠️ RESCUE MODE ACTIVATED</strong><br>
            <strong>Zone:</strong> ${plan.zone_name}<br>
            <strong>Reason:</strong> ${plan.rescue_reason}<br>
            <strong>Airlift Hub:</strong> ${plan.target_shelter_name}
          </div>
        `);
        this.layers.evacRoutes.addLayer(rescueMarker);
      }
    });

    // 5. Render Shelters
    const shelters = data.static_gis_layers.shelters;
    shelters.forEach(s => {
      const occPct = Math.round((s.current_occupancy / s.capacity) * 100);
      const shelterIcon = L.divIcon({
        className: 'shelter-icon',
        html: `<div style="background: #0284c7; color: white; font-weight: bold; border-radius: 8px; padding: 4px 8px; border: 1px solid #38bdf8; font-size: 11px; white-space: nowrap; box-shadow: 0 4px 12px rgba(0,0,0,0.6);">🏠 ${s.name.split(' ')[0]} (${occPct}%)</div>`,
        iconAnchor: [40, 15]
      });

      const marker = L.marker([s.lat, s.lon], { icon: shelterIcon });
      marker.bindPopup(`
        <div style="font-family: 'Outfit', sans-serif; font-size: 12px; color: #111; padding: 4px;">
          <h4 style="margin: 0 0 4px 0; color: #0284c7;">🏠 ${s.name}</h4>
          <strong>Capacity:</strong> ${s.capacity} persons<br>
          <strong>Occupancy:</strong> ${s.current_occupancy} (${occPct}%)<br>
          <strong>Free Space:</strong> ${s.capacity - s.current_occupancy}<br>
          <strong>Medical Unit:</strong> ${s.medical_unit ? '✅ Ready' : '❌ None'}<br>
          <strong>Boat Jetty:</strong> ${s.boat_access ? '✅ Accessible' : '❌ No'}
        </div>
      `);
      this.layers.shelters.addLayer(marker);
    });

    // 6. Render Wards
    const wards = data.static_gis_layers.wards;
    wards.forEach(w => {
      const wardCircle = L.circleMarker([w.lat, w.lon], {
        radius: 6,
        fillColor: '#93c5fd',
        color: '#ffffff',
        weight: 2,
        opacity: 0.9,
        fillOpacity: 0.75
      });
      wardCircle.bindPopup(`
        <div style="font-family: 'Outfit', sans-serif; font-size: 12px; color: #111; padding: 4px;">
          <strong>Ward:</strong> ${w.name} (${w.id})<br>
          <strong>Population:</strong> ${w.population.toLocaleString()}<br>
          <strong>Base Elevation:</strong> ${w.base_elev_m} m
        </div>
      `);
      this.layers.wards.addLayer(wardCircle);
    });
  }

  panTo(lat, lon, zoom = 14) {
    if (this.map) {
      this.map.flyTo([lat, lon], zoom, { animate: true, duration: 1.2 });
    }
  }
}

window.GISMapManager = GISMapManager;
