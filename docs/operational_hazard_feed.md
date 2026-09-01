# Persistent calibrated hazard feed

The deployed application can use an operator-validated GeoJSON hazard layer during a browser session. This tranche extends that path for deployment by supporting a configured HTTPS GeoJSON source when the layer has an approved 0-100 mapping.

## Required deployment variables

- `SIH_HAZARD_GEOJSON_URL` — HTTPS URL returning a GeoJSON `FeatureCollection`.
- `SIH_HAZARD_MAPPING_APPROVED=true` — explicit deployment acknowledgement that the source's hazard classes/values have a documented and reviewed mapping to the application's 0-100 hazard scale.

The application must not use a configured hazard GeoJSON analytically unless the approval flag is true. A reachable URL alone is not evidence of calibration.

## Feature contract

Every feature must contain:

- a valid geometry;
- numeric `hazard_score` in the inclusive range 0-100.

Recommended provenance properties:

- `hazard_type`
- `source`
- `reference_period`
- `source_url`
- `mapping_version`
- `updated_at`

## Safety boundary

Configured live weather, alert and event feeds remain contextual unless separately calibrated. This feed only supplies H when its numeric mapping has been explicitly approved; the frozen risk formula remains unchanged:

`Risk = 0.35H + 0.25E + 0.25V + 0.15A`
