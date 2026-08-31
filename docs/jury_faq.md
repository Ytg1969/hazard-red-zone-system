# SIH26191 Jury FAQ

## How is this different from a normal GIS dashboard?
A conventional GIS dashboard primarily visualizes hazard layers. This system adds transparent multi-hazard scoring, explainable habitation-level risk, vulnerability prioritization, limiting-resource shelter capacity, route-aware ranking, multi-shelter allocation, system-wide no-double-booking and administrative action-plan export.

## Which hazards are supported?
The demonstration supports Flood, Cyclone, Landslide, Earthquake, Drought and a Combined Multi-Hazard profile. The profiles feed the Hazard term of the same frozen final risk model.

## Are the multi-hazard indicator weights official standards?
No. They are explicit prototype assumptions used to demonstrate explainability and missing-data handling. The interface exposes the breakdown and completeness. A deployment should replace those rules with verified source-specific hazard mappings or calibrated models.

## Why use Puri, Guwahati and Chennai?
They are representative high-risk Indian geographies that let the demo exercise coastal cyclone/flood, flood/landslide/earthquake and cyclone/flood/drought scenarios. We do **not** claim they are a definitive national top-three ranking.

## Is the three-city data real?
The geography anchors are real. Bundled catchment populations, operational shelter capacities/occupancies, hazard indicator values and hazard polygons are synthetic DEMO scenario inputs. This is deliberately labelled so the team does not present invented operational observations as government data.

## Why not let AI automatically decide evacuation?
Evacuation is an administrative and legal decision. The prototype is intentionally human-in-the-loop: it explains factors and assumptions and produces decision-support recommendations for authorized officials.

## What are the KMeans zones doing?
They are experimental coordination/briefing groups based on geography and final risk similarity. They do not change hazard scores, final risk, relocation priority, shelter eligibility or evacuation orders.

## Why use weighted scoring instead of only machine learning?
The core must be explainable and robust without assuming a perfect historical training dataset. The weighted risk model provides transparent behavior. ML should only become a predictive validation layer when credible labels and leakage-safe evaluation exist.

## Are the default final risk weights official standards?
No. They are transparent prototype defaults. Scenario Studio allows policy emphasis to change while enforcing a total weight of 1.00. Production defaults require domain/government calibration.

## What happens when data is missing?
The app exposes completeness and fallbacks. Multi-hazard indicator profiles re-normalize across available indicators. Carrying capacity is VALIDATED, PARTIAL or UNVALIDATED depending on known resource constraints. External feeds use LIVE/CACHED/DEMO states.

## How do you avoid presenting demo data as live?
Every operational source is labelled LIVE, CACHED or DEMO. Bundled multi-city scenario data remains DEMO. A source is only shown LIVE after a verified current fetch succeeds.

## What is the SACHET integration status?
The application includes CAP/RSS-compatible alert infrastructure and caching behavior. A verified SACHET endpoint/identifier must be configured before it can be presented as LIVE; the system does not invent an identifier.

## Why is USGS in an Indian disaster-management project?
USGS FDSN is used only as optional earthquake-catalog context and as a demonstration of a verified external API with LIVE→CACHED behavior. It does not replace Indian seismic-hazard products and does not silently alter the deterministic risk score.

## How do you handle shelter carrying capacity?
Effective capacity is limited by the minimum known physical/resource constraint such as total space, water, sanitation or access/logistics. Available capacity subtracts current occupancy, and allocation never exceeds it.

## What if one shelter cannot accommodate everyone?
Population can be split across ranked safe shelters. If the safe capacity is still insufficient, the remaining deficit is shown explicitly.

## How is system-wide allocation different from recommending a shelter one village at a time?
The batch planner updates shelter occupancy after each assignment, so the same capacity cannot be double-booked for several habitations. In the multi-city demo, assignments are also constrained to the same city.

## What is the global optimizer?
It is an optional NetworkX network-simplex comparison layer. Crucially, it can only create assignment edges to shelters that already pass the normal safety/capacity ranking gate. It includes an explicit deficit path rather than forcing unsafe or over-capacity assignments. It remains decision support, not an autonomous order.

## Why use road routing instead of straight-line distance?
Straight-line distance can recommend operationally poor shelters. Cached OpenStreetMap road graphs are the preferred demo route layer. If unavailable, the application clearly labels the haversine fallback.

## Can another district use the app?
Yes. Command Center accepts habitation and shelter CSVs after schema validation. Uploaded files are user-supplied data and are not automatically treated as LIVE government observations.

## What happens if the internet fails during judging?
The core analytical workflow is designed to run fully offline from committed DEMO data. SACHET/USGS context may fall back or disappear without breaking risk/capacity/relocation analysis. Road routing can use a pre-cached graph or labelled haversine fallback.

## Why not process satellite imagery or InSAR directly?
Raw SAR/InSAR processing is a specialized workflow outside the core. The architecture can ingest preprocessed deformation or authoritative hazard layers later.

## How do you protect sensitive data?
The dashboard uses aggregate habitation-level counts rather than personally identifiable information. Production would require role-based access, audit logging and government data-governance controls.

## Can an administrator override the recommendation?
Yes. Officials can inspect risk contributions, hazard assumptions, routes, capacity and alternatives. The application is not an autonomous evacuation-order system.

## How is the project scalable?
The software contracts are location-independent. New districts/states can provide authoritative hazard, habitation, shelter and road data while preserving the same provenance, risk, capacity and relocation interfaces.
