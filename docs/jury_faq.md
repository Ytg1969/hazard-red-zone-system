# SIH26191 Jury FAQ

## How is this different from a normal GIS dashboard?
A conventional GIS dashboard primarily visualizes hazard layers. This system adds explainable habitation-level risk scoring, vulnerability prioritization, shelter carrying-capacity constraints, route-aware shelter ranking, multi-shelter allocation and phased relocation decisions.

## Why not let AI automatically decide evacuation?
Evacuation is an administrative and legal decision. The prototype is intentionally human-in-the-loop: it explains the factors, shows assumptions and produces decision-support recommendations for authorized officials.

## Why use weighted scoring instead of only machine learning?
The seven-day core must be explainable and robust even without a perfect historical training dataset. The weighted model provides transparent behavior. ML is an optional validation layer only when credible labels and leakage-safe evaluation are available.

## Are the default risk weights official standards?
No. They are transparent prototype defaults. Scenario Studio allows the emphasis to be changed while enforcing a total weight of 1.00. A real deployment would calibrate the defaults with the relevant disaster-management and domain experts.

## What happens when data is missing?
The app exposes data status and fallbacks. Carrying capacity is marked VALIDATED, PARTIAL or UNVALIDATED depending on available resource constraints. Live sources fall back to CACHED data where available, otherwise the user must explicitly switch to DEMO/static data.

## How do you avoid presenting demo data as live?
Every operational source is labelled LIVE, CACHED or DEMO. Bundled synthetic layers remain DEMO and the interface must not show them as live observations.

## Why not process satellite imagery or InSAR directly?
Raw SAR/InSAR processing is a substantial specialized workflow. The seven-day core is designed to ingest preprocessed hazard or deformation layers. Automated raw Sentinel-1 processing is a Phase-2 extension.

## How do you handle shelter carrying capacity?
The system does not rely only on physical beds. Effective capacity is limited by the minimum known resource constraint such as water, sanitation or access/logistics. Remaining capacity is calculated after current occupancy.

## What if one shelter cannot accommodate everyone?
The allocation routine distributes population across ranked safe shelters without exceeding available capacity and explicitly reports the remaining deficit.

## Why use road routing instead of straight-line distance?
Straight-line distance can recommend operationally poor shelters. The target workflow uses cached OpenStreetMap road graphs with OSMnx/NetworkX. If a graph cache is unavailable, the prototype clearly labels the haversine distance as a fallback.

## What happens if the internet fails during judging?
The application is designed to run from `data/demo/` with zero internet dependency. Road graphs are cached beforehand and live-data adapters use cache fallbacks. The demo must be rehearsed offline.

## How do you protect sensitive data?
The dashboard uses aggregate habitation-level counts rather than personally identifiable information. A real deployment would require role-based access control, audit logging and government data-governance policies.

## Can an administrator override the recommendation?
Yes. The system provides decision support, not an autonomous order. Officials can inspect factor contributions, test scenarios and select an alternative shelter based on verified field conditions.

## How is the project scalable?
The software contracts are location-independent. New districts/states can be added by supplying authoritative hazard, habitation, shelter and road data that conforms to the shared schemas and provenance requirements.
