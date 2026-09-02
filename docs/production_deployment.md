# SIH26191 Production Deployment Guide

This application is a decision-support prototype being hardened for live operational use. The deterministic red-zone and relocation pipeline is offline-safe; live APIs are additive context and must never be treated as authoritative risk inputs without calibration.

## Recommended runtime

- Python 3.12
- Streamlit
- Linux-based deployment preferred
- HTTPS termination at the platform/load balancer
- Outbound HTTPS access required for live context and OSRM

## Environment variables

- `SIH_HABITATION_CSV_URL` — optional HTTPS URL for a validated operational habitation/settlement feed. Despite the compatibility name, the endpoint may return CSV or Point GeoJSON/JSON. Configured feeds are validated and can bootstrap new browser sessions through the Streamlit server cache.
- `SIH_SHELTER_CSV_URL` — optional HTTPS URL for a validated operational shelter/relocation-site feed. CSV and Point GeoJSON/JSON are supported.
- `SIH_HAZARD_GEOJSON_URL` — optional HTTPS GeoJSON hazard source. Every feature must contain a numeric `hazard_score` in the range 0–100.
- `SIH_HAZARD_CALIBRATION_CONFIRMED=true` — mandatory gate before a configured hazard GeoJSON can supply the analytical H component. Do not set this until the class/value mapping is documented and reviewed.
- `SIH_HAZARD_SOURCE_LABEL` — optional human-readable source/layer label for hazard provenance.
- `SIH_SACHET_FEED_URL` — verified NDMA SACHET-compatible CAP/RSS feed URL. If absent, the integration remains explicitly unconfigured rather than fabricating identifiers or alerts.
- `SIH_ROAD_GRAPHML` — optional local OSM GraphML road-network path. If absent, routing can fall through to OSRM and then explicit straight-line fallback.
- `SIH_REQUIRE_OPERATIONAL_DATA=true` — strict production mode. When enabled, pages that require habitation/shelter analysis stop instead of falling back to bundled synthetic demo cities if validated operational data is unavailable.

Do not enable `SIH_REQUIRE_OPERATIONAL_DATA=true` until both operational settlement and relocation-site feeds are configured and tested. It is a final cutover switch, not a substitute for real data.

Never place credentials inside the repository. If an authority feed requires authentication, configure credentials through the deployment platform's secret/environment facility and keep the public source documentation/schema in the repository.

No API keys are required by the current Open-Meteo, USGS, GDACS, NASA EONET, OSM or public OSRM integrations. IMD may require client/IP authorization; authorization failures must remain visible and must not be bypassed.

## Dependency profiles

- `requirements.txt` — production/Streamlit Cloud runtime. It excludes test tooling and the optional OSMnx local-graph stack to reduce deployment installation time.
- `requirements-routing.txt` — production requirements plus OSMnx for local cached GraphML routing.
- `requirements-dev.txt` — routing bundle plus pytest for local development/testing. Optional experimental coordination clustering dependencies belong here rather than in the production web runtime.

The deployed app still retains the routing fallback chain when OSMnx is absent: live OSRM → cached OSRM → explicit haversine fallback.

## Streamlit Community Cloud

Best for SIH demonstration and public review.

Deploy:

- repository: `Ytg1969/hazard-red-zone-system`
- branch: `main`
- entrypoint: `app.py`
- Python: `3.12`

The app can initially be deployed with no secrets for public/no-key context and the fallback demonstration path. Add only verified operational feed configuration after deployment. When the real operational dataset and calibrated hazard layer are stable, enable `SIH_REQUIRE_OPERATIONAL_DATA=true` to prevent synthetic fallback on analytical pages.

After deployment, smoke-test these pages in this order:

1. Overview / landing page
2. Operations Hub
3. Operational Data
4. Red Zone Map
5. Risk Analysis
6. Relocation Planner and PDF export
7. Live Data Explorer
8. System Readiness
9. GIS Source Inspector

If deployment fails, record the first red build/runtime error before changing dependencies.

## Container / VM

For a controlled authority deployment, run behind a reverse proxy and use a persistent writable cache directory. Configure monitoring for process availability, outbound connectivity, filesystem usage and API latency.

## Production gates

Before promotion, run:

```bash
python -m pytest tests -q
python scripts/demo_gate.py
python scripts/production_gate.py
```

All three must pass. Pull requests also run a Python 3.12 deployment smoke workflow that installs the production dependencies, launches Streamlit and checks `/_stcore/health`.

## Operational data transition

`pages/9_Operational_Data.py` is the migration path from bundled demonstration cities to real authority datasets. It supports operator-uploaded CSV or Point GeoJSON/JSON datasets, configured HTTPS CSV/Point GeoJSON feeds, and a calibrated GeoJSON hazard layer. The application validates required fields, coordinates, population/capacity integrity, carrying-capacity evidence and provenance before activation.

For Point GeoJSON habitation/site inputs, coordinates are read from feature geometry. Non-Point geometries are rejected instead of being silently centroided because centroid selection can change the analytical and routing meaning of an official feature.

Bundled Puri/Guwahati/Chennai records must remain fallback-only until a chosen study area's authoritative habitation, shelter and calibrated hazard inputs can drive every core page. Do not relabel fallback data as real. Once the end-to-end replacement is tested, enable strict operational mode and then remove the bundled fallback in a later cleanup release.

## If a source cannot be fetched directly

Obtain one of the following from the accountable agency and preserve its source URL, publication/update date, license/terms and geographic coverage:

- CSV/XLSX settlement or vulnerability export
- CSV/XLSX shelter/relocation-site inventory
- Point GeoJSON/JSON settlement or shelter feed
- GeoJSON/Shapefile/GeoTIFF hazard boundaries
- WMS/WFS/WMTS/ArcGIS REST endpoint plus exact layer name
- API documentation plus a representative JSON/XML response
- public data.gov.in/Bhuvan/SDMA/district/IMD/CWC/GSI download link

Do not substitute guessed values for unavailable official data. If a source needs login, token or IP allow-listing, document the public endpoint/schema and configure the credential separately in deployment secrets.

## Data governance

Every dataset shown to an operator must carry a mode or provenance interpretation:

- `LIVE` — successfully retrieved from the named external source.
- `CACHED` — previously retrieved external data reused because refresh was unavailable or intentionally avoided.
- `DEMO` — bundled, synthetic or unverified operational values.

Unknown data must never be converted to zero merely to make the pipeline complete.

## Risk safety boundary

The frozen baseline remains:

`Risk = 0.35H + 0.25E + 0.25V + 0.15A`

External weather, event feeds and uncalibrated Bhuvan layers remain context-only until a documented source-specific mapping to a 0–100 analytical input is validated.

## Shelter safety boundary

- Reject `safety_score < 50`.
- Reject full/zero-available-capacity shelters.
- Effective capacity is limited by known resource constraints.
- Shared-capacity allocation must never overbook a shelter.

## Routing claims

Route provenance must be explicit:

1. local cached OSM graph
2. live OSRM route
3. cached OSRM route
4. straight-line haversine fallback

The system does not currently claim live traffic, road-closure awareness or hazard-avoiding routing.

## Operational limitations before authority use

The following remain production prerequisites rather than hidden assumptions:

- authoritative habitation and vulnerability datasets for the chosen study area
- verified relocation-site inventories and infrastructure capacities
- calibrated Bhuvan or other official hazard-class mappings where used numerically
- authorized IMD access if direct API ingestion is required
- verified SACHET production feed configuration
- documented update frequency and accountable data owner for every operational dataset
- field validation and administrative review of relocation-site suitability

## Release rule

Never promote a change that makes the application appear more certain than its source evidence. A degraded live source must degrade visibly while the deterministic offline workflow continues safely.
