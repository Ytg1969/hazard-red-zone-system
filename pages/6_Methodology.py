import streamlit as st

from src.ui_theme import inject_global_css, render_disclaimer, render_page_header

st.set_page_config(page_title="Methodology", layout="wide")
inject_global_css()
render_page_header(
    "Methodology",
    "Technical reference for risk scoring, carrying capacity, relocation ranking, routing and data limitations.",
)

st.markdown(
    """
### 1. Explainable risk model

The prototype uses a transparent weighted score:

`Risk = 0.35 × Hazard + 0.25 × Exposure + 0.25 × Vulnerability + 0.15 × Evacuation Difficulty`

All four inputs are normalized to **0–100** before weighting. Higher evacuation-difficulty values increase risk.

| Risk score | Classification |
|---:|---|
| 0–29 | LOW |
| 30–49 | MODERATE |
| 50–69 | HIGH |
| 70–100 | CRITICAL |

The Scenario Studio permits alternative emphasis, but weights are automatically normalized so that they always sum to 1.00.

### 2. Vulnerability

The current demonstration vulnerability score uses the share of children and elderly people in the habitation population. This is intentionally simple and explainable. Production deployments can add disability, health access, housing quality, poverty and other approved vulnerability indicators when reliable data is available.

### 3. Carrying capacity

Shelter capacity is not treated as a single building-capacity number. The system evaluates known limiting resources:

`effective_capacity = min(total_capacity, known water capacity, known sanitation capacity, known access capacity)`

- **VALIDATED** — all defined resource capacities are available.
- **PARTIAL** — some resource capacities are known; the minimum known constraint is used.
- **UNVALIDATED** — no resource sub-capacity is available; total physical capacity is used as a fallback.

`available_capacity = max(0, effective_capacity − current_occupancy)`

### 4. Relocation ranking

Unsafe or full shelters are removed before ranking. Remaining candidates are scored with transparent default weights:

- Safety: **35%**
- Capacity adequacy: **25%**
- Accessibility: **20%**
- Distance desirability: **20%**

If one shelter cannot accommodate the full habitation population, the allocation routine distributes people across ranked shelters without exceeding available capacity and reports any remaining deficit.

### 5. Routing

The current offline-safe baseline uses great-circle (haversine) distance and clearly labels it as `haversine_fallback`. The production/demo differentiator is cached OpenStreetMap road routing using OSMnx and NetworkX. Road graphs should be downloaded before judging so venue internet is not required.

### 6. Data modes

Every operational dataset or live adapter must expose one of three data modes:

- **LIVE** — fetched from a verified current source.
- **CACHED** — previously fetched live data reused because the live source is unavailable or intentionally disabled.
- **DEMO** — synthetic or demonstration data used to prove system behavior.

Demo and cached information must never be presented as live observations.

### 7. Optional machine learning

Machine learning is a validation/stretch layer, not a dependency of the core system. No model accuracy should be presented unless the team has credible historical labels, a defensible train/test split and checks against data leakage.

### 8. InSAR and satellite deformation

The seven-day core does **not** perform raw Sentinel-1 InSAR processing. The architecture can ingest preprocessed displacement/deformation layers as an additional hazard input in a later phase.

### 9. Limitations

- The prototype supports administrative decision making; it does not issue statutory evacuation orders.
- Demonstration risk weights are configurable assumptions, not universal disaster-management standards.
- Shelter occupancy and infrastructure capacity are only as current as their source timestamps.
- Road conditions can change during an emergency and must be revalidated before dispatch.
- Current demonstration hazard exposure is not a substitute for an authoritative hazard product.
"""
)

render_disclaimer()
