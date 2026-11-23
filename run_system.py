"""
Real-Time Flood Risk Prediction System — Quick Launch Script
Starts the FastAPI server with GIS Command Center Dashboard on http://127.0.0.1:8000
"""

import sys
import uvicorn

if __name__ == "__main__":
    print("=================================================================")
    print("🌊 Varuna AI — Real-Time Flood Risk Prediction System")
    print("🛰️ Fusing MOSDAC Satellite + Weather Radar + NWP + DEM + OSM GIS")
    print("📊 Serving 5 Required Outputs (Rainfall, Location, Depth, Roads, Evacuation)")
    print("🚀 Dashboard available at: http://127.0.0.1:8000")
    print("=================================================================\n")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
