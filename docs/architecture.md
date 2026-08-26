# Architecture

SIH26191 uses one explainable pipeline:

`Data → GIS Exposure → Vulnerability → Risk → Carrying Capacity → Routing → Relocation → Streamlit Dashboard → Draft Action Plan`

## Principles

1. `main` must remain runnable.
2. Demo mode must work without internet.
3. Live, cached and demo data must be visibly distinguished.
4. Operational pages show plain-language decisions; technical details live in Methodology.
5. ML is optional validation only unless credible labelled historical data is available.
6. Preprocessed InSAR can be ingested later; raw SAR processing is outside the 7-day core.

## Dependency order

Data → GIS/Vulnerability → Risk → Capacity/Routing/Relocation → Dashboard.
