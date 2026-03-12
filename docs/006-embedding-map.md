# 006 — Embedding Map (UMAP + Bokeh)

## Overview

`scripts/embedding_map.py` generates a self-contained HTML visualisation of all indexed images projected into 2D using UMAP.

## Usage

```bash
cd scripts
pip install -r requirements.txt

python embedding_map.py                          # defaults
python embedding_map.py --output my_map.html
python embedding_map.py --n-neighbors 30 --min-dist 0.05
python embedding_map.py --point-size 10 --thumb-size 150
```

## Arguments

| Argument | Default | Description |
|---|---|---|
| `--db` | `../pintme.db` | SQLite database path |
| `--chroma-dir` | `../chromadb` | ChromaDB directory |
| `--output` | `embedding_map.html` | Output HTML file |
| `--n-neighbors` | 15 | UMAP n_neighbors |
| `--min-dist` | 0.1 | UMAP min_dist |
| `--point-size` | 8 | Scatter point size in px |
| `--thumb-size` | 100 | Thumbnail size in px (for hover tooltip) |

## Interactivity

- **Hover** — shows a thumbnail and filename in a tooltip
- **Click** — opens the image file in the browser via `file://` URL
- Pan, zoom, box-zoom, reset, and save tools are available in the toolbar

## Data flow

1. All embeddings and their hashes are fetched from the ChromaDB image collection via `col.get(include=["embeddings"])`.
2. Hashes are joined against SQLite to retrieve absolute file paths.
3. UMAP reduces the high-dimensional embeddings to 2D.
4. A base64-encoded JPEG thumbnail is generated for each image and embedded directly in the HTML (no server required).

## Dependencies

See `scripts/requirements.txt`: `umap-learn`, `bokeh`, `numpy`, `pillow`, `sqlalchemy`, `chromadb`.
