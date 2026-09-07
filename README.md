# SIH26191 — Multi-Hazard Red Zone Decision Support System

A Streamlit-based geospatial decision-support prototype for identifying hazard-based red zones, explaining risk, checking shelter carrying capacity and producing capacity-aware relocation recommendations.

## Core workflow

`Data → GIS Exposure → Multi-Hazard Profile → Vulnerability → Explainable Risk → Carrying Capacity → Routing → Relocation/Optimization → Incident Command → Briefing`

## Current demo capability

The presentation path now includes:

- **Flood, Cyclone, Landslide, Earthquake, Drought and Combined Multi-Hazard** profiles;
- transparent hazard-indicator scoring with missing-data re-normalization and completeness reporting;
- frozen final risk contract: `0.35H + 0.25E + 0.25V + 0.15A`;
- real-geography demo contexts for **Puri, Guwahati and Chennai**;
- synthetic but realistic-scale operational catchment/shelter scenario data, always labelled `DEMO`;
- synthetic multi-city hazard GeoJSON footprints for map demonstration;
- experimental KMeans coordination zones that do not alter risk/relocation decisions;
- limiting-resource carrying capacity with VALIDATED / PARTIAL / UNVALIDATED status;
- safe-shelter ranking and multi-shelter population splitting;
- system-wide priority allocation preventing double-booked capacity;
- optional safety-gated NetworkX network-simplex global optimization comparison;
- cached OSM GraphML routing with labelled haversine fallback;
- Markdown and PDF action-plan export;
- custom habitation/shelter CSV validation and template workflow;
- NDMA SACHET-compatible CAP/RSS alert infrastructure with ETag-aware cache support;
- official IMD district-warning/rainfall context with LIVE→CACHED behavior;
- official USGS FDSN earthquake context with LIVE→CACHED behavior;
- dedicated **Live Data Context** page for source status and city-specific external evidence;
- cohesive Hazard Command 3 operator surface with Incident Command, Hazard Map, Risk Intelligence, Relocation, Briefing, Evidence Center and System Boundaries;
- Docker deployment support, tests and GitHub Actions CI.

## Demo data honesty

Puri, Guwahati and Chennai are **representative high-risk Indian geographies**, not a definitive ranking of India's three most disaster-prone cities.

The city coordinates/geographic context are real, while bundled habitation catchment populations, shelter capacities/occupancies, hazard indicator values and hazard polygons are **synthetic operational DEMO scenarios**. They exist to exercise the pipeline without pretending unavailable operational data is real.

See `docs/multicity_demo_sources.md` for official hazard-context references and exact limitations.

The prototype hazard indicator weights/bounds are visible in `src/hazard_model.py`. They are **not official hazard standards**. Authoritative deployments should replace them with verified source-specific mappings.

## Run the demo

Windows PowerShell:

```powershell
cd C:\Users\<user>\Project\hazard-red-zone-system
git fetch origin
git checkout main
git pull origin main
py -3.12 -m pip install -r requirements.txt
py -3.12 scripts/demo_gate.py
py -3.12 -m pytest tests -q
py -3.12 -m streamlit run app.py
```

The demo gate checks all five named hazard profiles plus Combined Multi-Hazard, the three-city dataset, frozen risk classes, local/capacity-safe relocation, batch no-double-booking, global optimizer accounting, IMD warning-code normalization, all required pages and both Markdown/PDF export. It should report `"demo_ready": true`.

## Probe real APIs before judging

This command is internet-dependent and optional:

```powershell
py -3.12 scripts/api_probe.py
```

It checks official IMD warning/rainfall context and USGS earthquake context for Puri, Guwahati and Chennai. It also reports the SACHET feed state. The probe never modifies risk scores or authoritative pilot data.

Expected source modes:
- `LIVE` — successfully refreshed from a verified source;
- `CACHED` — last successful response reused;
- `DEMO` — no verified live/cache response available or synthetic presentation content.

## Suggested five-minute walkthrough

1. **Incident Command** — select the priority focus, review exposed population, immediate relocation demand, safe capacity and decision gates.
2. **Hazard Map** — switch Puri / Guwahati / Chennai and show DEMO hazard footprints, shelter context and route provenance.
3. **Risk Intelligence** — show component contributions, dominant drivers and evidence completeness.
4. **Relocation** — safe-shelter ranking, split allocation, deficit and system-wide capacity sharing.
5. **Briefing** — generate the operator/judge handoff and export the action plan.
6. **Live Data Context** — refresh IMD, USGS and NDMA SACHET context and explain LIVE/CACHED/DEMO separation.
7. **Evidence Center / System Boundaries** — show source provenance, constraints and the decision-support boundary when asked.

See `docs/demo_guide.md` and `docs/pre_demo_checklist.md`.

## Risk model

`Risk = 0.35 × Hazard + 0.25 × Exposure + 0.25 × Vulnerability + 0.15 × Evacuation Difficulty`

Risk classes:

- LOW: 0–29
- MODERATE: 30–49
- HIGH: 50–69
- CRITICAL: 70–100

Scenario Studio may change policy emphasis, but weights are normalized to sum to 1.00.

## Carrying capacity

`effective_capacity = min(total, known water, known sanitation, known access/logistics)`

`available_capacity = max(0, effective_capacity - current_occupancy)`

Unknown is distinct from zero. Population allocation never exceeds available capacity.

## External feeds

### IMD weather context

`src/imd_context.py` uses official India Meteorological Department endpoints documented by IMD:

- district warnings: `https://mausam.imd.gov.in/api/warnings_district_api.php`
- district rainfall: `https://mausam.imd.gov.in/api/districtwise_rainfall_api.php`

The adapter filters the response to the selected demo geography and decodes documented warning codes/color levels. IMD data remains contextual until a verified source-specific analytical mapping is approved.

### NDMA SACHET

The application includes a CAP/RSS-compatible parser and ETag-aware cache behavior. The WMO Register of Alerting Authorities lists NDMA India's CAP feed as:

`https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml`

The connector remains opt-in so deterministic offline startup does not depend on the network. Configure it with `SIH_SACHET_FEED_URL` when live NDMA alert context is required. NDMA's separate per-alert CAP XML endpoint requires an identifier and ETag-aware caching; do not invent identifiers. See `DEPLOYMENT.md` for the WMO/NDMA verification references and exact cache contract.

### USGS earthquake context

`src/earthquake_context.py` uses the official USGS FDSN Event Web Service for optional earthquake context near the three demo geographies. This feed is contextual and does not silently modify the deterministic risk score.

### Bhuvan GIS

NRSC/ISRO Bhuvan documents OGC WMS/WMTS services including Flood Hazard and Flood Annual Layers. The exact layer identifier, legend/source class, CRS and source-class→0–100 mapping still have to be verified before a Bhuvan layer is allowed to drive risk scoring.

## Custom data

**Operational Data** is the supported ingestion surface for habitation and shelter CSV/Point GeoJSON inputs after schema validation. Uploaded files are user-supplied and are not automatically treated as live government data. A minimum habitation template is downloadable in the UI.

## Install

### Conda / Miniforge

```bash
conda env create -f environment.yml
conda activate hazard-red-zone
```

### Pip

```bash
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

Python 3.12 is the shared CI, release-candidate and Windows offline-bundle target.

## Docker

```bash
docker build -t hazard-red-zone .
docker run --rm -p 8501:8501 hazard-red-zone
```

See `DEPLOYMENT.md`.

## Cache a road network

```bash
python scripts/cache_road_network.py "Puri, Odisha, India"
```

PowerShell example:

```powershell
$env:SIH_ROAD_GRAPHML="data/cache/roads/Puri_Odisha_India.graphml"
```

If the graph is unavailable, the app explicitly falls back to haversine distance.

## Authoritative pilot work

The strict Odisha/Puri authoritative-data integration continues separately from the demo until population/admin details, vulnerability demographics, coordinates, shelter operations and a machine-readable authoritative hazard layer satisfy the provenance/readiness gates. Incomplete authoritative fields must not destabilize the presentation path.

## Important limitations

- Decision support only; authorized officials make evacuation/relocation decisions.
- Bundled multi-city operational values and hazard footprints are DEMO.
- Prototype hazard-profile weights are not official standards.
- External live feeds remain context unless explicitly integrated through a verified source-specific analytical mapping.
- Experimental coordination zones do not determine evacuation.
- Global optimization compares only shelter candidates already passing safety/capacity gates.
- Road conditions and shelter occupancy must be revalidated during emergencies.
- Raw Sentinel-1 InSAR processing remains outside the core; preprocessed layers can be integrated later.

Key documentation: `docs/technical_architecture.md`, `docs/multicity_demo_sources.md`, `docs/demo_guide.md`, `docs/pre_demo_checklist.md`, `docs/submission_summary.md`, `docs/jury_faq.md`, `docs/data_dictionary.md`, `docs/risk_methodology.md`.
