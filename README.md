# SIH26191 — Hazard Red Zone Decision Support System

A Streamlit-based geospatial decision-support prototype for identifying hazard-based red zones, assessing safe-zone/shelter carrying capacity, and prioritizing relocation of vulnerable habitations.

## Core workflow

`Data → GIS Exposure → Vulnerability → Risk → Carrying Capacity → Routing → Relocation → Dashboard → Draft Action Plan`

## Current implementation status

The stable offline core demo is merged to `main` and is the recommended presentation baseline.

The core demo includes:

- frozen habitation and shelter data contracts;
- deterministic offline demonstration data;
- synthetic GeoJSON hazard polygons for GIS pipeline testing;
- vector hazard intersection/proximity scoring;
- explainable weighted risk scoring with configurable weights;
- vulnerability scoring and phased relocation priority;
- limiting-resource carrying capacity with VALIDATED / PARTIAL / UNVALIDATED status;
- multi-criteria shelter ranking;
- capacity-safe multi-shelter population allocation;
- cached OSM GraphML routing support with a clearly labelled haversine fallback;
- Command Center, Red Zone Map, Risk Analysis, Relocation Planner, Scenario Studio and Methodology pages;
- draft action-plan export;
- LIVE / CACHED / DEMO data-mode infrastructure;
- automated tests and GitHub Actions CI.

## Demo now

On Windows PowerShell:

```powershell
cd C:\Users\<user>\Project\hazard-red-zone-system
git fetch origin
git checkout main
git pull origin main
py -3.13 scripts/demo_gate.py
py -3.13 -m pytest tests -q
py -3.13 -m streamlit run app.py
```

`demo_gate.py` validates the deterministic offline path, including risk scoring, shelter capacity, safe-shelter recommendation, multi-shelter allocation accounting and draft action-plan generation. It should report `"demo_ready": true` before the presentation.

Recommended 3-minute flow:

1. **Operational Overview** — show EOC KPIs and the highest-risk habitation.
2. **Red Zone Map** — show spatial red-zone identification.
3. **Risk Analysis** — explain the factor contributions behind the score.
4. **Relocation Planner** — show safe-shelter filtering, capacity-aware allocation and routing mode.
5. **Scenario Studio** — optionally adjust weights and show classification sensitivity.
6. **Draft Action Plan** — export the administrative decision-support output.

## Data honesty

Bundled hazard polygons, habitation records and shelter records are demonstration data unless explicitly replaced by an authoritative source. The UI must never present `DEMO` or `CACHED` data as `LIVE`.

Synthetic data is used to test the system pipeline and UI. It must not be used to claim scientific model accuracy or real-world hazard validation.

## Risk model

Default explainable score:

`Risk = 0.35 × Hazard + 0.25 × Exposure + 0.25 × Vulnerability + 0.15 × Evacuation Difficulty`

All factors are bounded to 0–100 and weights must sum to 1.00.

Risk classes:

- LOW: 0–29
- MODERATE: 30–49
- HIGH: 50–69
- CRITICAL: 70–100

## Carrying capacity

Where resource information exists:

`effective_capacity = min(total, water, sanitation, access)`

`available_capacity = max(0, effective_capacity - current_occupancy)`

Capacity status:

- `VALIDATED` — all defined resource constraints are available;
- `PARTIAL` — only some resource constraints are available;
- `UNVALIDATED` — total physical capacity is being used as fallback.

## Install

### Recommended: Conda / Miniforge

```bash
conda env create -f environment.yml
conda activate hazard-red-zone
```

### Pip alternative

```bash
python -m venv venv
# Windows
venv\Scripts\activate
python -m pip install -r requirements.txt
```

Python 3.12 is the recommended shared/CI version for the geospatial stack. Python 3.13 can be used locally when the environment installs cleanly.

## Run

```bash
streamlit run app.py
```

## Tests

```bash
python -m pytest tests
```

## Generate a larger synthetic demo dataset

```bash
python scripts/generate_demo_data.py --habitations 200 --shelters 20
```

Generated records are DEMO-only.

## Cache a road network before the demo

```bash
python scripts/cache_road_network.py "Puri, Odisha, India"
```

Then point the routing engine at the resulting GraphML file:

```powershell
$env:SIH_ROAD_GRAPHML="data/cache/roads/Puri_Odisha_India.graphml"
```

The app automatically falls back to haversine distance if the cache is unavailable.

## Development branches

Create new work from the latest `main`. Old implementation branches that have already been merged are not the working baseline.

Current authoritative-pilot development continues separately on `feature/odisha-pilot-data` so incomplete real-data fields cannot destabilize the demo.

## Important limitations

- This is a decision-support prototype, not an autonomous evacuation-order system.
- Current bundled hazard polygons are synthetic demonstration layers.
- Road conditions and shelter occupancy must be revalidated during real emergencies.
- Live IMD / NDMA / CWC integrations require verified source access and source-specific adapters.
- Optional ML validation should only be added when credible historical labels and leakage-safe validation are available.
- Raw InSAR processing is outside the seven-day core; preprocessed deformation layers can be integrated later.

See `docs/team_plan.md`, `docs/data_dictionary.md`, `docs/architecture.md`, `docs/data_sources.md`, `docs/risk_methodology.md`, and `docs/demo_script.md` before changing shared interfaces.
