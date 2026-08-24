import streamlit as st
from src.ui_theme import render_disclaimer

st.title("Methodology")
st.markdown("""
### Risk model
`Risk = 0.35H + 0.25E + 0.25V + 0.15A`, with all factors normalized to 0–100.

### Classes
- LOW: 0–29
- MODERATE: 30–49
- HIGH: 50–69
- CRITICAL: 70–100

### Carrying capacity
Effective capacity uses the most limiting available resource where space, water, sanitation and access data exist.

### Routing
Straight-line distance is the offline fallback. Member 4 will replace it with cached OSMnx/NetworkX routing.
""")
render_disclaimer()
