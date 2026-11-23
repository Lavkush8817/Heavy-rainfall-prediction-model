# SIH Nexus — Real-Time Flood Risk Prediction System

Satellite + Weather Radar + Rain Gauge + Weather Station + NWP + GIS + AI/ML.
Built for Smart India Hackathon.

## What it does — 5 output products

1. **Rainfall Prediction** — how much rain, where, and when (nowcast + short-range)
2. **Flood Location Prediction** — which specific areas will flood
3. **Water Depth Prediction** — how deep the water will get in those areas
4. **Road/Area Accessibility Prediction** — which roads and areas become impassable, and when
5. **Evacuation Recommendation** — which locations should evacuate, and via which safe route

Data comes from MOSDAC (ISRO) via `core/mosdac_connector.py`.

## Structure

- `core/` — fusion engine, MOSDAC connector, backtester, pilot scenarios
- `models/` — the 5 output models + pipeline runner
- `static/` — web dashboard (HTML/CSS/JS)
- `server.py` — web server · `run_system.py` — run the full system · `demo.py` — demo
- `mdapi.py` — MOSDAC API client · `tests/` — pipeline tests

## Setup

Replace `YOUR_GOOGLE_MAPS_API_KEY` in `config.json`, `static/index.html` and
`static/js/gis_map.js` with your own Google Maps API key, and fill in your
MOSDAC credentials in `config.json`.
