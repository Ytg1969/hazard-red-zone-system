# Puri Pilot — Authoritative Hazard Layer Integration

## Goal
Integrate at least one authoritative machine-readable hazard layer for the Puri pilot without converting a static map image into operational geometry by guesswork.

## Preferred source order

1. **NRSC/ISRO Bhuvan thematic services** — preferred machine-readable candidate because Bhuvan exposes thematic GIS services and lists Flood Hazard / Flood Annual Layers among available themes. The exact layer/service name must be verified from the live Bhuvan service catalogue before coding an adapter.
2. **OSDMA Flood Hazard Zonation Atlas — Odisha** — authoritative reference produced by NRSC/ISRO with OSDMA and coordinated with NDMA. Use it to validate interpretation, provenance and expected spatial patterns. Do not treat the PDF itself as a machine-readable operational layer unless a documented georeferencing/digitisation method is explicitly adopted.
3. **OSDMA State Hazard Map / State Disaster Management Plan** — contextual validation only unless a machine-readable layer is exposed.

## Integration contract

The existing GIS engine expects a vector layer that can be normalised to EPSG:4326 and includes a numeric `hazard_score` in the 0–100 range.

For an authoritative source, preserve these extra fields whenever possible:

- `hazard_type`
- `source_name`
- `source_url`
- `source_date` or `reference_period`
- `source_class` / source-native hazard category
- `score_method`
- `data_mode`

## Scoring rule

Do not invent a continuous 0–100 score until the source-native classes/legend are verified. If the source exposes categorical hazard classes, create a documented mapping table such as:

`source class -> hazard_score`

The mapping must be explicit, reproducible, monotonic with source severity and documented in `docs/risk_methodology.md` or a source-specific note.

## Acceptance checks

Before a Puri hazard layer is marked ready:

- exact authoritative service/download URL verified
- source layer name/schema recorded
- CRS identified and transformed to EPSG:4326 when required
- geometry validity checked
- Puri subset clipped without altering source meaning
- source-native hazard classes retained
- 0–100 mapping documented
- one or more known locations visually cross-checked against the OSDMA atlas/context map
- output works offline after being cached locally
- dashboard labels the data as `CACHED`, not `LIVE`, unless it is actually fetched live at runtime

## Coordinate-data note

Bhuvan can display settlement/census-related geographic information, but its public forum has historically directed users to Survey of India for downloadable village-boundary shapefiles. Therefore we should not claim that Bhuvan provides a downloadable authoritative village-boundary file until an exact current download/service is verified.

## Current status

- OSDMA Flood Hazard Zonation Atlas: verified authoritative reference.
- Bhuvan thematic Flood Hazard / Flood Annual Layers: verified as an official service family/candidate.
- Exact Puri machine-readable Bhuvan layer/service identifier: still to be verified before adapter implementation.
