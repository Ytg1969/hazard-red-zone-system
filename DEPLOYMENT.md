# Deployment Guide

This project is a Streamlit decision-support prototype. The recommended judging/demo path remains the offline `DEMO` dataset on `main`.

## Local Windows demo

```powershell
cd C:\Users\<user>\Project\hazard-red-zone-system
git checkout main
git pull origin main
py -3.13 scripts/demo_gate.py
py -3.13 -m pytest tests -q
py -3.13 -m streamlit run app.py
```

The demo gate should report `"demo_ready": true` before presentation.

## Conda environment

```bash
conda env create -f environment.yml
conda activate hazard-red-zone
streamlit run app.py
```

Python 3.12 is the shared/CI baseline.

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

## Optional external alert feed

The Command Center can display a CAP/RSS alert feed without coupling it to risk scoring. The connector is deliberately unconfigured by default.

After verifying an official public endpoint, set:

```powershell
$env:SIH_SACHET_FEED_URL="<verified CAP/RSS feed URL>"
```

The panel uses the normal source modes:

- `LIVE` when a configured source is fetched successfully;
- `CACHED` when a previously cached response is used after a refresh failure;
- `DEMO` when no verified feed is configured or no cache exists.

Do not set an unverified URL merely to obtain a LIVE badge.

## Operational deployment notes

A real government deployment would require controls that are outside this hackathon prototype, including authenticated access, role-based permissions, audit logging, secure storage, backup/recovery, formal source validation and incident-management procedures.

The application does not issue evacuation orders. Final evacuation, routing and shelter decisions remain with authorized officials and must use current field verification.
