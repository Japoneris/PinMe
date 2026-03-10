"""PinMe — Streamlit GUI."""
import base64
import os

import requests
import streamlit as st

SEARCH_API = os.environ.get("SEARCH_API", "http://localhost:8200")

st.set_page_config(page_title="PinMe", layout="wide")
st.title("📌 PinMe")

# ---------------------------------------------------------------------------
# Sidebar — display settings
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Settings")
    N_RESULTS = st.slider("Number of results", min_value=4, max_value=100, value=12, step=4)
    COLS      = st.slider("Columns", min_value=1, max_value=8, value=4)


# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------

if "results" not in st.session_state:
    st.session_state.results = None
if "error" not in st.session_state:
    st.session_state.error = None
if "ref_image" not in st.session_state:
    st.session_state.ref_image = None  # bytes of the uploaded query image
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0


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
        st.session_state.results   = r.json()["results"]
        st.session_state.error     = None
        st.session_state.ref_image = None
    except Exception as e:
        st.session_state.error     = str(e)
        st.session_state.results   = None
        st.session_state.ref_image = None


def search_image(image_bytes: bytes) -> None:
    try:
        b64 = base64.b64encode(image_bytes).decode()
        r = requests.post(
            f"{SEARCH_API}/search/image",
            json={"input": b64, "n_results": N_RESULTS+1},
            timeout=30,
        )
        r.raise_for_status()
        st.session_state.results   = r.json()["results"][:N_RESULTS]
        st.session_state.error     = None
        st.session_state.ref_image = image_bytes
    except Exception as e:
        st.session_state.error     = str(e)
        st.session_state.results   = None
        st.session_state.ref_image = None


# ---------------------------------------------------------------------------
# Search panel — unified box with both inputs and a single button
# ---------------------------------------------------------------------------

with st.container(border=True, height=250):
    col_main, col_img = st.columns([3, 1])
    with col_main:
        col_text, col_upload = st.columns([1, 1])

        with col_text:
            query = st.text_input(
                "Search by description",
                placeholder="a deer in a forest…",
            )
        with col_upload:
            uploaded = st.file_uploader(
                "Find visually similar",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"uploader_{st.session_state.uploader_key}",
            )
            if uploaded:
                st.session_state.ref_image = uploaded.read()

        search_btn = st.button("Search", use_container_width=True)

    with col_img:
        if st.session_state.ref_image:
            st.caption("**Query image**")
            st.image(st.session_state.ref_image)


if search_btn:
    if st.session_state.ref_image:
        with st.spinner("Searching…"):
            search_image(st.session_state.ref_image)
    elif query:
        with st.spinner("Searching…"):
            search_text(query)

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
                    img_url  = f"{SEARCH_API}/image/{result['hash']}"
                    file_url = f"file://{result['path']}"
                    st.image(img_url, width="stretch")
                    fname = result["path"].split("/")[-1]
                    dims  = f"{result['width']}×{result['height']}" if result.get("width") else ""
                    st.caption(f"[**{fname}**](<{file_url}>)  \ndist={result['distance']:.3f}  \n{dims}")
                    if result.get("caption"):
                        with st.expander("Caption"):
                            st.write(result["caption"])
                    if st.button("🔍 Search similar", key=result["hash"], use_container_width=True):
                        resp = requests.get(img_url, timeout=10)
                        if resp.ok:
                            st.session_state.ref_image = resp.content
                            st.session_state.uploader_key += 1
                            search_image(resp.content)
                            st.rerun()
