from pathlib import Path

import pandas as pd
import streamlit as st

from src.pilot_readiness import pilot_readiness
from src.ui_theme import (
    inject_global_css,
    render_data_mode_indicator,
    render_disclaimer,
    render_page_header,
)

st.set_page_config(page_title="Odisha Pilot Status", layout="wide")
inject_global_css()
render_page_header(
    "Odisha Pilot Status",
    "Authoritative-data readiness for the Puri pilot, kept separate from the working offline demonstration.",
)
render_data_mode_indicator("CACHED")

st.info(
    "The operational pages remain available in DEMO mode. This page shows which authoritative "
    "Puri inputs are verified and which fields are still blocking a full real-data run."
)

manifest_path = Path("data/pilot/source_manifest.csv")
processed_habitations = Path("data/pilot/processed/habitations.csv")
processed_shelters = Path("data/pilot/processed/shelters.csv")

left, right = st.columns([1.15, 1], gap="large")

with left:
    st.subheader("Pilot scope")
    st.markdown(
        """
        - **State:** Odisha
        - **Initial district:** Puri
        - **Population baseline:** Census of India 2011 PCA, explicitly historical
        - **Child proxy:** Census population age 0–6 only, labelled as such
        - **Shelters:** OSDMA / Puri DDMP MCS and MFS inventory
        - **Hazard layer:** authoritative machine-readable layer required before real GIS scoring
        """
    )

    st.subheader("Demo-safe architecture")
    st.markdown(
        """
        The system does not replace missing authoritative values with fabricated numbers.
        Until all operational fields are verified, the existing synthetic dataset remains the
        clearly labelled **DEMO** path for the live presentation.
        """
    )

with right:
    st.subheader("Readiness gate")
    if processed_habitations.exists() and processed_shelters.exists():
        try:
            habitations = pd.read_csv(processed_habitations)
            shelters = pd.read_csv(processed_shelters)
            report = pilot_readiness(habitations, shelters)
            hc1, hc2 = st.columns(2)
            hc1.metric(
                "Habitation readiness",
                f"{report['habitations']['readiness_percent']:.1f}%",
                f"{report['habitations']['ready_rows']}/{report['habitations']['total_rows']} rows",
            )
            hc2.metric(
                "Shelter readiness",
                f"{report['shelters']['readiness_percent']:.1f}%",
                f"{report['shelters']['ready_rows']}/{report['shelters']['total_rows']} rows",
            )
            if report["operational_ready"]:
                st.success("Authoritative Puri operational bundle is ready for integration.")
            else:
                st.warning("Processed files exist but still fail the operational-readiness gate.")
                st.json(report)
        except Exception as exc:
            st.error(f"Processed pilot files could not be validated: {exc}")
    else:
        st.warning("Authoritative processed Puri bundle has not been created yet.")
        st.caption(
            "This is expected until village demographics, verified coordinates, shelter operational "
            "details and an authoritative hazard layer are complete."
        )

st.divider()
st.subheader("Authoritative source register")
if manifest_path.exists():
    try:
        manifest = pd.read_csv(manifest_path)
        display_columns = [
            column
            for column in [
                "category",
                "source_name",
                "authority",
                "source_year",
                "coverage",
                "intended_use",
                "data_mode_default",
            ]
            if column in manifest.columns
        ]
        st.dataframe(manifest[display_columns], width="stretch", hide_index=True)
    except Exception as exc:
        st.error(f"Unable to read pilot source manifest: {exc}")
else:
    st.error("Pilot source manifest is missing.")

st.divider()
st.subheader("Remaining real-data blockers")
st.markdown(
    """
    1. Verified village-level elderly population source or explicitly documented approved derivation.
    2. Verified WGS84 coordinates for Puri villages and shelters.
    3. Complete shelter operational details where actually published, including capacity/occupancy status.
    4. Exact authoritative machine-readable flood/cyclone hazard layer and documented source-class scoring.
    5. End-to-end real Puri smoke test through GIS exposure, risk, shelter capacity and relocation.
    """
)

st.success(
    "Presentation status: the offline end-to-end DEMO path remains available while the authoritative "
    "pilot is completed behind a strict no-fabrication gate."
)

render_disclaimer()
