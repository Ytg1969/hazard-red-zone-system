# Mobile and Offline Operation

Hazard Command is a Streamlit application, so a browser always needs access to a running Streamlit server. "Offline" means **no internet/external API dependency while the local server is running**, not a static browser app that keeps working after the server stops.

## Recommended field setup

1. Prepare the laptop while internet is available.
2. Run the competition preflight:

```bash
python scripts/field_preflight.py
```

3. Start explicit offline/LAN mode:

```bash
python scripts/run_offline.py
```

4. The launcher binds Streamlit to `0.0.0.0`, sets `SIH_OFFLINE_MODE=true`, and prints the laptop URL plus the best available LAN URL.
5. Connect the phone/tablet to the same Wi-Fi or hotspot and open the printed `http://<laptop-ip>:8501` address.

This works without internet as long as the phone and laptop can reach each other on the local network.

## What the preflight verifies

`python scripts/field_preflight.py` runs without requiring live APIs and checks:

- required runtime modules and field files
- deterministic multi-hazard demo gate
- offline production gate
- PDF action-plan generation through the demo gate
- availability of the configured Streamlit port
- current Git commit / dirty working-tree state when Git metadata is available
- presence of cached Puri/Guwahati/Chennai GraphML road networks
- laptop and LAN launch addresses

A missing Puri road cache is a **warning by default** because the application has a labelled straight-line fallback. To require road-aware Puri routing before presentation, run:

```bash
python scripts/field_preflight.py --strict-road-cache
```

## Preparing road-aware offline routing

OSMnx is included in both the Conda environment and `requirements.txt`. Road GraphML files are intentionally not committed because they can be large.

While internet is available, cache Puri before the event:

```bash
python scripts/cache_road_network.py "Puri, Odisha, India"
```

This creates:

```text
data/cache/roads/Puri_Odisha_India.graphml
```

To cache all three bundled demo cities:

```bash
python scripts/cache_road_network.py --demo-cities
```

The Red Zone Map automatically looks for the bundled demo-city filenames. For a custom operational deployment, set `SIH_ROAD_GRAPHML` to the local GraphML file before launch.

## What remains available offline

- bundled Puri, Guwahati and Chennai demonstration scenarios
- deterministic red-zone scoring
- explainable H/E/V/A risk contributions
- shelter safety and carrying-capacity constraints
- relocation ranking and allocation
- local GraphML routing when cached
- visibly labelled straight-line routing fallback when no graph is available
- Markdown/PDF action-plan export
- uploaded local operational datasets
- offline reference locations for Puri, Guwahati and Chennai
- vector red-zone/shelter/event geometry without internet basemap tiles

## What is intentionally unavailable offline

The application does not fabricate current observations. In explicit offline mode it does not request:

- Open-Meteo weather or air quality
- USGS earthquake feeds
- GDACS
- NASA EONET
- IMD network context
- NDMA SACHET network feeds
- Open-Meteo geocoding
- live OSRM routes
- OpenStreetMap/Bhuvan map tiles
- configured remote habitation/shelter/hazard feeds

Source diagnostics report `OFFLINE` instead of pretending those sources are current.

## Mobile UX behavior

- desktop columns stack into a phone-friendly flow
- the sidebar behaves as a drawer
- primary links and buttons use larger touch targets
- tabs/secondary evidence are collapsed or scrollable instead of dominating narrow screens
- maps use a taller phone viewport
- tables/charts stay constrained to the viewport
- offline state remains visible outside the sidebar

## Final event-day sequence

While still online:

```bash
python -m pip install -r requirements.txt
python scripts/cache_road_network.py "Puri, Odisha, India"
python scripts/field_preflight.py --strict-road-cache
```

Then disconnect internet and repeat:

```bash
python scripts/field_preflight.py --strict-road-cache
python scripts/run_offline.py
```

Verify Overview, Red Zone Map, Risk Analysis, Relocation Planner and PDF export from the laptop and from a phone on the same local network.

## Safety boundary

Offline capability does not change the model's authority. The application remains decision support: evacuation and relocation orders are made by authorized disaster-management officials. Missing live information remains visibly missing rather than being estimated or presented as current.
