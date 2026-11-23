# Real-Time Flood Risk Prediction System — Rebuilt Blueprint
### Satellite + Weather Radar + Rain Gauge + Weather Station + NWP + GIS + AI/ML

This rebuild restructures the prototype around **5 required output products**, not just a generic rainfall→flood pipeline. Every phase below exists to serve one or more of these:

| # | Required Output | What it answers |
|---|---|---|
| 1 | **Rainfall Prediction** | How much rain, where, and when (nowcast + short-range) |
| 2 | **Flood Location Prediction** | Which specific areas will flood |
| 3 | **Water Depth Prediction** | How deep the water will get in those areas |
| 4 | **Road/Area Accessibility Prediction** | Which roads/areas become impassable, and when |
| 5 | **Evacuation Recommendation** | Which locations should evacuate, and via which safe route |

---

## PROPOSED SYSTEM — Architecture Overview

```
                        ┌─────────────────────────────────────────────┐
                        │              DATA SOURCES (Phase 1)          │
                        │  Satellite │ Weather Radar │ Rain Gauge │    │
                        │  Weather Station │ NWP │ GIS Layers          │
                        └─────────────────────┬─────────────────────┘
                                              ▼
                        ┌─────────────────────────────────────────────┐
                        │     PREPROCESSING & FUSION (Phase 2)         │
                        │  common grid, common timestep, QC, features  │
                        └─────────────────────┬─────────────────────┘
                                              ▼
              ┌───────────────────────────────────────────────────────┐
              │                 AI/ML CORE (Phase 3)                    │
              │                                                          │
              │  [1] Rainfall Prediction Model (nowcast + short-range)  │
              │              │                                          │
              │              ▼                                          │
              │  [2] Flood Location Model (where) ──┐                   │
              │              │                       │                  │
              │              ▼                       ▼                  │
              │  [3] Water Depth Model (how deep)  [GIS overlay engine] │
              │              │                       │                  │
              │              ▼                       ▼                  │
              │  [4] Road/Area Accessibility Model (passable/blocked)   │
              │              │                                          │
              │              ▼                                          │
              │  [5] Evacuation Zone & Route Recommender                │
              └───────────────────────────┬───────────────────────────┘
                                          ▼
                        ┌─────────────────────────────────────────────┐
                        │   DASHBOARD + ALERTS (Phase 4)               │
                        │  GIS map, depth overlay, blocked roads,      │
                        │  evacuation routes, SMS/app alerts           │
                        └─────────────────────────────────────────────┘
```

Outputs [2]–[5] are all **downstream consumers of [1]** — nothing else can run until the rainfall prediction is produced, since flood location, depth, road blockage, and evacuation zones are all functions of predicted rainfall + terrain + infrastructure.

---

## PHASE 0 — Environment & Credential Setup
*(unchanged from previous version — MOSDAC account, `config.json`, dataset IDs. See Phase 1 below for what additional GIS layers now need sourcing.)*

**New for this rebuild — additional GIS layers to acquire in Phase 0/1:**
- **Road network**: OpenStreetMap (via `osmnx`) or Bhuvan road layer — needed for Output 4
- **Population density / settlement layer**: WorldPop or Census 2011 gridded population — needed for Output 5 prioritization
- **Shelter/relief camp locations**: NDMA/SDMA public shelter registries — needed for Output 5 routing targets
- **Administrative boundaries**: village/ward polygons (Bhuvan/Survey of India) — needed to name evacuation zones in alerts

---

## PHASE 1 — Data Acquisition
*(mdapi.py covers satellite; separate pulls still needed for radar, rain gauge, weather station, NWP, DEM — as detailed in the earlier version of this blueprint.)*

**Direct mapping to the 5 outputs:**

| Source | Feeds which output(s) |
|---|---|
| Satellite (rainfall estimate, cloud imagery) | Output 1 |
| Weather Radar (reflectivity) | Output 1 |
| Rain Gauge (ground truth point rainfall) | Output 1 (bias correction) |
| Weather Station (temp/humidity/wind/pressure) | Output 1 (feature input) |
| NWP (GFS/WRF/ERA5) | Output 1 (short-range + instability indices) |
| DEM + drainage network | Output 2, 3 |
| Land Use/Land Cover | Output 2, 3 |
| River gauge / discharge | Output 2, 3 |
| Road network (GIS) | Output 4 |
| Population + shelter layer (GIS) | Output 5 |

**Transition trigger:** all rows above have raw files present and readable for the pilot region/period.

---

## PHASE 2 — Preprocessing & Multi-Source Fusion
*(as before: common grid, common timestep, gap-fill, bias correction, feature engineering, chronological/event-based split.)*

**Added for this rebuild:**
- Road network and shelter/population layers must be reprojected onto the **same grid** as the rainfall/DEM stack — this is what allows the flood depth output to be spatially joined against roads and settlements later without a separate GIS step.
- Precompute a **static "vulnerability layer"**: for every grid cell, store distance-to-river, elevation, population density, and nearest-shelter distance once, since these don't change per-event and can be reused across every prediction cycle.

**Transition trigger:** fused tensors + static vulnerability layer both pass a sanity check on a spot-checked sample day.

---

## PHASE 3 — AI/ML Core (one model/module per output)

### [Output 1] Rainfall Prediction Model
- **Nowcast (0–3 hr)**: ConvLSTM/U-Net ensemble on fused radar+satellite → rainfall intensity grid at 30/60/90/120-min lead times
- **Short-range (24–72 hr)**: NWP + bias-correction (XGBoost/LightGBM stack) → corrected district/grid rainfall forecast
- **Accuracy upgrades**: weighted loss on heavy-rain bins, hyperparameter search, uncertainty bounds on every prediction (carry this uncertainty forward — it matters for Output 5's risk prioritization)
- **Output artifact**: rainfall intensity/accumulation grid, with confidence interval, for each lead time

### [Output 2] Flood Location Prediction Model ("where")
- **Input**: Output 1's rainfall grid + DEM + drainage network + LULC + river gauge level
- **Architecture**: CNN/U-Net trained on Sentinel-1 SAR-derived historical flood polygons → binary/probabilistic flood-extent mask per grid cell
- **Output artifact**: a probability-of-inundation map (0–100%) per grid cell, for each forecast lead time

### [Output 3] Water Depth Prediction Model ("how deep")
- **Input**: same as Output 2, plus the flood-extent mask itself as a conditioning input
- **Architecture**: extend the Output 2 U-Net with a second regression head (multi-task learning: one head for extent classification, one head for depth regression) — more data-efficient than training two separate models, and depth predictions are physically constrained to only exist where extent is predicted positive
- **Accuracy upgrades**: augment training pairs using an offline hydrodynamic simulator (LISFLOOD-FP/HEC-RAS) run on synthetic rainfall scenarios over your DEM, since labeled real depth data will be very sparse
- **Output artifact**: a water-depth raster (in cm/m) for flooded cells only

### [Output 4] Road/Area Accessibility Model ("what becomes inaccessible")
- **Input**: Output 3's depth raster + road network layer (spatially joined)
- **Logic**: this can start as a **rule-based classifier** (no ML needed initially, and it's more defensible/explainable to judges):
  - Depth < 15cm → passable for all vehicles
  - 15–30cm → passable for high-clearance vehicles only
  - > 30cm → impassable / road closed
  (Thresholds should be calibrated against local traffic/vehicle-clearance norms for your pilot region.)
- **Optional ML upgrade**: train a classifier on historical road-closure reports (if available from local traffic police/NDMA) to learn region-specific thresholds instead of fixed cutoffs — do this only after the rule-based version is working, since it's an enhancement, not a blocker.
- **Output artifact**: a road-segment-level accessibility status (Open / Restricted / Closed), updated per forecast cycle

### [Output 5] Evacuation Zone & Route Recommendation
- **Input**: Output 2 (flood probability) + Output 3 (depth) + static vulnerability layer (population density, elevation) + Output 4 (which roads are usable) + shelter locations
- **Logic**:
  1. **Prioritize zones**: rank grid cells/wards by a composite risk score = f(flood probability × depth × population density), highest-risk zones surface first
  2. **Route evacuees**: run shortest-path routing (Dijkstra/A* via `networkx` or `osmnx`) from each high-risk zone to the nearest shelter, **excluding road segments marked Closed by Output 4** — this is why Output 4 must run before Output 5, not in parallel
  3. If no safe route exists (all roads closed), flag that zone for **priority air/boat rescue** rather than road evacuation — an important edge case to show in your demo, since it demonstrates the system reasoning about infrastructure failure, not just weather
- **Output artifact**: ranked list of evacuation zones + recommended route (or rescue-mode flag) per zone

---

## PHASE 3.5 — Accuracy Enhancement & Sign-off (Pre-Handoff Gate)

**Checklist — all should be true before handing models to integration:**
- [ ] Output 1: ensembling + weighted loss + hyperparameter search + uncertainty bounds attached
- [ ] Output 2/3: multi-task extent+depth model trained with hydrodynamic-simulator augmentation
- [ ] Output 2/3: k-fold (event-based) cross-validation, IoU/Dice for extent, RMSE for depth, both reported as ranges
- [ ] Output 4: rule-based thresholds calibrated and reviewed against at least one real historical road-closure event, if data exists
- [ ] Output 5: routing logic tested on a synthetic "all roads closed" edge case to confirm rescue-mode flagging works
- [ ] A model card written per output (architecture, inputs, known failure modes, metric ranges)

**Transition trigger:** every item checked, and each model clears its Phase 0 target threshold.

---

## PHASE 4 — System Integration

```
Output 1 (rainfall) → Output 2 (flood location) → Output 3 (depth)
        → Output 4 (road accessibility) → Output 5 (evacuation zones/routes)
        → GIS Dashboard (map layers: rainfall, flood extent, depth heatmap,
           road status, evacuation routes) + SMS/app alerts to at-risk zones
```

**Dashboard requirement (GIS-centric, since this system is explicitly GIS-based):**
- Base map with toggleable layers: rainfall heatmap, flood probability, depth raster, road status (color-coded), evacuation routes, shelter locations
- Timeline slider across lead times (nowcast → 72hr)
- Click-to-inspect: clicking any zone shows its risk score, predicted depth, nearest open route, and nearest shelter

**Transition trigger:** feeding one historical event through the full chain produces all 5 outputs end-to-end without manual intervention, and the dashboard renders all layers correctly.

---

## PHASE 5 — Validation & Backtesting

Validate each output against reality, not just against each other:
1. **Output 1**: compare against actual IMD-recorded rainfall for a backtested event
2. **Output 2/3**: compare predicted flood extent/depth against Sentinel-1 SAR-observed extent for that event (IoU/RMSE)
3. **Output 4**: compare predicted road closures against any available traffic/news reports for that event
4. **Output 5**: sanity-check that recommended evacuation routes were actually passable at the predicted time (i.e., the route doesn't route people through a road Output 4 predicted as closed)

**Transition trigger:** at least one full backtested case study where all 5 outputs are independently checked against real records.

---

## PHASE 6 — Packaging
*(unchanged — PPT, GitHub repo, live demo, one-pager. For this rebuild, structure the PPT/demo explicitly around the 5 outputs, since that's now the core value proposition to pitch.)*

---

## Quick Reference: Phase & Output Dependency Chain

| Phase | Needs completed before it | Produces |
|---|---|---|
| 0 Setup | — | credentials + GIS layers acquired |
| 1 Acquisition | Phase 0 | raw data for all 5 output dependencies |
| 2 Fusion | Phase 1 | fused tensors + static vulnerability layer |
| 3 → Output 1 | Phase 2 | rainfall prediction |
| 3 → Output 2 | Output 1 | flood location |
| 3 → Output 3 | Output 2 | water depth |
| 3 → Output 4 | Output 3 | road accessibility |
| 3 → Output 5 | Output 4 | evacuation zones/routes |
| 3.5 Sign-off | Outputs 1–5 | validated, documented models |
| 4 Integration | Phase 3.5 | end-to-end dashboard |
| 5 Validation | Phase 4 | backtested case study |
| 6 Packaging | Phase 5 | submission-ready deliverable |

**Key sequencing rule:** Outputs 2–5 are strictly sequential, not parallel — each depends on the one before it (flood location needs rainfall, depth needs location, road status needs depth, evacuation routing needs road status). Building them out of order means re-work when an upstream output changes.
