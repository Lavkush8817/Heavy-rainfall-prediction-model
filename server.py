"""
FastAPI Server for Real-Time Flood Risk Prediction System
Serves the 5-Output Pipeline APIs, MOSDAC data connector, Backtesting suite,
and Interactive GIS Command Center Dashboard.
"""

import os
import json
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from core.mosdac_connector import MosdacConnector, load_mosdac_config, save_mosdac_config
from core.pilot_scenarios import PILOT_REGIONS
from models.pipeline_runner import FloodPredictionPipeline
from core.backtester import BacktestingSuite

app = FastAPI(
    title="Varuna AI — Real-Time Flood Risk Prediction System",
    description="Satellite + Radar + NWP + GIS + AI/ML 5-Output Flood Early Warning System",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Pipelines & Connectors
mosdac = MosdacConnector(config_path="config.json")
pipeline_chennai = FloodPredictionPipeline(region_id="chennai_basin")
pipeline_assam = FloodPredictionPipeline(region_id="assam_brahmaputra")
backtester = BacktestingSuite()

def get_pipeline(region_id: str):
    if region_id == "assam_brahmaputra":
        return pipeline_assam
    return pipeline_chennai

# Mount Static Files
os.makedirs("static", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_root():
    """Serves the Mission-Critical GIS Operations Dashboard."""
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Flood Prediction Prototype Dashboard loading...</h1>")

@app.get("/api/config")
async def get_config():
    """Returns MOSDAC configuration and connection status."""
    status = mosdac.get_status()
    raw_cfg = load_mosdac_config("config.json")
    return {
        "status": "ok",
        "mosdac_status": status,
        "raw_config": raw_cfg.get("data", {})
    }

class ConfigUpdateRequest(BaseModel):
    user_credentials: Optional[Dict[str, Any]] = None
    search_parameters: Optional[Dict[str, Any]] = None
    download_settings: Optional[Dict[str, Any]] = None

@app.post("/api/config")
async def update_config(req: ConfigUpdateRequest):
    """Updates config.json settings."""
    cfg = load_mosdac_config("config.json").get("data", {})
    if req.user_credentials:
        cfg["user_credentials"] = req.user_credentials
    if req.search_parameters:
        cfg["search_parameters"] = req.search_parameters
    if req.download_settings:
        cfg["download_settings"] = req.download_settings

    success, msg = save_mosdac_config(cfg, "config.json")
    return {"success": success, "message": msg, "config": cfg}

@app.get("/api/pipeline/regions")
async def get_regions():
    """Lists available geographic pilot regions and metadata."""
    return {
        "regions": [
            {
                "id": k,
                "name": v["name"],
                "state": v["state"],
                "bounds": v["bounds"],
                "center": v["center"],
                "description": v["description"],
                "shelters_count": len(v["shelters"]),
                "wards_count": len(v["wards"])
            }
            for k, v in PILOT_REGIONS.items()
        ]
    }

@app.get("/api/pipeline/run")
async def run_pipeline(
    region_id: str = Query("chennai_basin", description="Pilot region identifier"),
    lead_time: str = Query("t60m", description="Lead time: t30m, t60m, t90m, t120m, t24h, t72h"),
    severity: float = Query(1.0, description="Storm severity multiplier (0.5 - 2.5)"),
    river_gauge: Optional[float] = Query(None, description="Custom river gauge height in meters")
):
    """
    Executes the complete 5-Output Flood Risk Prediction Pipeline.
    Output 1: Rainfall -> Output 2: Flood Location -> Output 3: Water Depth -> Output 4: Accessibility -> Output 5: Evacuation
    """
    pipeline = get_pipeline(region_id)
    results = pipeline.run(
        lead_time=lead_time,
        severity=severity,
        river_gauge_m=river_gauge
    )
    return JSONResponse(content=results)

@app.get("/api/backtest/run")
async def run_backtest_endpoint(
    event_key: str = Query("chennai_dec2015", description="Historical benchmark event")
):
    """Executes validation & backtesting suite across all 5 output models."""
    pipeline = get_pipeline("chennai_basin")
    res = backtester.run_backtest(pipeline, event_key=event_key)
    return JSONResponse(content=res)

class AlertBroadcastRequest(BaseModel):
    zone_ids: list[str]
    severity_level: str
    custom_message: Optional[str] = None
    channels: list[str] = ["SMS_CELL_BROADCAST", "CAP_NDMA_ALERT", "WHATSAPP_EMERGENCY"]

@app.post("/api/alerts/broadcast")
async def broadcast_emergency_alerts(req: AlertBroadcastRequest):
    """
    Simulates real-time dispatch of CAP-compliant emergency SMS and mobile alerts
    to residents in designated critical flood risk zones.
    """
    broadcast_id = f"NDMA-FL-ALERT-{int(os.times().system * 1000)}"
    return {
        "broadcast_id": broadcast_id,
        "status": "DISPATCHED_TO_TELCO_CARRIERS",
        "zones_targeted": req.zone_ids,
        "channels_activated": req.channels,
        "cap_payload": {
            "identifier": broadcast_id,
            "sender": "SDMA-DISASTER-OPS-CENTER",
            "sent": "2026-08-27T14:35:00+05:30",
            "status": "Actual",
            "msgType": "Alert",
            "scope": "Public",
            "info": {
                "category": "Met / Geo",
                "event": "FLASH FLOOD & INUNDATION WARNING",
                "urgency": "Immediate",
                "severity": req.severity_level,
                "certainty": "Observed / High Confidence Model Forecast",
                "headline": "URGENT FLOOD EVACUATION NOTICE",
                "description": req.custom_message or "Predicted water depth exceeds safe thresholds. Proceed via recommended safe green routes to designated relief camps immediately.",
                "instruction": "Do not attempt to cross flooded roadways (>15cm depth). If isolated, wait on upper floors for NDRF boat/airlift rescue."
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Flood Risk Prediction System Server at http://127.0.0.1:8000 ...")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
