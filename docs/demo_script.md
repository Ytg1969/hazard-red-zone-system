# SIH Demo Script

## Before judging

1. Pull the final tested commit on both primary and backup laptops.
2. Activate the same Python/Conda environment on both machines.
3. Run the one-command offline gate:

   ```bash
   python scripts/demo_gate.py
   ```

   The command must report `"demo_ready": true`.

4. Run the full automated suite:

   ```bash
   python -m pytest tests -q
   ```

5. Run `streamlit run app.py` once and open every page.
6. Disconnect internet and repeat the core workflow using `data/demo/`.
7. If road routing is part of the final demo, pre-cache Puri:

   ```bash
   python scripts/cache_road_network.py "Puri, Odisha, India"
   ```

   Then configure the GraphML path on the demo machine, for example in PowerShell:

   ```powershell
   $env:SIH_ROAD_GRAPHML="data/cache/roads/Puri_Odisha_India.graphml"
   ```

8. Verify the UI clearly says DEMO unless a source has actually been verified and loaded as CACHED/LIVE.
9. Keep a 2–3 minute screen recording of the successful core demo as a last-resort backup.

## Opening line

> Our system combines GIS-based hazard exposure, population vulnerability, evacuation difficulty, shelter capacity and routing to identify red zones and generate explainable, capacity-aware relocation recommendations for disaster authorities.

## Three-minute core path

### 1. Operational Overview — 30 sec

- State the problem: authorities need to know who is at risk, who moves first, where they should move and whether the destination can support them.
- Point to the visible Data Mode label.
- Show Habitations Monitored, Critical Red Zones, Population at Risk and Available Shelter Capacity.

### 2. Red Zone Map — 35 sec

- Open Red Zone Map.
- Explain that the bundled hazard polygons are synthetic DEMO layers used to prove the complete GIS pipeline offline.
- Select the highest-risk habitation.
- Show risk class, population and intersection/proximity with the demonstration hazard footprint.

### 3. Risk Analysis — 35 sec

- Open the same habitation.
- Show the 0–100 risk score.
- Explain the weighted contributions: hazard, exposure, vulnerability and evacuation difficulty.
- Emphasize that the risk classification is explainable rather than a black-box label.

### 4. Relocation Planner — 50 sec

- Select the same habitation.
- Show that unsafe or full shelters are filtered out.
- Compare safety, capacity adequacy, accessibility and travel distance.
- Show the primary shelter recommendation.
- Show multi-shelter allocation and any remaining capacity deficit.
- Point out routing mode: cached road network when available, otherwise clearly labelled haversine fallback.

### 5. Close — 30 sec

- Explain that the system goes beyond GIS visualization by converting hazard layers into priorities, explanations and capacity-aware relocation recommendations.
- Mention LIVE/CACHED/DEMO handling and offline resilience.
- State that it is decision support for district/EOC authorities, not an autonomous evacuation-order system.

Target core duration: **about 3 minutes**.

## Full differentiator path — approximately 4.5 minutes

Add these between Risk Analysis and Relocation Planner:

### Scenario Studio — 30 sec

- Choose a preset or adjust one weight.
- Show automatic weight normalization.
- Show how classification and affected population change under the scenario.

After Relocation Planner:

### Draft Action Plan — 20 sec

- Download/preview the draft administrative action plan.
- Point out risk, recommended shelter, capacity allocation, source/data mode and disclaimer.

### Odisha Pilot Status — 25 sec, Phase-2 branch only

- Open Odisha Pilot Status.
- Show the authoritative source register for Census/OSDMA.
- Explain that real Puri data is behind a strict readiness gate: missing elderly population, coordinates, shelter operational values or hazard geometry are never fabricated.
- This is the transition from the working offline prototype to an authoritative district pilot.

## Jury differentiator line

> A normal GIS dashboard shows layers. Our system converts those layers into explainable risk priorities, capacity-constrained shelter allocation and a draft relocation action plan.

## Final rehearsal gate

Run the complete demo with a stopwatch.

- If the core path is above 3.5 minutes, shorten narration.
- Do not remove Operational Overview, Red Zone Map, Risk Analysis or Relocation Planner from the core path.
- Scenario Studio, Pilot Status and export can be trimmed if the judging slot is shorter.
- Repeat the full flow once with Wi-Fi disabled.

## Failure handling during the pitch

- **Live API unavailable:** continue in CACHED or DEMO mode and say so explicitly.
- **Road graph unavailable:** continue with haversine fallback and show the routing-mode label.
- **Map tile internet issue:** core risk/capacity tables still work; do not stop the demo.
- **Authoritative Puri bundle incomplete:** show the Pilot Status readiness gate, then continue using the clearly labelled offline DEMO path.
- **Primary laptop failure:** switch to the pre-tested backup laptop.
- **Unexpected app issue:** use the backup recording, then continue with architecture and impact explanation.
