# Risk, Capacity and Relocation Methodology

## 1. Default explainable risk score

All factors are normalized to 0–100.

`Risk = 0.35 × Hazard + 0.25 × Exposure + 0.25 × Vulnerability + 0.15 × EvacuationDifficulty`

Higher values mean higher risk for every input, including evacuation difficulty.

### Classes

- 0–29: LOW
- 30–49: MODERATE
- 50–69: HIGH
- 70–100: CRITICAL

### Driver explanation

The system ranks risk drivers by **weighted contribution**, not by raw factor value. Example: a Hazard value of 80 at weight 0.35 contributes 28 risk points.

## 2. Scenario weights

Scenario Studio may change factor emphasis only when:

- the four normalized weights sum to 1.0;
- no weight is negative;
- the recommended defaults remain available;
- the UI reports how classifications and affected population change;
- the app labels the output as scenario analysis rather than an official order.

The UI accepts intuitive slider values and automatically normalizes them before risk calculation.

## 3. Demonstration GIS hazard score

When a vector hazard layer is available:

1. Create a habitation point from longitude/latitude.
2. If the point intersects one or more hazard polygons, use the maximum intersecting `hazard_score`.
3. If it is outside all polygons, calculate distance to the nearest hazard geometry using a projected metric CRS.
4. For the demonstration only, apply a transparent linear proximity decay within 10 km; beyond 10 km the vector-derived score becomes zero.
5. Record whether the habitation is inside a hazard polygon, the nearest distance, hazard type and source.

This proximity rule is a demo behavior, not a universal hazard-science standard. Authoritative production hazard layers may supply their own intensity/susceptibility values instead.

## 4. Vulnerability

Current baseline:

`Vulnerability = (children_population + elderly_population) / population × 100`

The score is bounded to 0–100. Production deployments may extend this with approved indicators such as disability prevalence, housing quality, poverty, health access or warning access when reliable datasets exist.

## 5. Carrying capacity

Known resource constraints are evaluated independently.

Pseudo-code:

```text
known = []
if water_capacity exists: add water_capacity
if sanitation_capacity exists: add sanitation_capacity
if access_capacity exists: add access_capacity

if all defined resource capacities exist:
    effective_capacity = min(total_capacity, known capacities)
    capacity_validation_status = VALIDATED
elif at least one resource capacity exists:
    effective_capacity = min(total_capacity, known capacities)
    capacity_validation_status = PARTIAL
else:
    effective_capacity = total_capacity
    capacity_validation_status = UNVALIDATED

available_capacity = max(0, effective_capacity - current_occupancy)
```

`data_mode` and `capacity_validation_status` are separate concepts. LIVE/CACHED/DEMO describes source freshness; VALIDATED/PARTIAL/UNVALIDATED describes the completeness of the capacity constraints.

## 6. Relocation priority

Current explainable baseline:

- CRITICAL + vulnerability >= 60: IMMEDIATE
- CRITICAL or HIGH: SHORT_TERM
- MODERATE: MEDIUM_TERM
- LOW: MONITOR

These labels are configurable decision-support categories, not statutory evacuation timelines.

## 7. Shelter ranking

Unsafe shelters and shelters with no available capacity are removed first.

Default suitability score:

`Suitability = 0.35 × Safety + 0.25 × CapacityAdequacy + 0.20 × Accessibility + 0.20 × DistanceDesirability`

Where:

- Safety, accessibility and distance desirability are normalized to 0–100.
- Capacity adequacy is capped at 100 and compares available capacity with the habitation population.
- Distance desirability currently decays linearly to zero at the transparent demo reference distance of 30 km.

The highest-ranked candidate becomes the primary recommendation.

## 8. Multi-shelter allocation

If one shelter cannot support the whole habitation population, the system walks through ranked candidates and assigns no more than each shelter's available capacity. The output reports:

- required population;
- allocated population;
- assigned population per shelter;
- remaining capacity deficit.

No allocation is allowed to exceed available capacity.

## 9. Routing

Routing uses two modes:

- `cached_osm_graph`: shortest road-network distance from a pre-downloaded OSM GraphML file;
- `haversine_fallback`: straight-line distance when no graph cache is available or road routing fails.

The routing mode is always exposed to the UI and action plan.

## 10. Optional ML validation

`src/ml_engine.py` provides an optional Random Forest validation utility. It is deliberately isolated from the operational risk engine.

Do not report ML accuracy unless:

- labels come from credible historical observations;
- the dataset size and class distribution are defensible;
- spatial/temporal leakage is controlled;
- the train/test methodology is documented;
- the model improves understanding rather than hiding assumptions.

Synthetic unit-test labels validate software behavior only and are not scientific evidence.
