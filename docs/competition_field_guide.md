# Competition Field Guide

Use this page on the presentation laptop. The goal is to prove the **tested offline operator workflow** before the jury/demo begins.

## Before leaving for the event — internet available

```bash
git checkout main
git pull origin main
python -m pip install -r requirements.txt
python scripts/cache_road_network.py "Puri, Odisha, India"
python scripts/field_preflight.py --strict-road-cache
```

Expected result:

```text
Core offline workflow: PASS
Road-aware Puri routing: READY
Overall field gate: PASS
```

If the road cache cannot be prepared, the core app can still pass the normal preflight, but rehearse and explicitly describe the route as a **straight-line fallback**.

## Final offline rehearsal

Disconnect internet before the rehearsal.

```bash
python scripts/field_preflight.py --strict-road-cache
python scripts/run_offline.py
```

Open the printed laptop URL. Put the phone on the same Wi-Fi/hotspot and open the printed LAN URL.

Verify in this order:

1. **Overview** — show the incident-level KPIs and DEMO/source state.
2. **Red Zone Map** — select Puri, inspect a HIGH/CRITICAL habitation and show the local road route if cached.
3. **Risk Analysis** — show H/E/V/A contribution transparency and completeness.
4. **Relocation Planner** — show safe-site filtering, available capacity, recommendation and population split.
5. **Action plan** — download the PDF.
6. **Live Context** — show that external sources are explicitly OFFLINE rather than fabricated.
7. **Operational Data** — show that validated local files can still be loaded without internet.

## Claims to make

- The system is **decision support**, not an evacuation authority.
- Bundled operational scenario values are **DEMO** unless a verified operational source is explicitly active.
- Live/context feeds do **not** silently modify the deterministic risk score.
- Shelter safety and capacity are hard gates before relocation ranking/allocation.
- Offline mode disables current external sources instead of inventing data.
- Road provenance is stated explicitly: local GraphML / cached / live OSRM / straight-line fallback.

## Claims not to make

Do not describe:

- prototype hazard weights as official government standards;
- synthetic hazard polygons as statutory hazard boundaries;
- synthetic shelter capacities as real operational capacity;
- Puri/Guwahati/Chennai as a definitive national top-three disaster ranking;
- KMeans coordination zones as evacuation orders;
- straight-line fallback distance as a road route.

## If something fails on stage

- **Internet/live source fails:** continue offline; the core risk/relocation workflow is independent.
- **Road GraphML fails:** point out the labelled straight-line fallback; do not claim road-network routing.
- **Phone cannot connect:** keep the laptop demo running and switch to the backup hotspot/network.
- **Operational upload fails validation:** return to the bundled DEMO workflow; do not fill missing fields manually during the demo.
- **Primary laptop fails:** use the backup laptop on the same tested commit and repeat the preflight.

## Files to copy to both laptops

- final repository at the tested commit
- Python environment / installed dependencies
- `data/cache/roads/Puri_Odisha_India.graphml` if road-aware offline routing will be shown
- any validated local operational datasets intended for the demo
- backup screen recording
- this field guide and `docs/pre_demo_checklist.md`
