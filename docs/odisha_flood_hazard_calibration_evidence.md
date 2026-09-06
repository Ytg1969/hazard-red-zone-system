# Odisha flood-hazard calibration evidence

Status: **EVIDENCE VERIFIED · ANALYTICAL CUTOVER BLOCKED**

This note records the strongest authoritative flood-hazard evidence currently verified for an Odisha/Puri pilot. It is deliberately **not** an activation configuration and does not authorize any source to supply the application's analytical `H` component yet.

The frozen application contract remains:

`Risk = 0.35H + 0.25E + 0.25V + 0.15A`

A hazard source may supply `H` only after the exact machine-readable product and a reviewed source-specific mapping to `hazard_score` 0–100 are documented and `SIH_HAZARD_CALIBRATION_CONFIRMED=true` is intentionally enabled.

## Authoritative source chain

### Odisha Flood Hazard Atlas, 2001–2018

Primary state-authority copy:

- Odisha State Disaster Management Authority (OSDMA): `https://www.osdma.org/wp-content/uploads/2019/09/Flood-Hazard-Atlas.pdf`

The atlas states that it was prepared by the National Remote Sensing Centre (NRSC), ISRO, in association with OSDMA and in coordination with NDMA. It uses Indian and foreign satellite observations spanning 2001–2018 to classify flood hazard by inundation frequency.

NRSC technical-document copy discovered from the official Bhuvan flood-hazard application:

- `https://bhuvan-app1.nrsc.gov.in/disaster/usrtasks/flood/doc/or-hz.pdf`

Official Bhuvan flood-hazard application:

- `https://bhuvan-app1.nrsc.gov.in/disaster/usrtasks/flood_hz/flood_hz.php?uname=empty`

### Generic Bhuvan thematic Flood Hazard WMS

Bhuvan Store / Bhuvan Wiki publish this generic Flood Hazard WMS endpoint:

- `https://bhuvan-ras2.nrsc.gov.in/cgi-bin/hazard.exe`

However, the Bhuvan Store metadata describes that generic Flood Hazard service as derived from flood data from **1998–2007**, while the Odisha atlas documented above is the **2001–2018** product. The current Bhuvan Flood Hazard Zones application also describes a broader integration of annual inundation layers through 2019.

**Therefore the project must not assume that `hazard.exe` plus a guessed Odisha layer name is the machine-readable equivalent of the 2001–2018 Odisha atlas.** The exact layer identifier, product vintage, legend, CRS, spatial bounds and export/query behavior must be verified from the official service before analytical use.

## Verified Odisha classification schema

The 2001–2018 Odisha atlas classifies flood hazard by the number of observed inundations during the 18-year period:

| Hazard code | Atlas severity | Observed inundation frequency, 2001–2018 | Atlas hazard weight |
| ---: | --- | --- | ---: |
| 1 | Very Low | 1 time | 1 |
| 2 | Low | 2–4 times | 2 |
| 3 | Moderate | 5–6 times | 3 |
| 4 | High | 7–9 times | 4 |
| 5 | Very High | 10–14 times | 5 |

The atlas uses the 1–5 weights in its own district flood-hazard-index methodology. These are **source-native ordinal weights**, not the application's 0–100 `hazard_score` values.

### Calibration boundary

No source-class → 0–100 mapping is approved in this repository yet.

In particular:

- do not treat atlas code 5 as an automatic `hazard_score=100`;
- do not linearly rescale codes 1–5 without an explicit reviewed calibration decision;
- do not infer a score for Normal / River / Water Body / No-data classes;
- do not convert unknown or uncovered areas to zero;
- do not use district-level hazard index or rank as a habitation-level hazard score.

Any future mapping must document the rationale, treatment of no-data/water classes, spatial resolution/scale, source vintage, validation evidence and a version identifier.

## Verified Puri district evidence

The atlas reports Puri among the eight worst flood-affected districts by district flood-hazard area.

District summary:

- geographical area: **347,900 ha**
- total flood-hazard area: **185,028 ha**
- flood-hazard share of district area: **53%**
- atlas flood-hazard index: **22**
- atlas rank: **5**

Puri flood-hazard area by source class:

| Hazard code | Severity | Area (ha) |
| ---: | --- | ---: |
| 1 | Very Low | 39,583 |
| 2 | Low | 57,053 |
| 3 | Moderate | 26,364 |
| 4 | High | 35,187 |
| 5 | Very High | 26,841 |
|  | **Total** | **185,028** |

These statistics provide strong evidence that Puri is an appropriate flood-focused study area. They do **not** provide feature geometry or habitation-level `hazard_score` values by themselves.

## Source limitations that must remain visible

The atlas/Bhuvan material notes limitations including:

- satellite passes may not coincide with peak flooding;
- available satellite coverage controls what inundation can be observed;
- observed inundation can include embankment breaches and rainwater accumulation in low-lying/coastal areas;
- localized/flash/minor flooding may not always be captured;
- the atlas is a historical frequency product, not a live flood-extent feed.

The atlas reports that maps were supplied through OSDMA to district administrations for feedback/ground validation. This strengthens provenance, but does not remove the need to verify the exact machine-readable layer used by this application.

## Machine-readable cutover status

### Verified

- accountable source organizations: NRSC/ISRO + OSDMA, with NDMA coordination
- Odisha atlas reference period: 2001–2018
- five source-native frequency classes and definitions
- source-native ordinal hazard weights 1–5
- Puri district summary and class-wise areas
- generic Bhuvan Flood Hazard WMS service URL exists

### Unresolved — hard blockers

- exact official WMS/WMTS/WFS/other machine-readable **Odisha 2001–2018 layer identifier**
- proof that the machine-readable layer corresponds to the same atlas vintage/schema
- exact CRS and spatial bounds of that product
- legend/class encoding in the machine-readable response
- whether a vector/query/export path exists that can preserve source classes without screen/image digitization
- reviewed source-class → application 0–100 `hazard_score` mapping
- treatment of normal river/waterbody, outside-coverage and no-data cells/features
- bounded Puri export and end-to-end habitation overlay validation

Until all required items are resolved, this source remains **calibration evidence only** and `SIH_HAZARD_CALIBRATION_CONFIRMED` must remain false/unset for this product.

## Layer-name investigation record

Official Bhuvan pages expose real WMS layer naming for some annual layers (for example, the current flood page links to Assam annual-layer legend requests such as `as_fld_1999`). A historical third-party example also references an Assam flood-hazard layer named `as_hz`.

Neither item proves the Odisha hazard-layer identifier. Searches of the official indexed pages did not expose an Odisha `_hz` layer key. **Do not infer `or_hz`, `od_hz`, or any other Odisha identifier from naming conventions.**

## Acceptance criteria for analytical activation

Before an Odisha/Puri flood-hazard product may supply analytical `H`:

1. Capture the exact official machine-readable endpoint and layer/product identifier.
2. Save the official capabilities/metadata/legend evidence with reference date and product vintage.
3. Prove its schema matches the intended Odisha atlas product or document the newer authoritative replacement.
4. Obtain a bounded Puri extract in a format the project can validate reproducibly, preferably GeoJSON/vector or a documented raster-to-feature workflow.
5. Preserve source classes and no-data semantics during conversion.
6. Document and review the explicit source-class → 0–100 `hazard_score` mapping.
7. Add provenance fields including source, source URL, reference period, mapping version and retrieval/conversion time.
8. Run the project hazard validator, overlay checks, Foundation Tests, Deployment Smoke and an authoritative Puri end-to-end smoke.
9. Only then enable `SIH_HAZARD_CALIBRATION_CONFIRMED=true` for the reviewed deployment.

## Operational interpretation

This evidence improves source readiness without changing current risk results. The application's bundled DEMO hazards remain explicitly synthetic; the Odisha atlas must not be relabelled as an active analytical feed until the machine-readable and calibration gates above are satisfied.
