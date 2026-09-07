# Deployment Guide

This project is a Streamlit decision-support prototype. The recommended judging/demo path remains the offline `DEMO` dataset on `main`.

## Local Windows demo

```powershell
cd C:\Users\<user>\Project\hazard-red-zone-system
git checkout main
git pull origin main
py -3.12 scripts/demo_gate.py
py -3.12 -m pytest tests -q
py -3.12 -m streamlit run app.py
```

The demo gate should report `"demo_ready": true` before presentation.

Python 3.12 is the shared CI, offline-bundle and supported local baseline.

## Conda environment

```bash
conda env create -f environment.yml
conda activate hazard-red-zone
streamlit run app.py
```

## Pip environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

## Docker

Build:

```bash
docker build -t hazard-red-zone .
```

Run:

```bash
docker run --rm -p 8501:8501 hazard-red-zone
```

Then open `http://localhost:8501`.

## Cached road routing

Before an offline presentation, optionally cache the pilot road graph:

```bash
python scripts/cache_road_network.py "Puri, Odisha, India"
```

On PowerShell, point the app at the resulting file:

```powershell
$env:SIH_ROAD_GRAPHML="data/cache/roads/Puri_Odisha_India.graphml"
```

If a cache is not available, the application continues with a clearly labelled straight-line/haversine fallback.

## Optional NDMA SACHET alert feed

Live Data Context and System Readiness can display NDMA SACHET CAP/RSS alert context without coupling it to risk scoring. The connector remains deliberately unconfigured by default so offline startup never depends on the network.

The WMO Register of Alerting Authorities lists the National Disaster Management Authority of India CAP feed as:

`https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml`

To enable that verified public feed for a deployment, set:

```powershell
$env:SIH_SACHET_FEED_URL="https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml"
```

Source verification references:

- WMO Register of Alerting Authorities, India / NDMA record: `https://alertingauthority.wmo.int/authorities.php?recId=331`
- NDMA SACHET RSS page: `https://sachet.ndma.gov.in/CapFeed`
- NDMA agency integration guide: `https://sachet.ndma.gov.in/docs/Integration_Guide_For_Agencies.pdf`

The RSS URL above is the discovery/current-alert feed. NDMA's separate per-alert CAP XML endpoint uses an `identifier` parameter; do not invent identifiers or derive them from unrelated IDs. NDMA's integration guide requires consumers of that CAP XML endpoint to cache the XML + ETag, send `If-None-Match` on subsequent requests, use the cached XML on HTTP 304, and replace the cache/ETag on HTTP 200.

The panel uses the normal source modes:

- `LIVE` when a configured source is fetched successfully;
- `CACHED` when a previously cached response is reused after refresh failure or HTTP cache revalidation;
- `DEMO`/explicit unavailable state when no verified feed is configured or no usable cache exists.

Do not set an unverified URL merely to obtain a LIVE badge. Failure to reach the feed must never be interpreted as "no alerts" or "all clear."

## Operational deployment notes

A real government deployment would require controls that are outside this hackathon prototype, including authenticated access, role-based permissions, audit logging, secure storage, backup/recovery, formal source validation and incident-management procedures.

The application does not issue evacuation orders. Final evacuation, routing and shelter decisions remain with authorized officials and must use current field verification.
