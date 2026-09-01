# SIH26191 Production Deployment Guide

This application is a decision-support prototype being hardened for live operational use. The deterministic red-zone and relocation pipeline is offline-safe; live APIs are additive context and must never be treated as authoritative risk inputs without calibration.

## Recommended runtime

- Python 3.12
- Streamlit
- Linux-based deployment preferred
- HTTPS termination at the platform/load balancer
- Outbound HTTPS access required for live context and OSRM

## Environment variables

- `SIH_HABITATION_CSV_URL` — optional HTTPS URL for a validated operational habitation/settlement CSV. The Operational Data page fetches it with LIVE/CACHED provenance and validates it before use.
- `SIH_SHELTER_CSV_URL` — optional HTTPS URL for a validated operational shelter/relocation-site CSV. The Operational Data page fetches it with LIVE/CACHED provenance and validates it before use.
- `SIH_SACHET_FEED_URL` — verified NDMA SACHET-compatible CAP/RSS feed URL. If absent, the integration remains DEMO/unconfigured.
- `SIH_ROAD_GRAPHML` — optional local OSM GraphML road-network path. If absent, routing can fall through to OSRM and then explicit straight-line fallback.

Never place credentials inside the repository. If an authority feed requires authentication, configure credentials through the deployment platform's secret/environment facility and keep the public source documentation/schema in the repository.

No API keys are required by the current Open-Meteo, USGS, GDACS, NASA EONET, OSM or public OSRM integrations. IMD may require client/IP authorization; authorization failures must remain visible and must not be bypassed.

## Deployment options

### Streamlit Community Cloud
Best for SIH demonstration and public review. Deploy `app.py` from the `main` branch using Python 3.12. Add only verified operational feed settings under app secrets/environment configuration. Do not add fabricated secrets.

### Container / VM
For a controlled authority deployment, run behind a reverse proxy and use a persistent writable cache directory. Configure monitoring for process availability, outbound connectivity, filesystem usage and API latency.

## Production gates

Before promotion, run:

```bash
python -m pytest tests -q
python scripts/demo_gate.py
python scripts/production_gate.py
```

All three must pass.

## Operational data transition

`pages/9_Operational_Data.py` is the migration path from bundled demonstration cities to real authority datasets. It supports either operator-uploaded CSVs or configured HTTPS CSV feeds. The application validates required fields, coordinates, population/capacity integrity, carrying-capacity evidence and provenance before activation.

The bundled Puri/Guwahati/Chennai records must remain available only as fallback until a chosen study area's authoritative habitation, shelter and calibrated hazard inputs can drive every core page. Do not remove fallback data before that end-to-end replacement is tested.

## If a source cannot be fetched directly

Obtain one of the following from the accountable agency and preserve its source URL, publication/update date, license/terms and geographic coverage:

- CSV/XLSX settlement or vulnerability export
- CSV/XLSX shelter/relocation-site inventory
- GeoJSON/Shapefile hazard boundaries
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

External weather, event feeds and Bhuvan layers remain context-only until a documented source-specific mapping to a 0–100 analytical input is validated.

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
