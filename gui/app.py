"""PintMe — Streamlit GUI."""
import base64
import os

import requests
import streamlit as st

SEARCH_API = os.environ.get("SEARCH_API", "http://localhost:8200")
N_RESULTS  = 12
COLS       = 4

st.set_page_config(page_title="PintMe", layout="wide")
st.title("📌 PintMe")


# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------

if "results" not in st.session_state:
    st.session_state.results = None
if "error" not in st.session_state:
    st.session_state.error = None


# ---------------------------------------------------------------------------
# Search helpers
# ---------------------------------------------------------------------------

def search_text(query: str) -> None:
    try:
        r = requests.post(
            f"{SEARCH_API}/search/text",
            json={"query": query, "n_results": N_RESULTS},
            timeout=30,
        )
        r.raise_for_status()
        st.session_state.results = r.json()["results"]
        st.session_state.error   = None
    except Exception as e:
        st.session_state.error   = str(e)
        st.session_state.results = None


def search_image(image_bytes: bytes) -> None:
    try:
        b64 = base64.b64encode(image_bytes).decode()
        r = requests.post(
            f"{SEARCH_API}/search/image",
            json={"input": b64, "n_results": N_RESULTS},
            timeout=30,
        )
        r.raise_for_status()
        st.session_state.results = r.json()["results"]
        st.session_state.error   = None
    except Exception as e:
        st.session_state.error   = str(e)
        st.session_state.results = None


# ---------------------------------------------------------------------------
# Search bar
# ---------------------------------------------------------------------------

col_text, col_upload = st.columns([3, 2])

with col_text:
    with st.form("text_search", clear_on_submit=False):
        query    = st.text_input("Search by description", placeholder="a deer in a forest…")
        text_btn = st.form_submit_button("Search", use_container_width=True)
    if text_btn and query:
        with st.spinner("Searching…"):
            search_text(query)

with col_upload:
    uploaded = st.file_uploader("Find visually similar", type=["jpg", "jpeg", "png", "webp"])
    if uploaded:
        with st.spinner("Searching…"):
            search_image(uploaded.read())

st.divider()


# ---------------------------------------------------------------------------
# Display results
# ---------------------------------------------------------------------------

if st.session_state.error:
    st.error(f"Search failed: {st.session_state.error}")

elif st.session_state.results is not None:
    results = st.session_state.results
    if not results:
        st.info("No results found.")
    else:
        st.caption(f"{len(results)} result(s)")
        for row_start in range(0, len(results), COLS):
            cols = st.columns(COLS)
            for col, result in zip(cols, results[row_start:row_start + COLS]):
                with col:
                    st.image(f"{SEARCH_API}/image/{result['hash']}", width="stretch")
                    fname = result["path"].split("/")[-1]
                    dims  = f"{result['width']}×{result['height']}" if result.get("width") else ""
                    st.caption(f"**{fname}**  \ndist={result['distance']:.3f}  {dims}")
                    if result.get("caption"):
                        with st.expander("Caption"):
                            st.write(result["caption"])
