# Puri Pilot — Demographic Mapping Notes

## Verified Census source

Use the Census of India 2011 Primary Census Abstract at town, village and ward level for Odisha, District Puri (reference `PC11_PCA-TV-2118`). The official catalogue exposes a downloadable workbook named `DDW_PCA2118_2011_MDDS with UI.xlsx` and identifies the data source as Population Census 2011.

Source catalogue: https://censusindia.gov.in/nada/index.php/catalog/6578

## Fields directly supported by the Puri PCA

The official catalogue lists village-level fields including:

- total population
- male population
- female population
- population age 0-6 years
- male population age 0-6 years
- female population age 0-6 years
- scheduled caste population
- scheduled tribe population
- literate / illiterate counts
- worker categories

For the frozen project schema, `children_population` may be populated from the source's `Population 0-6 years old` field, provided the UI/methodology explicitly describes the child proxy as **age 0-6 from Census 2011** rather than implying all minors/children.

## Elderly population gap

The Puri PCA catalogue does not list a village-level elderly/senior-citizen field. Therefore:

- do not derive `elderly_population` by subtraction;
- do not assign a state/district percentage silently to every village;
- do not set the value to zero when unavailable;
- keep the field unavailable until a defensible village-level source or an explicitly documented derived method is approved.

A district-level age-distribution table may be useful for context, but applying a district ratio to village populations would be a modelled estimate, not a directly observed village count. If such a method is later adopted it must be labelled as derived, documented and sensitivity-tested.

## Recommended ingestion mapping

| Project field | Puri PCA basis | Status |
| --- | --- | --- |
| `habitation_id` | Census village/location code | Direct |
| `name` | Area / village name | Direct |
| `population` | Population - Total | Direct |
| `children_population` | Population 0-6 years old | Direct historical proxy |
| `elderly_population` | Not listed in PCA village fields | Pending |
| `latitude` / `longitude` | Not assumed from PCA demographic table | Separate verified join |
| `population_reference_year` | 2011 | Direct metadata |
| `data_mode` | `CACHED` for bundled authoritative snapshot | Project metadata |

## Data-honesty rule

Census 2011 is authoritative historical data. It must never be presented as current population. The dashboard should show both source year and data mode.

`LIVE`/`CACHED` describe retrieval/availability mode; they do not imply demographic recency.
