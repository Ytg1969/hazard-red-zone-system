# Demo Readiness Gate

This document defines the point at which the SIH26191 prototype is safe to demonstrate to teammates or judges without overstating the maturity of the authoritative Puri pilot.

## Demo-ready means

The presentation may proceed when all of the following are true:

- the deterministic offline `DEMO` dataset loads;
- synthetic hazard GeoJSON loads or the UI clearly falls back to stored demo hazard scores;
- risk scoring produces bounded LOW / MODERATE / HIGH / CRITICAL classes;
- carrying-capacity calculation produces non-negative available capacity;
- Red Zone Map, Risk Analysis, Relocation Planner and Scenario Studio load without Streamlit exceptions;
- shelter recommendations never allocate beyond available capacity;
- the UI clearly shows `DEMO` for synthetic operational data;
- `python scripts/demo_gate.py` reports `"demo_ready": true`;
- `python -m pytest tests -q` passes;
- the same core workflow is manually opened once before judging.

## What may be demonstrated now

The working offline path can demonstrate:

1. GIS-based hazard exposure from synthetic vector polygons.
2. Vulnerability and evacuation-difficulty scoring.
3. Explainable weighted risk classification.
4. Red-zone prioritization.
5. Limiting-resource shelter capacity.
6. Safe-shelter filtering and multi-shelter allocation.
7. Road-aware routing when a cached graph is configured, with haversine fallback otherwise.
8. Scenario-weight adjustment.
9. Draft administrative action-plan export.
10. Odisha/Puri authoritative-source and readiness status on the Phase-2 branch.

## What must not be claimed yet

Until the Puri readiness gate passes, do not claim that the demo uses:

- current real population;
- complete village-level elderly population;
- verified coordinates for every Puri village/shelter;
- live shelter occupancy;
- complete shelter resource capacities;
- an operational authoritative flood/cyclone geometry layer;
- validated predictive accuracy for real emergencies.

## Judge-safe wording

Use:

> This is a working offline decision-support prototype. The end-to-end demo uses clearly labelled synthetic operational data, while the Odisha/Puri authoritative pilot is being integrated behind strict provenance and completeness gates.

Avoid:

> This is a live operational disaster system for Puri.

## Final preflight commands

```powershell
py -3.13 scripts/demo_gate.py
py -3.13 -m pytest tests -q
py -3.13 -m streamlit run app.py
```

Then manually open the Overview, Red Zone Map, Risk Analysis, Relocation Planner and Scenario Studio before the presentation.
