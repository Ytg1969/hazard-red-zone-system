# Mobile and Offline Operation

Hazard Command is a Streamlit application, so a browser always needs access to a running Streamlit server. "Offline" therefore means **no internet/external API dependency**, not a fully static browser app that runs after the server disappears.

## Supported field setup

The recommended no-internet setup is:

1. Run the application on a laptop with Python and the project dependencies already installed.
2. Start explicit offline mode:

```bash
python scripts/run_offline.py
```

3. The launcher binds Streamlit to `0.0.0.0`, disables external live-source calls with `SIH_OFFLINE_MODE=true`, and prints both the laptop URL and the best available LAN URL.
4. Connect a phone/tablet to the same Wi-Fi network or to the laptop/phone hotspot.
5. Open the printed LAN address, normally `http://<laptop-ip>:8501`.

This can work with **no internet connection** as long as the phone and laptop can reach each other on the local network.

## What remains available offline

- bundled Puri, Guwahati and Chennai demonstration scenarios
- deterministic red-zone scoring
- explainable H/E/V/A risk contributions
- shelter safety and carrying-capacity constraints
- relocation ranking and allocation
- local/cached routing fallbacks where available
- Markdown/PDF action-plan export
- uploaded local operational datasets
- the bundled offline location index for Puri, Guwahati and Chennai

## What is intentionally unavailable offline

The application does not fabricate current observations. In explicit offline mode it will not request:

- Open-Meteo weather or air quality
- USGS earthquake feeds
- GDACS
- NASA EONET
- IMD network context
- NDMA SACHET network feeds
- Open-Meteo geocoding
- live OSRM routes
- remote operational feeds that are not already available locally/cached

Source diagnostics report `OFFLINE` instead of pretending those sources are current.

## Mobile UX behavior

The shared UI is designed to adapt at narrow widths:

- desktop columns stack into a single phone-friendly flow
- the sidebar behaves as a drawer and uses automatic initial state
- primary links and buttons use larger touch targets
- tabs become horizontally scrollable rather than wrapping into unreadable rows
- maps use a taller phone viewport
- tables/charts stay constrained to the viewport and can scroll where necessary
- decorative hero content is reduced on very small screens

## Preparing a demo laptop

Do this while internet is available, before the event:

```bash
python -m pip install -r requirements.txt
python -m pytest tests -q
python scripts/demo_gate.py
python scripts/production_gate.py
```

Then disconnect from the internet and run:

```bash
python scripts/run_offline.py
```

Verify Overview, Red Zone Map, Risk Analysis, Relocation Planner and PDF export from both the laptop and a phone on the same local network.

## Optional local operational data

For stronger offline demonstrations, keep validated habitation/shelter files on the laptop and load them through Operational Data. Do not enable strict operational mode until those files are complete and verified.

If a cached road graph is prepared, set `SIH_ROAD_GRAPHML` to its local path before launching. This provides a stronger routing option without internet; otherwise the routing chain may fall back to explicit straight-line distance.

## Safety boundary

Offline capability does not change the model's authority. The application remains decision support: evacuation and relocation orders are made by authorized disaster-management officials. Missing live information remains visibly missing rather than being estimated or presented as current.
