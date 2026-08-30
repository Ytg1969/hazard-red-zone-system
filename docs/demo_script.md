# SIH Demo Script

## Before judging

1. Pull the final tested `main` commit on both primary and backup laptops.
2. Activate the same Python/Conda environment on both machines.
3. Run the offline gate:

   ```bash
   python scripts/demo_gate.py
   ```

   It must report `"demo_ready": true`.

4. Run the full automated suite:

   ```bash
   python -m pytest tests -q
   ```

5. Run `streamlit run app.py` and open every page once.
6. Disconnect internet and repeat the core workflow using `data/demo/`.
7. If road routing is part of the final demo, pre-cache Puri:

   ```bash
   python scripts/cache_road_network.py "Puri, Odisha, India"
   ```

   Then configure the GraphML path on the demo machine, for example in PowerShell:

   ```powershell
   $env:SIH_ROAD_GRAPHML="data/cache/roads/Puri_Odisha_India.graphml"
   ```

8. Verify the UI still clearly says DEMO unless a source has actually been connected and verified.
9. Keep a short screen recording of the successful core demo as a last-resort backup.

## Opening line

> Our system combines GIS-based hazard exposure, population vulnerability, evacuation difficulty, shelter capacity and routing to identify red zones and generate explainable, capacity-aware relocation recommendations for disaster authorities.

## Three-minute core path

### 1. Operational Overview — 30 sec

- State the problem: authorities need to know who is at risk, who moves first, where they should move and whether the destination can support them.
- Point to Data Mode.
- Show Habitations Monitored, Critical Red Zones, Population at Risk and Available Shelter Capacity.

### 2. Red Zone Map — 35 sec

- Open Red Zone Map.
- Explain that the bundled hazard polygons are synthetic DEMO layers used to prove the GIS pipeline offline.
- Select the highest-risk habitation.
- Show risk class, population and whether the habitation intersects or lies close to the demonstration hazard footprint.

### 3. Risk Analysis — 35 sec

- Open the same habitation.
- Show the 0–100 risk score.
- Explain the weighted contributions: hazard, exposure, vulnerability and evacuation difficulty.
- Emphasize that administrators can inspect why the location received its class.

### 4. Relocation Planner — 50 sec

- Select the same habitation.
- Show that unsafe or full shelters are filtered out.
- Compare safety, capacity adequacy, accessibility and travel distance.
- Show the primary shelter recommendation.
- Show multi-shelter allocation and any remaining deficit.
- Point out routing mode: cached road network when configured, otherwise clearly labelled haversine fallback.

### 5. Close — 30 sec

- Explain that the system goes beyond GIS visualization by converting layers into risk priority, explanations and capacity-aware relocation recommendations.
- Mention LIVE/CACHED/DEMO source handling and offline resilience.
- State that it is decision support, not an autonomous evacuation order.

Target core duration: **about 3 minutes**.

## Full differentiator path — approximately 4.5 minutes

Add these between Risk Analysis and Relocation Planner:

### Scenario Studio — 30 sec

- Choose a preset or adjust one weight.
- Show automatic weight normalization.
- Show how classification and affected population change under the scenario.

After Relocation Planner:

### Draft Action Plan — 20 sec

- Download/preview the draft Markdown action plan.
- Point out data mode, risk, primary shelter, capacity allocation and disclaimer.

## Differentiator line

> A normal GIS dashboard shows layers. Our system converts those layers into explainable risk priorities, capacity-constrained shelter allocation and a draft relocation action plan.

## Final rehearsal gate

- If the core path is above 3.5 minutes, shorten narration.
- Do not remove Operational Overview, Red Zone Map, Risk Analysis or Relocation Planner from the core path.
- Scenario Studio and export can be trimmed if the judging slot is shorter.
- Repeat the full flow once with Wi-Fi disabled.

## Failure handling during the pitch

- **Live API unavailable:** continue in CACHED or DEMO mode and say so explicitly.
- **Road graph unavailable:** continue with haversine fallback and show the routing-mode label.
- **Map tile internet issue:** core risk/capacity tables still work; do not stop the demo.
- **Primary laptop failure:** switch to the pre-tested backup laptop.
- **Unexpected app issue:** use the backup recording, then continue with architecture and impact explanation.
