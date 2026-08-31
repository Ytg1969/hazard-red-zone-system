# Technical Architecture — SIH26191

## Decision pipeline

`LIVE/CACHED/DEMO data → normalization → GIS exposure → transparent hazard profile → vulnerability → frozen explainable risk → red-zone class → relocation priority → shelter safety/capacity → routing → allocation/optimization → dashboard/export`

## Multi-hazard layer

`src/hazard_model.py` provides explicit prototype profiles for Flood, Cyclone, Landslide, Earthquake and Drought plus a Combined profile. Indicator scores are bounded to 0–100 using documented physical/proxy ranges. Missing indicators re-normalize only the active weights and expose data completeness.

The multi-hazard layer feeds only the Hazard term. It does not change the frozen final risk equation:

`Risk = 0.35H + 0.25E + 0.25V + 0.15A`

## Experimental coordination zoning

`src/coordination_zones.py` uses standardized latitude, longitude and final risk score with KMeans to create coordination groups. The labels are display/briefing aids only and do not alter any risk or relocation decision.

## Capacity and relocation

Effective capacity is the minimum known limiting resource. Available capacity subtracts current occupancy and is never negative. Single-habitation allocation can split population across safe shelters.

`src/batch_relocation.py` shares capacity across all priority habitations in deterministic priority order. `src/global_optimizer.py` adds an optional network-simplex comparison. It creates graph edges only to shelters that already pass the normal safety and capacity filters, and uses an explicit high-cost deficit path when capacity is insufficient.

## External context

- NDMA SACHET compatible CAP/RSS parser with LIVE/CACHED/DEMO separation.
- Optional USGS FDSN earthquake context with LIVE→CACHED behavior.
- Cached OSM GraphML routing where available, with labelled haversine fallback.

External feeds are contextual unless a source-specific integration explicitly maps them into the analytical contract.

## Data honesty

The bundled multi-city dataset uses real geography anchors for Puri, Guwahati and Chennai but synthetic operational catchment populations, shelter capacities/occupancies, hazard indicator scenarios and hazard polygons. All remain DEMO.

See `docs/multicity_demo_sources.md` for source context and limitations.
