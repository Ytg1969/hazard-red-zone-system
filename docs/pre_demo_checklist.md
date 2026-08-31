# Pre-Demo Checklist

## Code and environment
- [ ] `git checkout main && git pull origin main`
- [ ] `py -3.13 -m pip install -r requirements.txt`
- [ ] `py -3.13 scripts/demo_gate.py` reports `demo_ready: true`
- [ ] `py -3.13 -m pytest tests -q` passes
- [ ] `py -3.13 -m streamlit run app.py` launches without traceback

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

## External context
- [ ] SACHET panel gracefully uses LIVE/CACHED/DEMO behavior
- [ ] No unverified endpoint is labelled LIVE
- [ ] Optional USGS earthquake context failure does not break the core app

## Operational resilience
- [ ] Disconnect internet and repeat the core demo
- [ ] Cached road graph is configured if road-aware routing is being shown
- [ ] Haversine fallback is visibly labelled when road cache is absent
- [ ] Primary and backup laptops both run the final tested commit
- [ ] Backup screen recording exists

## Jury-safe claims
- [ ] Do not call prototype multi-hazard weights official standards
- [ ] Do not call demo hazard polygons authoritative maps
- [ ] Do not call synthetic shelter capacities real capacities
- [ ] Do not call Puri/Guwahati/Chennai a definitive national top-3 ranking
- [ ] State that KMeans zones are coordination aids, not evacuation orders
- [ ] State that global optimization only compares safe/capacity-valid candidates
