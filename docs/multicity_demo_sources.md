# Multi-city demonstration data and source context

## Purpose

The bundled multi-city dataset is a **DEMO scenario**, not a claim of current operational conditions. It uses real Indian geographies and official hazard-context sources, while the habitation catchment populations, shelter capacities/occupancies, hazard indicator values and GeoJSON footprints are synthetic scenario inputs chosen to exercise the full decision-support pipeline.

The application must continue to display `DEMO` for these records.

## Why these three geographies

These are representative high-risk contexts selected to demonstrate different hazard families. They are **not presented as a definitive ranking of India's three most disaster-prone cities**.

### Puri, Odisha

Demonstrated hazards: cyclone, flood, drought and coastal inundation context.

Official context:
- Odisha State Disaster Management Authority, Puri District Disaster Management Plan 2025-26: https://www.osdma.org/wp-content/uploads/2019/05/DDMP-Puri-2025-Final.pdf
- OSDMA Early Warning Dissemination System: https://www.osdma.org/preparedness/early-warning-communications/ewds/
- OSDMA Integrated Coastal Zone Management Project / cyclone shelters: https://www.osdma.org/integrated-coastal-zone-management-project/

The Puri DDMP lists flood, cyclone, water-logging, drought, earthquake, tsunami, fire and heat wave among district hazards. OSDMA also identifies Puri among coastal districts prioritized for cyclone/flood/tsunami early-warning coverage.

### Guwahati, Assam

Demonstrated hazards: flood, landslide and earthquake.

Official context:
- Assam State Disaster Management Authority initiatives: https://asdma.assam.gov.in/about-us/detail/initiatives-and-interventions

ASDMA lists Flood Hazard Atlas/FLEWS work, seismic micro-zonation/earthquake-hazard assessment and landslide hazard-risk mitigation for Guwahati among its initiatives.

### Chennai, Tamil Nadu

Demonstrated hazards: urban/coastal flood, cyclone and drought/water-stress scenario.

For the bundled demo, Chennai is used as a realistic coastal metropolitan test geography. Before any claim of authoritative Chennai operational risk, replace the bundled scenario indicators with verified Tamil Nadu/IMD/CWC/NDMA source-specific data and document the exact source, reference period and mapping.

## Verified real-time/context APIs

### India Meteorological Department (IMD)

The official IMD API documentation lists public endpoints including current weather, district nowcast, district rainfall, district warnings, state rainfall, AWS/ARG data, river-basin quantitative precipitation forecast and RSS feeds.

The current project uses two verified official endpoint families for **context only**:
- District-wise warning API: `https://mausam.imd.gov.in/api/warnings_district_api.php`
- District-wise rainfall API: `https://mausam.imd.gov.in/api/districtwise_rainfall_api.php`

IMD's warning documentation defines `Day_1` ... `Day_5` warning codes and corresponding color levels. The adapter decodes the documented warning codes while preserving source fields. A successful call is `LIVE`; a previous successful response reused after failure is `CACHED`; if no live/cache response exists the page reports an empty `DEMO` context plus the error instead of fabricating weather observations.

The official IMD API page also instructs consumers to attribute IMD and use client-side caching. Some production access may require IP whitelisting, so venue connectivity must be checked before relying on it during judging.

Official documentation:
- https://mausam.imd.gov.in/responsive/apis.php
- https://mausam.imd.gov.in/imd_latest/contents/api.pdf

### USGS FDSN earthquake catalogue

`src/earthquake_context.py` uses the official USGS FDSN Event Web Service for recent earthquake context near Puri, Guwahati and Chennai. The query uses city center, search radius, time window and minimum magnitude and returns GeoJSON events.

Official API documentation:
- https://earthquake.usgs.gov/fdsnws/event/1/
- https://earthquake.usgs.gov/earthquakes/feed/

This earthquake feed is external context and never silently changes the deterministic prototype risk score.

## National alert integration

NDMA SACHET is the preferred national alert context. The public portal states that it is a CAP-based Integrated Alert System and publishes alerts to an RSS feed:
- https://sachet.ndma.gov.in/
- https://sachet.ndma.gov.in/CapFeed

The official integration guide documents an ETag-aware CAP XML retrieval pattern and requires consumers to cache XML and send `If-None-Match` on subsequent requests:
- https://sachet.ndma.gov.in/docs/Integration_Guide_For_Agencies.pdf

The shared live-data layer now supports ETag revalidation. HTTP 304 reuses the server-confirmed current cache as `CACHED` with `stale=False`; network failure uses the last response as stale `CACHED`. The application still does **not** invent a universal SACHET feed identifier. A verified endpoint/identifier must be configured before the UI may label that source `LIVE`.

## Bhuvan GIS integration path

NRSC/ISRO Bhuvan documents OGC-compliant WMS/WMTS services and lists Flood Hazard and Flood Annual Layers among consumable thematic services. The documented WMS service family includes:
- `https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms`

This proves the authoritative OGC service path, but the project must still verify the exact hazard layer identifier, legend/source classes, coverage, CRS and source-class-to-0-100 mapping before a Bhuvan layer is allowed to drive hazard scoring.

## Prototype multi-hazard indicator model

The transparent profiles in `src/hazard_model.py` cover:
- Flood
- Cyclone
- Landslide
- Earthquake
- Drought
- Combined multi-hazard

The indicator weights and numeric scaling bounds are explicit prototype assumptions, not official standards. Missing indicators cause the active weights to be re-normalized; the UI exposes data completeness. In authoritative deployments, replace these prototype rules with source-specific calibrated mappings.

## Demo honesty rules

1. Real geography does not make synthetic operational values authoritative.
2. Generic demo shelter names are used so synthetic capacities are not attributed to real institutions.
3. Do not claim the demo hazard footprints are official GIS boundaries.
4. Do not claim the scenario rainfall, wind, earthquake or drought indicators are current observations.
5. LIVE/CACHED/DEMO labels remain mandatory.
6. External LIVE context is isolated from analytical scoring until an explicit, source-specific integration mapping is verified.
