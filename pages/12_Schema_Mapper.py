from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from src.operational_file_ingest import read_operational_upload
from src.operational_sources import fetch_operational_preview
from src.operational_workspace import normalize_operational_habitations, normalize_operational_shelters
from src.schema_mapping import apply_field_mapping, canonical_fields, missing_canonical_fields, suggest_field_mapping
from src.ui_theme import inject_global_css, render_data_mode_indicator, render_disclaimer, render_page_header


st.set_page_config(page_title="Authority Schema Mapper", page_icon="MAP", layout="wide")
inject_global_css()
render_page_header(
    "Authority Schema Mapper",
    "Map heterogeneous government/district settlement and relocation-site fields into the validated operational contract without editing source files.",
)

st.info(
    "This tool never guesses ambiguous semantics. Suggested matches are only a starting point; the operator confirms every canonical field before activation or export."
)

kind = st.segmented_control(
    "Dataset type",
    ["Habitation / settlement", "Shelter / relocation site"],
    default="Habitation / settlement",
)
canonical_kind = "habitation" if kind.startswith("Habitation") else "shelter"
required_fields = canonical_fields(canonical_kind)

source_mode = st.segmented_control(
    "Source",
    ["Upload file", "Public HTTPS URL"],
    default="Upload file",
)

source = None
source_note = None
if source_mode == "Upload file":
    upload = st.file_uploader(
        "Upload authority dataset",
        type=["csv", "xlsx", "geojson", "json"],
        help="CSV, XLSX, or Point GeoJSON/JSON. XLSX uses the first worksheet only; Point geometry supplies latitude and longitude before mapping.",
    )
    if upload is not None:
        try:
            source = read_operational_upload(upload)
            source_note = f"Uploaded file: {upload.name}"
        except Exception as exc:
            st.error(f"Could not parse authority dataset: {exc}")
else:
    st.caption(
        "Use a public HTTPS CSV or Point GeoJSON/JSON endpoint. Private-network targets and URLs containing embedded credentials are rejected. "
        "Remote XLSX is not fetched by this text-feed adapter; download XLSX and use Upload file instead."
    )
    remote_url = st.text_input("Authority dataset HTTPS URL", placeholder="https://data.example.gov.in/settlements.csv")
    if st.button("Fetch source fields", type="primary", width="stretch", disabled=not remote_url.strip()):
        try:
            with st.spinner("Fetching authority source for schema inspection..."):
                preview = fetch_operational_preview(remote_url.strip())
            st.session_state["schema_mapper_remote_preview"] = preview
        except Exception as exc:
            st.session_state.pop("schema_mapper_remote_preview", None)
            st.error(f"Could not fetch authority source: {exc}")
    preview = st.session_state.get("schema_mapper_remote_preview")
    if preview and str(preview.get("source_url")) == remote_url.strip():
        source = preview["data"]
        source_note = f"{preview['mode']} · {preview['format']} · fetched {preview['fetched_at']}"
        render_data_mode_indicator(preview["mode"])
        if preview.get("stale"):
            st.warning("The schema preview is from a stale cache because the latest source refresh failed.")

if source is None:
    st.markdown("### Canonical contract")
    st.code("\n".join(required_fields), language="text")
    st.caption(
        "Load an authority source to review exact/common alias suggestions, confirm every required field, validate the transformed dataset, and export a canonical CSV or deployment field map."
    )
    render_disclaimer()
    st.stop()

st.markdown("### Source inspection")
c1, c2, c3 = st.columns(3)
c1.metric("Records", len(source))
c2.metric("Source fields", len(source.columns))
c3.metric("Dataset type", "Habitation" if canonical_kind == "habitation" else "Relocation site")
if source_note:
    st.caption(source_note)
with st.expander("Preview original source", expanded=False):
    st.dataframe(source.head(50).astype(str), width="stretch", hide_index=True)

suggestions = suggest_field_mapping(source, canonical_kind)
options = ["— Not mapped —", *[str(column) for column in source.columns]]

st.markdown("### Confirm field mapping")
st.caption("Each source column can be used only once. Existing canonical columns can be mapped to themselves.")
mapping: dict[str, str | None] = {}
columns = st.columns(2, gap="large")
for index, target in enumerate(required_fields):
    suggested = suggestions.get(target)
    default_index = options.index(suggested) if suggested in options else 0
    selected = columns[index % 2].selectbox(
        target,
        options,
        index=default_index,
        key=f"schema_mapper_{canonical_kind}_{target}",
        help=f"Canonical field required by the {canonical_kind} production contract.",
    )
    mapping[target] = None if selected == "— Not mapped —" else selected

selected_sources = [value for value in mapping.values() if value]
duplicates = sorted({value for value in selected_sources if selected_sources.count(value) > 1})
if duplicates:
    st.error(f"A source column cannot populate multiple canonical fields: {duplicates}")

mapped = None
validation = None
if not duplicates:
    try:
        mapped = apply_field_mapping(source, mapping, canonical_kind)
        missing = missing_canonical_fields(mapped, canonical_kind)
        if missing:
            st.warning(f"Still missing required canonical fields: {missing}")
        else:
            if canonical_kind == "habitation":
                validated, validation = normalize_operational_habitations(mapped)
            else:
                validated, validation = normalize_operational_shelters(mapped)
            mapped = validated
            st.success("Canonical schema and production validation passed.")
    except Exception as exc:
        st.error(f"Mapped dataset failed validation: {exc}")

if mapped is not None:
    st.markdown("### Canonical preview")
    preview_cols = [field for field in required_fields if field in mapped.columns]
    other_cols = [column for column in mapped.columns if column not in preview_cols]
    st.dataframe(mapped[[*preview_cols, *other_cols]].head(50).astype(str), width="stretch", hide_index=True)

    if validation:
        with st.expander("Production assessment", expanded=False):
            st.json(validation)

        st.download_button(
            "Download canonical CSV",
            data=mapped.to_csv(index=False).encode("utf-8-sig"),
            file_name=("canonical_habitations.csv" if canonical_kind == "habitation" else "canonical_relocation_sites.csv"),
            mime="text/csv",
            type="primary",
            width="stretch",
        )

        confirmed_mapping = {key: value for key, value in mapping.items() if value}
        env_name = "SIH_HABITATION_FIELD_MAP" if canonical_kind == "habitation" else "SIH_SHELTER_FIELD_MAP"
        st.markdown("### Deployment field map")
        st.caption(
            "For a recurring public HTTPS source, place this JSON value in the deployment secret/environment variable shown below. "
            "The mapping is field semantics only; it does not contain credentials."
        )
        st.code(f"{env_name}={json.dumps(confirmed_mapping, ensure_ascii=False)}", language="text")
        st.caption("Or download the canonical CSV above and activate it from Operational Data.")

render_disclaimer()
