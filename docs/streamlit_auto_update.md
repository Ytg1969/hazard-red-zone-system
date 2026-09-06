# Streamlit Community Cloud auto-update contract

Status: **PUBLIC DEPLOYMENT CONTRACT**

The public SIH26191 demonstration deployment is expected to use Streamlit Community Cloud with these GitHub coordinates:

- repository: `Ytg1969/hazard-red-zone-system`
- branch: `main`
- entrypoint: `app.py`
- Python baseline: `3.12`

## Automatic update behavior

Streamlit Community Cloud monitors the connected GitHub repository. When a commit reaches the configured `main` branch, Community Cloud automatically refreshes the deployed application. Changes to Python/application files are normally reflected directly; dependency-file changes can trigger a fuller rebuild/redeploy.

No separate GitHub Actions deployment webhook is required for this hosting model. The repository's GitHub Actions workflows are release gates and smoke checks, not the hosting transport.

## Project release rule

Only changes that have passed the repository's Foundation Tests and Deployment Smoke gates should be merged to `main`. Because the public Streamlit app follows `main`, feature branches and unreviewed experimental branches must never be configured as the public deployment source.

The current deployment coordinates must not be changed casually. If the repository, branch, or entrypoint is renamed or moved, update the Streamlit Community Cloud app configuration and this contract together.

## What this repository can and cannot verify

This repository can enforce the intended deployment coordinates and keep `main` release-gated. It cannot inspect a user's Streamlit Community Cloud account settings from GitHub alone.

After first deployment, verify once in Streamlit Community Cloud that the app is bound to:

`Ytg1969/hazard-red-zone-system` → `main` → `app.py`

Once that binding is correct, future tested merges to `main` should propagate automatically through Community Cloud.

## Safety boundary

Automatic website refresh does not change the project's analytical contracts. LIVE external context remains additive unless calibrated; unknown values remain unknown; shelter capacity remains a hard constraint; and the frozen risk equation remains:

`Risk = 0.35H + 0.25E + 0.25V + 0.15A`
