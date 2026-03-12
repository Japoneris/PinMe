# 002 — GUI Search Panel Redesign

## Overview

The search panel was redesigned so that both inputs (text query and image upload) live inside a single bordered box, search is only triggered on button click, and an uploaded query image is previewed inline.

## Layout

```
┌─────────────────────────────────────────────────────────┐
│  [ Text input          ]  [ File uploader ]  [ Preview ] │
│  [ Search by text ]       [ Search by image ]            │
└─────────────────────────────────────────────────────────┘
```

- `st.container(border=True)` provides the unified box (avoids `st.form` which does not render `st.image` reliably).
- Two explicit buttons — **Search by text** and **Search by image** — replace the single ambiguous "Search" button, removing any priority conflict when both inputs are filled.
- Each button is disabled when its corresponding input is empty.

## Query Image Preview

When an image is uploaded, its bytes are stored in `st.session_state.ref_image` immediately (on upload), so the preview appears in the third column before any search is run.

When **🔍 Search similar** is clicked on a result card, the image is fetched from the search API, stored as the new `ref_image`, the file uploader is reset (by incrementing `uploader_key`), and a new image search is triggered automatically.
