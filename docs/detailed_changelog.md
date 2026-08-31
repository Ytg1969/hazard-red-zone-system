# Detailed Changelog — Curated Multi-Hazard Demo

## Source review

This iteration reviewed the teammate ZIP and the accompanying comparison notes, then curated the useful concepts into the existing project instead of replacing the frozen risk/capacity contracts.

## Integrated

### Multi-hazard architecture
- Added Flood, Cyclone, Landslide, Earthquake and Drought prototype profiles.
- Added Combined Multi-Hazard scoring.
- Added explicit indicator normalization, weights, contributions and data-completeness reporting.
- Preserved the final explainable risk equation and thresholds.

### Realistic demonstration scope
- Replaced the presentation default with a nine-habitation, nine-shelter dataset across Puri, Guwahati and Chennai.
- Uses real geography anchors but synthetic operational values and synthetic hazard footprints.
- Added official hazard-context documentation and explicit non-ranking/data-honesty language.

### Coordination zoning
- Added KMeans Zone A/B/C grouping for EOC coordination.
- Kept zoning out of risk, priority, safety and evacuation decision logic.

### Relocation optimization
- Preserved the existing safe-shelter ranking and multi-shelter split.
- Strengthened system-wide allocation so shelter capacity cannot be double-booked.
- Added same-city constraints to prevent nonsensical cross-state demo allocation.
- Added an optional NetworkX network-simplex global comparison that can only use shelters already passing safety/capacity filters and retains an explicit deficit path.

### Data flexibility
- Added habitation and shelter CSV upload validation in Command Center.
- Added a downloadable minimum habitation template.
- Uploaded data remains user-supplied and is not automatically labelled LIVE.

### External context
- Preserved NDMA SACHET-compatible CAP/RSS infrastructure and LIVE/CACHED/DEMO states.
- Added optional official USGS FDSN earthquake context with disk-cache fallback.
- External feeds remain separate from final risk unless an explicit verified mapping is implemented.

### Presentation and documentation
- Multi-hazard controls added across Overview, Command Center, Map, Risk Analysis, Relocation Planner and Scenario Studio.
- Risk Analysis now shows hazard-indicator contributions as well as final risk contributions.
- Map shows multi-city synthetic hazard footprints and coordination zones.
- Relocation Planner exposes batch allocation and optional global-optimization comparison.
- Added/updated README, technical architecture, five-minute demo guide, pre-demo checklist, submission summary, methodology and jury FAQ.
- Existing PDF/Markdown action-plan export, Docker support and deployment guidance retained.

## Deliberately not copied as-is

### Alternate AHP/final risk model
Not adopted because it conflicts with the frozen explainable SIH risk contract and thresholds.

### Unsourced hazard claims
Prototype hazard indicator weights are included only with explicit labels. They are not presented as scientific standards or authoritative mappings.

### KMeans as an evacuation decision
Not adopted. Clusters are coordination aids only.

### Teammate optimizer without the existing safety gate
Not adopted as written. The useful global-allocation concept was reimplemented so only existing safety/capacity-valid candidates can receive flow.

### Synthetic values attached to real institutions
Not adopted. Generic demo shelter names are used whenever capacity/occupancy is synthetic.

### Fourth data mode / ambiguous custom-data labeling
Not adopted. The system keeps the frozen LIVE/CACHED/DEMO vocabulary; user uploads are explicitly described as user supplied.

## Verification added
- Tests for all hazard profiles and score bounds.
- Tests for missing-indicator re-normalization.
- Tests for all three demo geographies and DEMO labels.
- Tests preventing cross-city batch relocation.
- Tests for global optimizer capacity/city safeguards.
- Tests for USGS parsing without network access.
- Expanded `scripts/demo_gate.py` to verify multi-hazard, multi-city, capacity-safe relocation, global optimization and PDF/Markdown export.
