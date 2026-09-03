from __future__ import annotations

import pandas as pd
import streamlit as st

from src.operational_file_ingest import read_operational_upload
from src.operational_workspace import normalize_operational_habitations, normalize_operational_shelters
from src.schema_mapping import apply_field_mapping, canonical_fields, missing_canonical_fields, suggest_field_mapping
from src.ui_theme import inject_global_css, render_disclaimer, render_page_header


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

upload = st.file_uploader(
    "Upload authority dataset",
    type=["csv", "geojson", "json"],
    help="CSV or Point GeoJSON/JSON. Point geometry supplies latitude and longitude before mapping.",
)

if upload is None:
    st.markdown("### Canonical contract")
    st.code("\n".join(required_fields), language="text")
    st.caption(
        "Once an authority file is uploaded, the page proposes exact/common alias matches, lets you override them, validates the transformed dataset and offers a canonical CSV export."
    )
    render_disclaimer()
else:
    try:
        source = read_operational_upload(upload)
    except Exception as exc:
        st.error(f"Could not parse authority dataset: {exc}")
        render_disclaimer()
        st.stop()

    st.markdown("### Source inspection")
    c1, c2, c3 = st.columns(3)
    c1.metric("Records", len(source))
    c2.metric("Source fields", len(source.columns))
    c3.metric("Dataset type", "Habitation" if canonical_kind == "habitation" else "Relocation site")
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
            st.caption("Download and activate this validated file from Operational Data, or use the same mapping in deployment field-map configuration for a live HTTPS feed.")

render_disclaimer()
