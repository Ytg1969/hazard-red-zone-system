# SIH26191 — Hazard Red Zone Decision Support System

A Streamlit-based geospatial decision-support prototype for identifying hazard-based red zones, assessing safe-zone/shelter carrying capacity, and prioritizing relocation of vulnerable habitations.

## Core workflow

`Data → GIS Exposure → Vulnerability → Risk → Carrying Capacity → Routing → Relocation → Dashboard → Draft Action Plan`

## Current implementation status

The stable offline core demo is already merged to `main` and is the recommended presentation baseline.

The active Phase-2 branch is:

- `feature/odisha-pilot-data` — authoritative Odisha/Puri data staging, provenance, readiness gates and hazard/shelter adapters.

The core demo currently includes:

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
- Odisha Pilot Status page on the Phase-2 branch;
- draft action-plan export;
- LIVE / CACHED / DEMO data-mode infrastructure;
- automated tests and GitHub Actions CI.

## Demo now

For a jury/team presentation, use the clearly labelled offline DEMO path. The authoritative Puri pilot is intentionally kept behind a no-fabrication readiness gate until its missing real-world fields are verified.

On Windows PowerShell:

```powershell
cd C:\Users\<user>\Project\hazard-red-zone-system
git fetch origin
git checkout main
git pull origin main
py -3.13 -m pytest tests -q
py -3.13 -m streamlit run app.py
```

Open the local Streamlit URL, normally `http://localhost:8501`.

Recommended 3-minute flow:

1. **Operational Overview** — establish the EOC problem and show top risk KPIs.
2. **Red Zone Map** — show spatial red-zone identification.
3. **Risk Analysis** — explain why a habitation is high/critical using factor contributions.
4. **Relocation Planner** — show safe shelter filtering, capacity-aware allocation and route distance.
5. **Scenario Studio** — change weights and demonstrate explainable scenario sensitivity.
6. **Draft Action Plan** — export the administrative decision-support output.

For the development branch, use `feature/odisha-pilot-data`. It adds the Odisha Pilot Status page and authoritative-data readiness tooling while retaining the same working DEMO path.

## Data honesty

Bundled hazard polygons, habitation records and shelter records are demonstration data unless explicitly replaced by an authoritative source. The UI must never present `DEMO` or `CACHED` data as `LIVE`.

Synthetic data is used to test the system pipeline and UI. It must not be used to claim scientific model accuracy or real-world hazard validation.

Census 2011 values used in the Puri pilot must remain explicitly historical. The directly published Census age-0-6 population may only be used as an age-0-6 child proxy when labelled exactly that way. Missing elderly, coordinate, shelter-capacity or hazard-layer information is not fabricated.

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

Python 3.12 is the recommended shared/CI version for the geospatial stack. Python 3.13 is a practical local Windows fallback when 3.12 is unavailable and the environment installs cleanly.

## Run

```bash
streamlit run app.py
```

## Tests

```bash
python -m pytest tests
```

## Pilot readiness check

On `feature/odisha-pilot-data`, once processed authoritative CSVs exist:

```powershell
py -3.13 scripts/check_pilot_readiness.py `
  --habitations data/pilot/processed/habitations.csv `
  --shelters data/pilot/processed/shelters.csv `
  --fail-if-not-ready
```

The processed Puri bundle is only written when all frozen operational fields pass the readiness and preprocessing gates.

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

Create new feature work from the latest `main`. Do not continue new work from old implementation branches that have already been merged.

Current Phase-2 integration branch:

- `feature/odisha-pilot-data`

## Important limitations

- This is a decision-support prototype, not an autonomous evacuation-order system.
- Current bundled hazard polygons are synthetic demonstration layers.
- Road conditions and shelter occupancy must be revalidated during real emergencies.
- Live IMD / NDMA / CWC integrations require verified source access and source-specific adapters.
- The authoritative Puri pilot is not operational-ready until the readiness gate passes.
- Optional ML validation should only be added when credible historical labels and leakage-safe validation are available.
- Raw InSAR processing is outside the seven-day core; preprocessed deformation layers can be integrated later.

See `docs/team_plan.md`, `docs/data_dictionary.md`, `docs/architecture.md`, `docs/data_sources.md`, `docs/risk_methodology.md`, `docs/demo_script.md`, `docs/odisha_pilot_plan.md`, and `docs/pilot_hazard_integration.md` before changing shared interfaces.
