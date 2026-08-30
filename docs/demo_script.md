# SIH Demo Script

## Before judging

1. Pull the final tested commit on both primary and backup laptops.
2. Activate the same Python/Conda environment on both machines.
3. Run `python -m pytest tests`.
4. Run `streamlit run app.py` once and open every page.
5. Disconnect internet and repeat the core workflow using `data/demo/`.
6. If road routing is part of the final demo, pre-cache the selected district:

   ```bash
   python scripts/cache_road_network.py "Cuttack, Odisha, India"
   ```

   Then configure the GraphML path on the demo machine, for example in PowerShell:

   ```powershell
   $env:SIH_ROAD_GRAPHML="data/cache/roads/Cuttack_Odisha_India.graphml"
   ```

7. Verify the UI still clearly says DEMONSTRATION DATA unless a live adapter has actually been connected and verified.
8. Keep a 2–3 minute screen recording of the successful core demo as a last-resort backup.

## Three-minute core path

### 1. Operational Overview — 30 sec

- State the problem in one sentence: authorities need to know who is at risk, who moves first, where they should move and whether the destination can support them.
- Point to Data Mode.
- Show Habitations Monitored, Critical Red Zones, Population at Risk and Available Shelter Capacity.

### 2. Red Zone Map — 35 sec

- Open Red Zone Map.
- Explain that the bundled hazard polygons are synthetic DEMO layers used to prove the GIS pipeline offline.
- Select the highest-risk habitation.
- Show risk class, population and whether the habitation intersects the demonstration hazard footprint.

### 3. Risk Analysis — 35 sec

- Open the same habitation.
- Show the 0–100 risk score.
- Explain weighted contributions in plain language.
- State that the model is explainable and administrators can inspect the drivers.

### 4. Relocation Planner — 50 sec

- Select the same habitation.
- Show that unsafe/full shelters are filtered.
- Compare suitability, safety, distance and capacity.
- Show primary shelter recommendation.
- Show multi-shelter allocation and any remaining deficit.
- Point out the routing mode: cached road network if configured, otherwise clearly-labelled haversine fallback.

### 5. Close — 30 sec

- Explain that the tool adds decisions on top of GIS visualization: risk, capacity and phased relocation.
- Mention LIVE/CACHED/DEMO source handling, offline resilience and the ability to integrate official state/national data.
- State that it is decision support, not an autonomous evacuation order.

Target core duration: **about 3 minutes**.

## Full differentiator path — approximately 4.5 minutes

Add these between Risk Analysis and Relocation Planner:

### Scenario Studio — 30 sec

- Choose Hazard Priority or adjust one slider.
- Show automatic weight normalization.
- Show how many locations changed class and the population affected.

After Relocation Planner:

### Draft Action Plan — 20 sec

- Download/preview the Markdown action plan.
- Point out source/data mode, risk, primary shelter, capacity allocation and disclaimer.

## Day 6.5 rehearsal gate

Run the complete demo with a stopwatch.

- If the core path is above 3.5 minutes, shorten narration before Day 7.
- Do not remove the Overview, Red Zone Map, Risk Analysis or Relocation Planner from the core path.
- Scenario Studio and export can be trimmed live if the judging slot is shorter than expected.

## Failure handling during the pitch

- **Live API unavailable:** switch to cached or DEMO mode and say so explicitly.
- **Road graph unavailable:** continue with haversine fallback and show the routing-mode label.
- **Map tile internet issue:** core risk/capacity tables still work; do not stop the demo.
- **Primary laptop failure:** switch to the pre-tested backup laptop.
- **Unexpected app issue:** use the backup recording, then continue with architecture and impact explanation.
