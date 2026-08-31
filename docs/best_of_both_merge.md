# Curated best-of-both merge

Source reviewed: `Ytg1969/hazard-red-zone-system-22`.

The second repository contains useful presentation and routing ideas, but it also contains alternate analytical contracts that conflict with the frozen SIH26191 risk/capacity methodology. This merge therefore ports only compatible improvements.

## Adopted

- Road-route geometry for map visualization when a cached OSM GraphML file is available.
- Explicit dashed straight-line fallback when no local road cache exists.
- Multi-city road-cache helper for Puri, Guwahati and Chennai.
- Custom bounding-box road-cache option.
- Recommended shelter route displayed directly on the Red Zone Map after the existing safety/capacity ranking gate.

## Kept from the primary repository

- Frozen risk equation: `0.35H + 0.25E + 0.25V + 0.15A`.
- Frozen risk thresholds: LOW 0–29, MODERATE 30–49, HIGH 50–69, CRITICAL 70–100.
- Existing multi-hazard profiles and explainability contract.
- Effective/available shelter-capacity rules and validation status.
- Same-city allocation safeguards and global optimizer safety gate.
- LIVE/CACHED/DEMO provenance semantics.
- Open-Meteo, USGS, GDACS, IMD authorization handling, SACHET infrastructure and Bhuvan WMS context.

## Deliberately not copied

- Alternate AHP defaults/thresholds or labels that conflict with the frozen risk contract.
- Dataset-relative min/max hazard scaling, because scores can change when rows are added or removed and therefore are not stable operational semantics.
- Claims of congestion-aware or hazard-avoiding routing without verified live traffic, road-capacity or hazard-intersection data.
- The committed Bhubaneswar GraphML cache as a default for the three-city demo; demo routing caches must match the selected city.
- The separate premium launcher referenced by the second repository because its referenced `ui` package is not present in that repository tree.

## Demo road-cache command

```powershell
py -3.13 scripts/cache_road_network.py --demo-cities
```

Large GraphML files should remain local cache artifacts. The application continues to work without them using an explicitly labelled straight-line fallback.
