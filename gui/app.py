"""PinMe — Streamlit GUI."""
import base64
import os

import numpy as np
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
    COLS      = st.slider("Columns", min_value=1, max_value=8, value=4)
    ROWS      = st.slider("Rows",    min_value=1, max_value=20, value=3)
    N_RESULTS = COLS * ROWS

    st.divider()
    st.subheader("Diversity")
    diversity_on = st.toggle("Remove near-duplicates", value=False)
    excl_d = st.slider(
        "Exclusion distance",
        min_value=0.01, max_value=1.0, value=0.10, step=0.01,
        disabled=not diversity_on,
        help="Images closer than this distance to an already-kept result are excluded.",
    )
    OVERSAMPLE = 4   # fetch this many × N_RESULTS when diversity is on


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
# Diversity filter
# ---------------------------------------------------------------------------

def _cosine_dist(a: list, b: list) -> float:
    a, b = np.array(a, dtype=np.float32), np.array(b, dtype=np.float32)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(1.0 - np.dot(a, b) / denom) if denom > 0 else 0.0


def apply_diversity(results: list, d: float, n_keep: int) -> list:
    """Greedy pass: keep a result only if it is farther than d from all kept results."""
    kept = []
    for candidate in results:
        emb = candidate.get("embedding")
        if emb is None or all(_cosine_dist(emb, k["embedding"]) > d for k in kept):
            kept.append(candidate)
        if len(kept) >= n_keep:
            break
    return kept


# ---------------------------------------------------------------------------
# Search helpers
# ---------------------------------------------------------------------------

def _fetch_n() -> int:
    """How many results to request from the API (oversample when diversity is on)."""
    return N_RESULTS * OVERSAMPLE if diversity_on else N_RESULTS


def search_text(query: str) -> None:
    try:
        r = requests.post(
            f"{SEARCH_API}/search/text",
            json={"query": query, "n_results": _fetch_n(), "include_embeddings": diversity_on},
            timeout=30,
        )
        r.raise_for_status()
        results = r.json()["results"]
        if diversity_on:
            results = apply_diversity(results, excl_d, N_RESULTS)
        st.session_state.results   = results
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
            json={"input": b64, "n_results": _fetch_n() + 1, "include_embeddings": diversity_on},
            timeout=30,
        )
        r.raise_for_status()
        results = r.json()["results"][1:]  # skip self (rank 0 is the query image itself)
        if diversity_on:
            results = apply_diversity(results, excl_d, N_RESULTS)
        else:
            results = results[:N_RESULTS]
        st.session_state.results   = results
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
