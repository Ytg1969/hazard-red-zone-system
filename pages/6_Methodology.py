import streamlit as st

from src.ui_theme import inject_global_css, render_disclaimer, render_page_header

st.set_page_config(page_title="Methodology", layout="wide")
inject_global_css()
render_page_header(
    "Methodology",
    "Technical reference for multi-hazard scoring, explainable risk, carrying capacity, relocation optimization, routing and data limitations.",
)

st.markdown(
    """
### 1. Explainable risk model

The frozen prototype risk contract remains:

`Risk = 0.35 × Hazard + 0.25 × Exposure + 0.25 × Vulnerability + 0.15 × Evacuation Difficulty`

All four inputs are bounded to **0–100** before weighting. Higher evacuation-difficulty values increase risk.

| Risk score | Classification |
|---:|---|
| 0–29 | LOW |
| 30–49 | MODERATE |
| 50–69 | HIGH |
| 70–100 | CRITICAL |

Scenario Studio permits alternative policy emphasis, but weights are normalized to 1.00.

### 2. Transparent multi-hazard component

The **Hazard** term can now be supplied by one of six explicit profiles:

- Flood
- Cyclone
- Landslide
- Earthquake
- Drought
- Combined multi-hazard

Each profile uses visible indicator rules from `src/hazard_model.py`. Missing indicators cause only the available prototype weights to be re-normalized, and a data-completeness percentage is displayed.

These indicator weights and numeric bounds are **prototype assumptions for DEMO/scenario use, not official hazard standards**. Authoritative deployments should replace them with source-specific calibrated mappings while keeping the same explainable interface.

### 3. Vulnerability

The demonstration vulnerability score uses the share of children and elderly people in the habitation population. Production deployments can add approved disability, health-access, housing, poverty and other indicators when defensible data exists.

### 4. Coordination zones (experimental)

KMeans groups nearby habitations with similar final risk into `Zone A`, `Zone B`, etc. This is a coordination/briefing aid only. The zone label does **not** alter hazard score, risk score, relocation priority, shelter eligibility or evacuation orders.

### 5. Carrying capacity

`effective_capacity = min(total_capacity, known water capacity, known sanitation capacity, known access capacity)`

- **VALIDATED** — all defined resource capacities are available.
- **PARTIAL** — some resource capacities are known; the minimum known constraint is used.
- **UNVALIDATED** — no resource sub-capacity is available; total physical capacity is the fallback.

`available_capacity = max(0, effective_capacity − current_occupancy)`

Unknown values remain unknown rather than being silently converted to zero.

### 6. Relocation ranking and splitting

Unsafe or full shelters are removed first. Remaining candidates use the frozen transparent ranking weights:

- Safety: **35%**
- Capacity adequacy: **25%**
- Accessibility: **20%**
- Distance desirability: **20%**

Population can be split across several safe shelters, and any deficit is reported explicitly.

### 7. System-wide and global optimization

The priority-first batch planner shares shelter capacity across habitations so the same space cannot be double-booked.

An optional NetworkX network-simplex comparison layer performs a global min-cost flow using only shelter edges that already pass the existing safety/capacity ranking gate. A high-cost deficit path makes insufficient capacity explicit instead of forcing an unsafe assignment. In the multi-city demo, both planners enforce same-city shelter assignment when `demo_city` metadata exists.

The global optimizer is an experimental comparison tool, not an autonomous evacuation-order engine.

### 8. Routing

The offline-safe baseline uses great-circle distance and labels it `haversine_fallback`. Cached OpenStreetMap routing through OSMnx/NetworkX can be enabled for road-aware demonstration without venue internet.

### 9. External context and data modes

Every operational source must expose one of:

- **LIVE** — verified current source.
- **CACHED** — previously fetched response reused when live access is unavailable.
- **DEMO** — synthetic demonstration data.

NDMA SACHET CAP/RSS support is isolated from the deterministic risk pipeline. USGS FDSN earthquake queries are available as optional external context and use LIVE→CACHED behavior. External context does not silently change the risk score.

### 10. Three-city demonstration

The enhanced demo includes Puri, Guwahati and Chennai as representative high-risk Indian geographies covering coastal cyclone/flood, flood/landslide/earthquake and cyclone/flood/drought contexts. They are **not claimed to be a definitive ranking of India's three most disaster-prone cities**.

City coordinates are real-geography anchors. Catchment populations, operational shelter capacities/occupancies, hazard indicator values and demo GeoJSON footprints are synthetic scenario inputs. See `docs/multicity_demo_sources.md`.

### 11. Data upload

Command Center accepts habitation and shelter CSV uploads after the frozen schema validator checks required columns, coordinates and non-negative population/capacity fields. Uploaded data is user supplied and is not automatically labelled as a live government source.

### 12. Limitations

- This system provides administrative decision support; it does not issue statutory evacuation orders.
- Prototype multi-hazard weights are transparent assumptions, not universal standards.
- DEMO footprints are not authoritative hazard-zone boundaries.
- Shelter occupancy and infrastructure capacity are only as current as their source timestamps.
- Road conditions must be revalidated before dispatch.
- ML zoning is a coordination aid only unless separately validated for an operational use case.
- Raw Sentinel-1 InSAR processing remains outside the core; preprocessed deformation layers can be ingested later.
"""
)

render_disclaimer()
