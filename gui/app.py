"""PinMe — entry point."""
import streamlit as st

st.set_page_config(page_title="PinMe", layout="wide")

# ---------------------------------------------------------------------------
# Shared sidebar — values stored in session state, read by page scripts
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Settings")
    st.slider("Columns", min_value=1, max_value=8, value=4, key="cols")
    st.slider("Rows",    min_value=1, max_value=20, value=5, key="rows")
    st.divider()
    st.subheader("Diversity")
    st.toggle("Remove near-duplicates", value=False, key="diversity_on")
    st.slider(
        "Exclusion distance",
        min_value=0.01, max_value=1.0, value=0.15, step=0.01,
        key="excl_d",
        disabled=not st.session_state.get("diversity_on", False),
        help="Images closer than this distance to an already-kept result are excluded.",
    )
    st.divider()
    st.subheader("Dimensions")
    st.slider("Width (px)",  min_value=0, max_value=4096, value=(0, 4096), step=32, key="dim_width_range")
    st.slider("Height (px)", min_value=0, max_value=4096, value=(0, 4096), step=32, key="dim_height_range")

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

pg = st.navigation([
    st.Page("pages/local.py", title="Local", icon="📌"),
    st.Page("pages/web.py",   title="Web",   icon="🌐"),
])
pg.run()
