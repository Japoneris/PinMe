"""Shared search logic and UI components for PinMe pages."""
import base64

import numpy as np
import requests
import streamlit as st

OVERSAMPLE = 4


# ---------------------------------------------------------------------------
# Diversity filter
# ---------------------------------------------------------------------------

def _cosine_dist(a: list, b: list) -> float:
    a, b = np.array(a, dtype=np.float32), np.array(b, dtype=np.float32)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(1.0 - np.dot(a, b) / denom) if denom > 0 else 0.0


def apply_diversity(results: list, d: float, n_keep: int) -> list:
    kept = []
    for candidate in results:
        emb = candidate.get("embedding")
        if emb is None or all(_cosine_dist(emb, k["embedding"]) > d for k in kept):
            kept.append(candidate)
        if len(kept) >= n_keep:
            break
    return kept


# ---------------------------------------------------------------------------
# Settings helpers
# ---------------------------------------------------------------------------

def _settings() -> dict:
    """Read shared display/diversity settings from session state."""
    cols         = st.session_state.get("cols", 4)
    rows         = st.session_state.get("rows", 5)
    diversity_on = st.session_state.get("diversity_on", False)
    return {
        "cols":         cols,
        "n_results":    cols * rows,
        "diversity_on": diversity_on,
        "excl_d":       st.session_state.get("excl_d", 0.15),
    }


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def init_state(prefix: str) -> None:
    for key, default in [("results", None), ("error", None), ("ref_image", None), ("uploader_key", 0)]:
        if f"{prefix}_{key}" not in st.session_state:
            st.session_state[f"{prefix}_{key}"] = default


# ---------------------------------------------------------------------------
# Search functions
# ---------------------------------------------------------------------------

def do_text_search(query: str, endpoint: str, prefix: str) -> None:
    s = _settings()
    n = s["n_results"] * OVERSAMPLE if s["diversity_on"] else s["n_results"]
    try:
        r = requests.post(
            endpoint,
            json={"query": query, "n_results": n, "include_embeddings": s["diversity_on"]},
            timeout=30,
        )
        r.raise_for_status()
        results = r.json()["results"]
        if s["diversity_on"]:
            results = apply_diversity(results, s["excl_d"], s["n_results"])
        st.session_state[f"{prefix}_results"]   = results
        st.session_state[f"{prefix}_error"]     = None
        st.session_state[f"{prefix}_ref_image"] = None
    except Exception as e:
        st.session_state[f"{prefix}_error"]     = str(e)
        st.session_state[f"{prefix}_results"]   = None
        st.session_state[f"{prefix}_ref_image"] = None


def do_image_search(image_bytes: bytes, endpoint: str, prefix: str) -> None:
    s = _settings()
    n = s["n_results"] * OVERSAMPLE if s["diversity_on"] else s["n_results"]
    try:
        b64 = base64.b64encode(image_bytes).decode()
        r = requests.post(
            endpoint,
            json={"input": b64, "n_results": n + 1, "include_embeddings": s["diversity_on"]},
            timeout=30,
        )
        r.raise_for_status()
        results = r.json()["results"][1:]   # skip self
        if s["diversity_on"]:
            results = apply_diversity(results, s["excl_d"], s["n_results"])
        else:
            results = results[:s["n_results"]]
        st.session_state[f"{prefix}_results"]   = results
        st.session_state[f"{prefix}_error"]     = None
        st.session_state[f"{prefix}_ref_image"] = image_bytes
    except Exception as e:
        st.session_state[f"{prefix}_error"]     = str(e)
        st.session_state[f"{prefix}_results"]   = None
        st.session_state[f"{prefix}_ref_image"] = None


# ---------------------------------------------------------------------------
# UI components
# ---------------------------------------------------------------------------

def render_search_panel(prefix: str, placeholder: str = "search…") -> tuple[bool, bool, str]:
    """Render the search box. Returns (text_btn_clicked, img_btn_clicked, query_text)."""
    with st.container(border=True, height=250):
        col_main, col_img = st.columns([3, 1])
        with col_main:
            col_text, col_upload = st.columns([1, 1])
            with col_text:
                query = st.text_input("Search by description", placeholder=placeholder)
            with col_upload:
                uploaded = st.file_uploader(
                    "Find visually similar",
                    type=["jpg", "jpeg", "png", "webp"],
                    key=f"{prefix}_uploader_{st.session_state[f'{prefix}_uploader_key']}",
                )
                if uploaded:
                    st.session_state[f"{prefix}_ref_image"] = uploaded.read()

            btn_text, btn_img = st.columns(2)
            with btn_text:
                text_btn = st.button("Search by text",  use_container_width=True, disabled=not query)
            with btn_img:
                img_btn  = st.button("Search by image", use_container_width=True,
                                     disabled=not st.session_state[f"{prefix}_ref_image"])

        with col_img:
            if st.session_state[f"{prefix}_ref_image"]:
                st.caption("**Query image**")
                st.image(st.session_state[f"{prefix}_ref_image"])

    return text_btn, img_btn, query


def _apply_dim_filter(results: list) -> list:
    """Filter results by the shared width/height range sliders. Unknown dims pass through."""
    min_w, max_w = st.session_state.get("dim_width_range",  (0, 4096))
    min_h, max_h = st.session_state.get("dim_height_range", (0, 4096))
    if min_w == 0 and max_w == 4096 and min_h == 0 and max_h == 4096:
        return results  # sliders at defaults — skip the loop entirely
    return [
        r for r in results
        if not (r.get("width") and r.get("height"))
        or (min_w <= r["width"] <= max_w and min_h <= r["height"] <= max_h)
    ]


def render_results(prefix: str, render_card) -> None:
    """Render the results grid. render_card(result) is called inside each grid cell."""
    error   = st.session_state[f"{prefix}_error"]
    results = st.session_state[f"{prefix}_results"]
    cols    = st.session_state.get("cols", 4)

    if error:
        st.error(f"Search failed: {error}")
    elif results is not None:
        results = _apply_dim_filter(results)
        if not results:
            st.info("No results found.")
        else:
            st.caption(f"{len(results)} result(s)")
            for row_start in range(0, len(results), cols):
                grid = st.columns(cols)
                for col, result in zip(grid, results[row_start:row_start + cols]):
                    with col:
                        render_card(result)
