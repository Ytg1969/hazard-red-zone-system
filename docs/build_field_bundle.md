# Build a Windows Offline Field Bundle

The repository includes a GitHub Actions workflow named **Build Offline Field Bundle**. It creates a ready-to-copy Windows artifact while internet access is available in GitHub Actions.

The workflow now has two entry paths:

- **Automatic release build:** after **Deployment Smoke** completes successfully on `main`, the bundle workflow checks out the exact commit SHA from that successful smoke run and builds an `all-demo-cities` Windows bundle.
- **Manual rebuild:** **Actions → Build Offline Field Bundle → Run workflow** remains available. Manual runs may choose `puri` or `all-demo-cities`.

The automatic path is preferred for the competition release because it ties the artifact to the exact `main` commit that passed Deployment Smoke. A failed Deployment Smoke does not produce an automatic bundle.

The bundle contains:

- the tested Hazard Command source tree;
- a Windows Python 3.12 wheelhouse for `requirements.txt`;
- generated OpenStreetMap GraphML road caches for all three bundled demo cities on automatic builds;
- Puri-only or all-demo-city road caches on manual builds, according to `road_scope`;
- a strict field-preflight JSON report;
- `INSTALL_OFFLINE.ps1` for first-time offline installation into an isolated `.venv`;
- `START_OFFLINE.cmd` for strict-preflight + LAN launch on every rehearsal/demo;
- a `README_FIRST.txt` with the shortest event-day sequence;
- `BUILD_INFO.txt` recording the exact commit SHA, workflow/run, trigger type, source Deployment Smoke run when applicable, road scope and build UTC.

Python 3.12 itself is **not** embedded; install 64-bit Python 3.12 on the competition laptop before going fully offline.

## Automatic release artifact

For normal release flow:

1. Merge a change to `main` only after Foundation Tests + Deployment Smoke pass on the PR.
2. The push to `main` runs Deployment Smoke again for the merge commit.
3. When that `main` Deployment Smoke succeeds, **Build Offline Field Bundle** starts automatically on `windows-latest`.
4. The workflow checks out `github.event.workflow_run.head_sha`, not whatever happens to be the newest commit when the Windows runner starts.
5. Automatic builds use `road_scope=all-demo-cities`.
6. When it succeeds, download the `hazard-command-windows-offline-<run>` artifact and keep its `BUILD_INFO.txt` and `field_preflight.json`.
7. Extract it and copy the whole folder to both the primary and backup competition laptops.

This removes the old requirement to remember a manual workflow dispatch after every release-candidate merge.

## Manual rebuild

Use the manual path when you need to retry a transient road-download failure or intentionally create a smaller Puri-only bundle:

1. Open **Actions**.
2. Select **Build Offline Field Bundle**.
3. Choose **Run workflow**.
4. Leave `road_scope` as `puri` for a smaller bundle, or select `all-demo-cities` for Puri, Guwahati and Chennai road graphs.
5. Run the workflow.
6. Download and archive the resulting artifact together with its provenance files.

The workflow intentionally fails instead of uploading a bundle if:

- a required Windows wheel cannot be downloaded;
- the requested road graph cannot be generated;
- the Puri GraphML cannot be loaded and used to compute a real `cached_osm_graph` route between a bundled Puri habitation and a safety/capacity-qualified shelter;
- the deterministic demo or offline production gate fails during strict preflight;
- `INSTALL_OFFLINE.ps1` cannot create a clean Windows `.venv`, install entirely from the bundled wheelhouse, and pass strict field preflight.

The temporary validation `.venv` created on the GitHub runner is deleted before upload, so the downloaded artifact remains portable between Windows laptops. Each laptop creates its own local `.venv` during installation.

This means `Road-aware Puri routing: READY` proves more than file presence: the same cached-routing path used by the app successfully produced a road-network route without live OSRM.

Because road generation depends on public OpenStreetMap/Overpass services, a transient upstream failure can require a manual rebuild. Do not interpret a failed road-download run as a failure of the offline application itself.

## First-time setup on each competition laptop

After extracting the artifact, right-click `INSTALL_OFFLINE.ps1` and choose **Run with PowerShell**.

It will:

1. require Python 3.12;
2. create `hazard-red-zone-system\.venv`;
3. install dependencies using `--no-index` and only the bundled `wheelhouse`;
4. run `field_preflight.py --strict-road-cache`;
5. write `INSTALL_OK.txt` only when the strict field gate passes.

No internet is required for these steps.

If PowerShell execution policy blocks the script, open PowerShell in the bundle folder and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\INSTALL_OFFLINE.ps1
```

## Every rehearsal / demo

Double-click:

```text
START_OFFLINE.cmd
```

The launcher refuses to start if the local `.venv` is missing or strict field preflight fails. When it passes, it starts Streamlit in explicit OFFLINE/LAN mode and prints the laptop and phone URLs.

The preflight should report:

```text
Core offline workflow: PASS
Road-aware Puri routing: READY
Overall field gate: PASS
```

It also prints the validated Puri habitation → shelter sample route, distance and `cached_osm_graph` provenance.

Put the phone on the same Wi-Fi/hotspot and open the LAN URL printed by the launcher.

## Manual fallback commands

If the helper scripts cannot be used, open PowerShell in the extracted bundle root:

```powershell
py -3.12 -m venv hazard-red-zone-system\.venv
hazard-red-zone-system\.venv\Scripts\python.exe -m pip install --no-index --find-links wheelhouse -r hazard-red-zone-system\requirements.txt
cd hazard-red-zone-system
.\.venv\Scripts\python.exe scripts\field_preflight.py --strict-road-cache
.\.venv\Scripts\python.exe scripts\run_offline.py
```

## What to archive locally

GitHub Actions artifacts expire. After a successful build, keep a local copy of:

- the downloaded field-bundle artifact;
- `BUILD_INFO.txt` with the exact tested Git commit SHA and source smoke run;
- `field_preflight.json` generated by the workflow;
- any validated operational files you intend to demonstrate;
- a backup screen recording.

See `docs/competition_field_guide.md` and `docs/pre_demo_checklist.md` for the event-day sequence and jury-safe claim boundaries.
