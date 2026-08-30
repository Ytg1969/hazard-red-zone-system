# Odisha / Puri Pilot Data Staging

This directory is for authoritative pilot inputs and derived staging outputs. The committed DEMO dataset remains separate and must continue to work offline.

## Rules

- Do not commit fabricated values to make a row operational-ready.
- Census 2011 population must retain `population_reference_year = 2011` and be described as historical/CACHED.
- Unknown shelter occupancy/capacity remains null/unknown, not zero.
- Coordinates must come from a verified source and be WGS84 decimal degrees before they enter the frozen operational schema.
- Hazard classes must be mapped to 0-100 only through an explicit, documented mapping for the exact authoritative layer.

## Expected staged files

A local integration run may produce:

- `data/pilot/processed/habitations.csv`
- `data/pilot/processed/shelters.csv`
- `data/pilot/processed/hazards.geojson`

These files should only be called operational-ready when the readiness gate passes.

Run:

```bash
python scripts/check_pilot_readiness.py \
  --habitations data/pilot/processed/habitations.csv \
  --shelters data/pilot/processed/shelters.csv \
  --fail-if-not-ready
```

The command prints a JSON report with missing fields and completeness percentages. It does not fill any gaps.

## Provenance

Every authoritative source used for the pilot must be recorded in `data/pilot/source_manifest.csv` with source authority, URL, reference year/date, coverage, intended use and default data mode.
