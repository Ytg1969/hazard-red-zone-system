# Frozen Data Dictionary

## Habitability / habitation fields

Required: `habitation_id`, `name`, `latitude`, `longitude`, `population`, `children_population`, `elderly_population`.

Derived/optional: `hazard_score`, `exposure_score`, `vulnerability_score`, `accessibility_score`, `risk_score`, `risk_level`, `relocation_priority`, `data_timestamp`, `data_mode`.

Recommended administrative keys: `state_code`, `district_code`, `village_code`.

## Shelter / safe-zone fields

Required: `shelter_id`, `name`, `latitude`, `longitude`, `total_capacity`, `current_occupancy`.

Derived/optional: `water_capacity`, `sanitation_capacity`, `access_capacity`, `effective_capacity`, `available_capacity`, `safety_score`, `accessibility_score`, `last_updated`, `data_mode`.

## Rules

- Coordinates are decimal degrees (WGS84) unless a module explicitly reprojects internally.
- Scores use 0–100.
- Higher `accessibility_score` in the risk engine means greater evacuation difficulty; do not invert silently.
- Data mode must be one of `LIVE`, `CACHED`, `DEMO`.
- Shared field names may not be changed without integration-lead approval.
