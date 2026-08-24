# Data Layout

- `demo/` — committed demonstration data; app must work offline using this.
- `raw/` — downloaded source data; keep large/raw files out of Git when appropriate.
- `processed/` — normalized files matching frozen data contracts.
- `cache/` — cached live API responses and cached routing artifacts; generally local/runtime generated.

Every operational dataset must record source, update date/timestamp, and data mode (`LIVE`, `CACHED`, or `DEMO`).
