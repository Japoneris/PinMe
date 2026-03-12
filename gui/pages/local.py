"""PinMe — Local image search page."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import streamlit as st
from shared import init_state, do_text_search, do_image_search, render_search_panel, render_results

SEARCH_API = os.environ.get("SEARCH_API", "http://localhost:8200")
PREFIX = "local"

st.title("📌 Local")
init_state(PREFIX)


def render_card(result):
    img_url  = f"{SEARCH_API}/image/{result['hash']}"
    file_url = f"file://{result['path']}"
    st.image(img_url, width="stretch")
    fname = result["path"].split("/")[-1]
    dims  = f"{result['width']}×{result['height']}" if result.get("width") else ""
    st.caption(f"[**{fname}**](<{file_url}>)  \ndist={result['distance']:.3f}  \n{dims}")
    if result.get("caption"):
        with st.expander("Caption"):
            st.write(result["caption"])
    if st.button("🔍 Search similar", key=f"local_{result['hash']}", use_container_width=True):
        resp = requests.get(img_url, timeout=10)
        if resp.ok:
            st.session_state[f"{PREFIX}_ref_image"]    = resp.content
            st.session_state[f"{PREFIX}_uploader_key"] += 1
            do_image_search(resp.content, f"{SEARCH_API}/search/image", PREFIX)
            st.rerun()


text_btn, img_btn, query = render_search_panel(PREFIX, placeholder="a deer in a forest…")

if text_btn and query:
    with st.spinner("Searching…"):
        do_text_search(query, f"{SEARCH_API}/search/text", PREFIX)

if img_btn and st.session_state[f"{PREFIX}_ref_image"]:
    with st.spinner("Searching…"):
        do_image_search(st.session_state[f"{PREFIX}_ref_image"], f"{SEARCH_API}/search/image", PREFIX)

st.divider()
render_results(PREFIX, render_card)
