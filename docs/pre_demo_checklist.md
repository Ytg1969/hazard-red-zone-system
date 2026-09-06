# Pre-Demo Checklist

## Release and laptop gate
- [ ] `git checkout main && git pull origin main`
- [ ] `python -m pip install -r requirements.txt`
- [ ] `python scripts/field_preflight.py` reports `Core offline workflow: PASS`
- [ ] Record the tested Git commit printed by the preflight
- [ ] Working tree is clean, or every intentional local file is documented
- [ ] TCP port 8501 is available (or `SIH_OFFLINE_PORT` is set to an available port)

## Road-aware offline routing
- [ ] While internet is available, run `python scripts/cache_road_network.py "Puri, Odisha, India"`
- [ ] Confirm `data/cache/roads/Puri_Odisha_India.graphml` exists on the presentation laptop
- [ ] Run `python scripts/field_preflight.py --strict-road-cache` and confirm PASS
- [ ] If road cache is intentionally absent, rehearse the visibly labelled straight-line fallback instead of claiming road-aware routing

## Multi-hazard walkthrough
- [ ] Combined Multi-Hazard loads
- [ ] Flood profile loads
- [ ] Cyclone profile loads
- [ ] Landslide profile loads
- [ ] Earthquake profile loads
- [ ] Drought profile loads
- [ ] Hazard data completeness is visible
- [ ] Risk contribution chart is visible and totals match the frozen risk equation

## Three-city demo
- [ ] Puri scenario loads
- [ ] Guwahati scenario loads
- [ ] Chennai scenario loads
- [ ] All Demo Cities overview loads
- [ ] Map shows synthetic hazard footprints and DEMO label
- [ ] Explain verbally that cities are real geography anchors while operational values/footprints are DEMO scenario inputs

## Relocation
- [ ] Unsafe/full shelters are excluded
- [ ] Multi-shelter population split works
- [ ] Deficit is explicit if capacity is insufficient
- [ ] Batch allocation does not double-book capacity
- [ ] Multi-city batch allocation never crosses demo-city boundaries
- [ ] PDF and Markdown action plans download
- [ ] Route provenance is visible as local GraphML, cached route or labelled fallback

## Offline phone rehearsal
- [ ] Disconnect the laptop from the internet
- [ ] Run `python scripts/field_preflight.py --strict-road-cache`
- [ ] Run `python scripts/run_offline.py`
- [ ] Laptop opens the printed `127.0.0.1` URL
- [ ] Phone joins the same Wi-Fi/hotspot and opens the printed LAN URL
- [ ] Overview works on phone
- [ ] Red Zone Map works without internet basemap tiles
- [ ] Risk Analysis works on phone
- [ ] Relocation Planner works on phone
- [ ] Live Context shows explicit OFFLINE source state
- [ ] Operational Data still permits local file recovery/uploads

## External context when internet is available
- [ ] SACHET panel gracefully uses LIVE/CACHED/DEMO behavior
- [ ] No unverified endpoint is labelled LIVE
- [ ] Optional external-source failure does not break the core app
- [ ] Live Context is presented as corroborating evidence, not as an automatic risk-score input

## Operational resilience
- [ ] Primary and backup laptops both run the same final tested commit
- [ ] Puri road GraphML exists on both laptops if road-aware offline routing will be shown
- [ ] Local operational files needed for the demonstration exist on both laptops
- [ ] Backup hotspot plan has been tested
- [ ] Backup screen recording exists
- [ ] Chargers/power bank and required display adapters are packed

## Jury-safe claims
- [ ] Do not call prototype multi-hazard weights official standards
- [ ] Do not call demo hazard polygons authoritative maps
- [ ] Do not call synthetic shelter capacities real capacities
- [ ] Do not call Puri/Guwahati/Chennai a definitive national top-3 ranking
- [ ] State that KMeans zones are coordination aids, not evacuation orders
- [ ] State that global optimization only compares safe/capacity-valid candidates
- [ ] State that offline mode disables current external observations rather than fabricating them
