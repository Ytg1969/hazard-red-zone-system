# Odisha Pilot Data Plan

## Why Odisha

Odisha is a strong pilot geography for SIH26191 because it combines high disaster relevance with comparatively strong public disaster-management data availability and fits the system's current architecture.

Key reasons:

1. **Multi-hazard relevance.** Odisha's State Disaster Management Plan identifies cyclone vulnerability across the coastal districts, with Balasore, Bhadrak, Kendrapara and Jagatsinghpur classified as very highly cyclone-prone and Ganjam, Puri and Khordha as highly cyclone-prone.
2. **Operational shelter ecosystem.** OSDMA publishes a Multi Purpose Cyclone/Flood Shelter inventory and the Odisha Economic Survey reports district-wise cyclone/flood shelter counts. This makes capacity-aware relocation demonstrable with a real administrative context.
3. **Authoritative village-level population baseline.** Census of India 2011 Primary Census Abstract provides village-level population and demographic indicators for Odisha. These values must be labelled with source year 2011 and must not be presented as current population.
4. **GIS and warning-system relevance.** OSDMA already uses GIS, vulnerability mapping, early-warning systems and decision-support approaches, which aligns closely with the intended EOC workflow of this project.
5. **Low migration cost from the current demo.** The existing synthetic demonstration is anchored around Bhubaneswar/Khordha, so moving to an Odisha pilot minimizes unnecessary rework while preserving the offline DEMO fallback.

Odisha is therefore a practical pilot, not a claim that it is the only or universally 'most disaster-prone' state. The architecture remains state-agnostic.

## Pilot scope

Initial state: **Odisha**.

Recommended first operational subset: a manageable coastal district cluster rather than the entire state. Candidate districts should be selected based on data completeness across population, hazard layer and shelter inventory. Khordha/Puri or a similar coastal cluster is preferred for the first integrated build because it can exercise cyclone/flood exposure, shelter capacity and routing in one coherent geography.

## Source hierarchy

### Population and vulnerability baseline

Primary source:
- Office of the Registrar General & Census Commissioner, India (ORGI), Census 2011 Primary Census Abstract / Basic Population Figures at State, District, Sub-District and Village level.
- Source year must remain explicit: `2011`.
- Useful fields include total population and available demographic indicators that can support transparent vulnerability proxies.

Secondary Odisha catalogue:
- Odisha Open Government Data portal, Primary Census Abstract 2011 - Odisha.

### Shelter inventory

Primary source:
- Odisha State Disaster Management Authority (OSDMA), Multi Purpose Cyclone/Flood Shelters.

Supporting source:
- Odisha Economic Survey statistical appendix, district-wise MCS/MFS shelter counts.

Shelter records must not receive invented resource capacities. Unknown water, sanitation or access capacities remain null/unknown so the existing `VALIDATED` / `PARTIAL` / `UNVALIDATED` logic stays truthful.

### Hazard layer

Priority source family:
- OSDMA State Disaster Management Plan cyclone vulnerability mapping.
- OSDMA Flood Hazard Atlas / other authoritative state or national hazard layers where machine-readable geometry can be obtained and licensing/access is clear.

Do not convert a map image into operational polygons unless the derivation method is documented and clearly marked as derived rather than source-native GIS data.

## Mapping into the frozen habitation contract

Required project fields:

- `habitation_id`
- `name`
- `latitude`
- `longitude`
- `population`
- `children_population`
- `elderly_population`

Recommended administrative keys:

- `state_code`
- `district_code`
- `village_code`

Source metadata to retain alongside ingestion:

- `source_name`
- `source_url`
- `source_year`
- `source_retrieved_at`
- `source_license_or_terms`
- `data_mode`

Where the source does not provide a required demographic field such as children or elderly population at the chosen granularity, the adapter must not silently fabricate it. The field must be derived only through a documented method or remain unavailable until a defensible source is added.

## Data-mode rule

- Bundled synthetic data: `DEMO`
- Previously fetched authoritative snapshot used offline: `CACHED`
- Data fetched from a verified source during the current session: `LIVE`

Historical Census data is authoritative but historical. `LIVE` describes retrieval mode, not population recency. The UI must display both data mode and source year where relevant.

## Phase-2 acceptance criteria

The Odisha pilot-data phase is complete when:

1. At least one district has authoritative habitation/population records mapped to the frozen contract.
2. Source year and provenance are visible and preserved.
3. At least one real shelter inventory is ingested without inventing missing capacities.
4. DEMO data remains available as offline fallback.
5. Existing preprocessing tests and end-to-end tests still pass.
6. The UI can distinguish authoritative/CACHED inputs from DEMO inputs.

## Next implementation step

Build a deterministic Odisha Census adapter that converts selected ORGI village-level records into the project's habitation schema while preserving Census codes and provenance. Coordinate enrichment should be handled as a separate, documented join because Census PCA tables are demographic tables and should not be assumed to contain trustworthy WGS84 village centroids.
