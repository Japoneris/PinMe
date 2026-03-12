"""PinMe — Web image search page."""
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import streamlit as st
from shared import init_state, do_text_search, do_image_search, render_search_panel, render_results

SEARCH_API = os.environ.get("SEARCH_API", "http://localhost:8200")
PREFIX = "web"

st.title("🌐 Web")
init_state(PREFIX)


def render_card(result):
    img_url   = f"{SEARCH_API}/web/image/{result['hash']}"
    page_url  = result.get("page_url", "")
    image_url = result.get("image_url", "")
    domain    = urlparse(page_url).netloc if page_url else "unknown"

    st.image(img_url, width="stretch")
    dims = f"{result['width']}×{result['height']}" if result.get("width") else ""
    if page_url:
        st.caption(f"[**{domain}**](<{page_url}>)  \ndist={result['distance']:.3f}  \n{dims}")
    else:
        st.caption(f"**{domain}**  \ndist={result['distance']:.3f}  \n{dims}")
    if image_url:
        st.caption(f"🔗 `{image_url[:60]}{'…' if len(image_url) > 60 else ''}`")
    if result.get("caption"):
        with st.expander("Caption"):
            st.write(result["caption"])
    if st.button("🔍 Search similar", key=f"web_{result['hash']}", use_container_width=True):
        resp = requests.get(img_url, timeout=10)
        if resp.ok:
            st.session_state[f"{PREFIX}_ref_image"]    = resp.content
            st.session_state[f"{PREFIX}_uploader_key"] += 1
            do_image_search(resp.content, f"{SEARCH_API}/web/search/image", PREFIX)
            st.rerun()


text_btn, img_btn, query = render_search_panel(PREFIX, placeholder="a cat on a couch…")

if text_btn and query:
    with st.spinner("Searching…"):
        do_text_search(query, f"{SEARCH_API}/web/search/text", PREFIX)

if img_btn and st.session_state[f"{PREFIX}_ref_image"]:
    with st.spinner("Searching…"):
        do_image_search(st.session_state[f"{PREFIX}_ref_image"], f"{SEARCH_API}/web/search/image", PREFIX)

st.divider()
render_results(PREFIX, render_card)
