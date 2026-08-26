# Data Sources

This file is the provenance register. Replace placeholders with the exact datasets actually frozen for the demo.

| Category | Preferred source | Freshness | Planned use |
|---|---|---|---|
| Weather / warnings | IMD APIs | Live / forecast | Rainfall, nowcast, district warning inputs |
| Multi-hazard alerts | NDMA SACHET | Near real time | Alert context and active warning display |
| Flood forecasting | Central Water Commission | Live / advisory | River and flood escalation context |
| Satellite / hazard layers | NRSC Bhuvan | Varies by product | Hazard base layers and disaster products |
| Landslide | Geological Survey of India | Baseline / warning products | Susceptibility, inventory, regional warning context |
| Population | Census of India PCA | Static official baseline | Population and demographic vulnerability |
| Administrative IDs | Local Government Directory | Maintained directory | Current state/district/village code reconciliation |
| Shelter inventory | State SDMA / district administration | Periodic | Real shelter locations and facilities |
| Roads | OpenStreetMap | Continuously edited | Cached OSMnx/NetworkX route graph |

For every frozen dataset record: dataset name, exact source URL, license/terms, date, spatial resolution, update timestamp, geographic coverage, and whether the app treats it as LIVE, CACHED, or DEMO.
