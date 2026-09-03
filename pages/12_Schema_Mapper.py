from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from src.operational_file_ingest import read_operational_upload
from src.operational_sources import fetch_operational_preview
from src.operational_workspace import normalize_operational_habitations, normalize_operational_shelters, serialize_workspace
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
remote_preview = None
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
        "Use a public HTTPS CSV, explicit .xlsx, or Point GeoJSON/JSON endpoint. Private-network targets and URLs containing embedded credentials are rejected. "
        "XLSX uses the first worksheet only and is cached as binary data rather than being decoded as text."
    )
    remote_url = st.text_input("Authority dataset HTTPS URL", placeholder="https://data.example.gov.in/settlements.csv")
    if st.button("Fetch source fields", type="primary", width="stretch", disabled=not remote_url.strip()):
        try:
            with st.spinner("Fetching authority source for schema inspection..."):
                remote_preview = fetch_operational_preview(remote_url.strip())
            st.session_state["schema_mapper_remote_preview"] = remote_preview
        except Exception as exc:
            st.session_state.pop("schema_mapper_remote_preview", None)
            st.error(f"Could not fetch authority source: {exc}")
    remote_preview = st.session_state.get("schema_mapper_remote_preview")
    if remote_preview and str(remote_preview.get("source_url")) == remote_url.strip():
        source = remote_preview["data"]
        source_note = f"{remote_preview['mode']} · {remote_preview['format']} · fetched {remote_preview['fetched_at']}"
        render_data_mode_indicator(remote_preview["mode"])
        if remote_preview.get("stale"):
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

        staged = mapped.copy()
        if remote_preview:
            staged["data_mode"] = remote_preview["mode"]
            staged["source_fetched_at"] = remote_preview["fetched_at"]
            if "source_context" not in staged.columns:
                staged["source_context"] = remote_preview["source_url"]

        slot_key = f"schema_mapper_staged_{canonical_kind}"
        stage_label = "Stage mapped habitations" if canonical_kind == "habitation" else "Stage mapped relocation sites"
        if st.button(stage_label, width="stretch"):
            st.session_state[slot_key] = staged.to_dict(orient="records")
            st.success("Mapped dataset staged in this browser session.")

st.divider()
st.markdown("### Workspace staging")
st.caption("Map and stage each dataset separately. When both are staged, activate them together as one validated operational workspace.")
h_records = st.session_state.get("schema_mapper_staged_habitation")
s_records = st.session_state.get("schema_mapper_staged_shelter")
stage_cols = st.columns(2)
stage_cols[0].metric("Habitations", f"{len(h_records)} staged" if h_records else "Not staged")
stage_cols[1].metric("Relocation sites", f"{len(s_records)} staged" if s_records else "Not staged")

if h_records and s_records:
    workspace_label = st.text_input("Operational workspace label", placeholder="e.g. Wayanad District, Kerala", key="schema_mapper_workspace_label")
    if st.button("Activate staged operational workspace", type="primary", width="stretch"):
        try:
            staged_h, _ = normalize_operational_habitations(pd.DataFrame(h_records))
            staged_s, _ = normalize_operational_shelters(pd.DataFrame(s_records))
            st.session_state["operational_workspace"] = serialize_workspace(
                staged_h,
                staged_s,
                label=workspace_label.strip() or "Schema-mapped operational workspace",
            )
            st.success("Operational workspace activated. Red Zone Map, Risk Analysis and Relocation Planner can now use it.")
        except Exception as exc:
            st.error(f"Could not activate staged workspace: {exc}")
    st.page_link("pages/9_Operational_Data.py", label="Open Operational Data", use_container_width=True)

if h_records or s_records:
    if st.button("Clear staged schema-mapped datasets", type="secondary", width="stretch"):
        st.session_state.pop("schema_mapper_staged_habitation", None)
        st.session_state.pop("schema_mapper_staged_shelter", None)
        st.rerun()

render_disclaimer()
