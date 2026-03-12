# 003 — GUI Sidebar Settings

## Overview

A Streamlit sidebar exposes display and search configuration so users can adjust them without editing code.

## Controls

| Control | Default | Description |
|---|---|---|
| Columns | 4 | Number of result columns in the grid |
| Rows | 3 | Number of result rows in the grid |
| Remove near-duplicates | off | Enables diversity filtering |
| Exclusion distance | 0.15 | Cosine distance threshold for diversity |

`N_RESULTS` is derived as `COLS × ROWS` so the grid is always fully filled.

The diversity controls are described in detail in `004-diversity-filtering.md`.
