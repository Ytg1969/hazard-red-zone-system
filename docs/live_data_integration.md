# Live Data Integration Runbook

The core application must remain fully usable in DEMO mode. Live sources are added only after their access method, schema, terms and freshness behavior are verified.

## Data-mode rule

Every adapter returns a `DataEnvelope` with one of:

- `LIVE` — current response fetched successfully;
- `CACHED` — a previously successful response reused because the source is unavailable or intentionally offline;
- `DEMO` — synthetic/static demonstration content.

Never relabel CACHED or DEMO as LIVE.

## Generic JSON adapter

`src.live_data.fetch_json_with_cache()` provides the shared behavior:

```python
from src.live_data import fetch_json_with_cache

envelope = fetch_json_with_cache(
    source="Verified Source Name",
    url="https://verified-endpoint.example/data",
    cache_path="data/cache/source/latest.json",
)
```

On failure, the adapter uses the disk cache if one exists. If neither live nor cached data exists, the caller must explicitly choose a static/demo fallback.

## Source-specific adapter checklist

Before adding an IMD, NDMA SACHET, CWC or state-agency adapter:

1. Record the exact official source URL.
2. Confirm whether access requires registration, an API key, query parameters or a manual download.
3. Save one representative raw response under a non-sensitive local test fixture if terms allow it.
4. Document field mappings into the project's frozen contracts.
5. Parse timestamps and preserve the source timestamp separately from the app fetch time.
6. Define a staleness threshold appropriate to the product.
7. Add a cache path under `data/cache/`.
8. Add tests that do not depend on internet connectivity.
9. Display LIVE/CACHED/DEMO plus timestamp in the UI.
10. Keep the DEMO pipeline available even if the source is unreachable.

## Recommended integration order

1. Weather / warnings feed after IMD access is verified.
2. NDMA SACHET alert context.
3. CWC flood advisory/forecast context for a flood-focused pilot.
4. State SDMA shelter data where a stable downloadable inventory is available.
5. Additional satellite/GSI products as static or periodically refreshed GIS layers.

## Secrets

Do not commit API keys, access tokens or restricted endpoints. Store secrets in environment variables or Streamlit secrets for the demo machine.

## Cache policy

- Small JSON responses may be stored under `data/cache/` locally.
- Large cache files should normally remain ignored by Git and be regenerated/preloaded on the demo laptops.
- The demo runbook must state exactly how to regenerate every required cache.
