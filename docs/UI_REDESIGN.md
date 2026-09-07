# Hazard Command 2.0 UI redesign

## Product goal
Turn the Streamlit prototype into a judge-ready emergency operations workspace. The interface should answer four questions quickly: **where is danger, who is affected, where can people move safely, and what evidence supports the recommendation?**

## Primary operator flow
1. **Command** — active scope, incident severity, people at risk, immediate relocation demand, safe capacity and top priority.
2. **Map** — spatial hazard picture, selected habitation, qualified shelters and route provenance.
3. **Risk** — explain the deterministic score and its evidence without changing the frozen model.
4. **Relocate** — capacity-constrained shelter allocation and route review.
5. **Context / briefing** — source-labelled live context and exportable administrative evidence.

## Interaction principles
- One active geography/hazard context per page.
- Show decisions first; put source diagnostics and methodology behind secondary disclosure.
- Prefer progressive disclosure over long explanatory pages.
- Preserve LIVE/CACHED/DEMO provenance near the data it qualifies.
- Keep unknown values unknown.
- Never turn uncalibrated live observations into analytical risk.
- Never overbook shelter capacity.
- Never present an automated evacuation order.
- Offline mode must remain a first-class usable path.

## Visual direction
Dark operational command interface with restrained blue/teal system accents and risk colour reserved for severity. Large map surfaces, compact KPI strips, clear action hierarchy, minimal prose, mobile-friendly controls, and consistent empty/loading/error states.

## Legacy-page policy
Existing technical pages remain available while the redesign is validated, but they are treated as evidence/system tooling rather than the primary judge/operator workflow. Removal or consolidation happens only after page smoke tests and navigation contracts are updated together.
