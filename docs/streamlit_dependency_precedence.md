# Streamlit Community Cloud dependency precedence

Streamlit Community Cloud uses the first supported dependency manifest it finds. In this repository both `environment.yml` and `requirements.txt` exist at the repository root, so `environment.yml` is selected before `requirements.txt`.

Operational rule:

- production dependency changes must keep `environment.yml` and `requirements.txt` aligned
- when forcing a Streamlit Cloud dependency rebuild, modify the selected `environment.yml` manifest, not only `requirements.txt`
- `folium`, `streamlit-folium`, and `plotly` are direct application dependencies and must remain explicitly present in the selected manifest
- GitHub Deployment Smoke remains the local production-environment gate; Streamlit Site Verification is the public-host gate after merge

The public app remains bound to `main` and `app.py`.
