# Team Implementation Plan

## Member 1 — Data & Vulnerability
Branch: `feature/data`
Owns: `data/`, `src/preprocessing.py`, `src/vulnerability.py`
Deliver: frozen schemas, cleaned habitation/shelter data, provenance, vulnerability inputs, offline demo dataset.

## Member 2 — GIS & Hazard
Branch: `feature/spatial`
Owns: `src/spatial_analysis.py` and hazard preparation assets.
Deliver: vector/raster ingestion, CRS handling, spatial intersection, hazard exposure, map-ready outputs.

## Member 3 — Risk & Optional ML
Branch: `feature/risk`
Owns: `src/risk_engine.py`; optional `src/ml_engine.py` only if credible labelled data is found.
Deliver: normalized 0–100 risk factors, explainable risk score/class, scenario weights, optional ML validation.

## Member 4 — Capacity, Routing & Relocation
Branch: `feature/relocation`
Owns: `src/carrying_capacity.py`, `src/routing.py`, `src/relocation.py`.
Deliver: limiting-resource capacity, safe-shelter filtering, cached road routing, capacity-aware ranking/allocation, relocation priority.

## Member 5 — Dashboard / UX
Branch: `feature/dashboard`
Owns: `app.py`, `pages/`, presentation layer.
Deliver: operational overview, red-zone map, risk analysis, relocation workflow, scenario studio, professional error/empty states.

## Member 6 — Integration / QA / SIH
Branch: `feature/integration`
Owns: tests, docs, PR review, end-to-end integration, demo/PPT flow.
Deliver: stable `main`, nightly smoke tests, interface compliance, offline fallback, Antigravity review on the real cloned repository.

## Merge order
Data → GIS/Vulnerability → Risk → Capacity/Routing/Relocation → Dashboard.

## Daily rule
`main` must run at the end of every day using `data/demo/` even with internet disabled.
