# SIH26191 — Multi-Hazard Red Zone Decision Support System

A Streamlit-based geospatial decision-support prototype for identifying hazard-based red zones, explaining risk, checking shelter carrying capacity and producing capacity-aware relocation recommendations.

## Core workflow

`Data → GIS Exposure → Multi-Hazard Profile → Vulnerability → Explainable Risk → Carrying Capacity → Routing → Relocation/Optimization → Dashboard → Draft Action Plan`

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
- NDMA SACHET-compatible CAP/RSS alert infrastructure with strict LIVE/CACHED/DEMO handling;
- optional USGS FDSN earthquake context with LIVE→CACHED behavior;
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
py -3.13 -m pip install -r requirements.txt
py -3.13 scripts/demo_gate.py
py -3.13 -m pytest tests -q
py -3.13 -m streamlit run app.py
```

The demo gate checks all five named hazard profiles plus Combined Multi-Hazard, the three-city dataset, frozen risk classes, local/capacity-safe relocation, batch no-double-booking, global optimizer accounting and both Markdown/PDF export. It should report `"demo_ready": true`.

## Suggested five-minute walkthrough

1. **Operational Overview** — All Demo Cities + Combined Multi-Hazard.
2. **Red Zone Map** — switch Puri / Guwahati / Chennai and show DEMO hazard footprints.
3. **Risk Analysis** — choose a named hazard and show indicator contributions + final risk contributions.
4. **Relocation Planner** — safe-shelter ranking, split allocation, deficit and system-wide capacity sharing.
5. **Scenario Studio** — adjust risk policy weights and show classification impact.
6. **Command Center** — show CAP/RSS alert infrastructure and optional external context.
7. **Export** — download the PDF action plan.

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

### NDMA SACHET

The application includes a CAP/RSS-compatible parser and cache behavior. Configure only a verified endpoint/identifier before presenting it as LIVE. The official SACHET integration guidance requires ETag-aware CAP XML caching.

### USGS earthquake context

`src/earthquake_context.py` uses the official USGS FDSN Event Web Service for optional earthquake context near the three demo geographies. This feed is contextual and does not silently modify the deterministic risk score.

## Custom data

Command Center accepts habitation and shelter CSV uploads after schema validation. Uploaded files are user-supplied and are not automatically treated as live government data. A minimum habitation template is downloadable in the UI.

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

Python 3.12 remains the shared/CI target; Python 3.13 can be used locally when dependencies install cleanly.

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
- Experimental coordination zones do not determine evacuation.
- Global optimization compares only shelter candidates already passing safety/capacity gates.
- Road conditions and shelter occupancy must be revalidated during emergencies.
- Raw Sentinel-1 InSAR processing remains outside the core; preprocessed layers can be integrated later.

Key documentation: `docs/technical_architecture.md`, `docs/multicity_demo_sources.md`, `docs/demo_guide.md`, `docs/pre_demo_checklist.md`, `docs/submission_summary.md`, `docs/jury_faq.md`, `docs/data_dictionary.md`, `docs/risk_methodology.md`.
