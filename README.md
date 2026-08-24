# SIH26191 — Hazard Red Zone Decision Support System

A Streamlit-based geospatial decision-support prototype for identifying hazard-based red zones, assessing safe-zone/shelter carrying capacity, and prioritizing relocation of vulnerable habitations.

## Core workflow

`Data → GIS Exposure → Vulnerability → Risk → Carrying Capacity → Routing → Relocation → Dashboard → Draft Action Plan`

## Current foundation

- Frozen habitation and shelter data contracts
- Explainable weighted risk engine with configurable weights
- Limiting-resource carrying-capacity logic
- Offline-safe straight-line routing fallback
- Safe-shelter recommendation contract
- LIVE / CACHED / DEMO data-mode contract
- Demonstration datasets for offline operation
- Streamlit page skeletons for Command Center, Red Zone Map, Risk Analysis, Relocation Planner, Scenario Studio and Methodology
- Foundation tests and team documentation

## Important limitation

This project is a decision-support prototype. It must not be presented as an autonomous evacuation-order system. Live integrations, real road-network routing, official shelter inventories and optional ML validation are added incrementally and must always expose source/freshness information.

## Install

```bash
python -m venv venv
# Windows
venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Tests

```bash
python -m pytest tests
```

## Team branches

- `feature/data`
- `feature/spatial`
- `feature/risk`
- `feature/relocation`
- `feature/dashboard`
- `feature/integration`

Shared contracts and architecture changes are proposed through `feature/architecture-v2` before being merged to `main`.

See `docs/team_plan.md`, `docs/data_dictionary.md`, `docs/architecture.md`, and `docs/data_sources.md` before implementing modules.
