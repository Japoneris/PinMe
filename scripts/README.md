# Scripts

Standalone analysis and utility tools for PintMe. Each script can be run independently from the `scripts/` directory.

## Setup

```bash
cd scripts
pip install -r requirements.txt
```

---

## embedding_map.py — 2-D Embedding Visualisation

Projects image or text embeddings into 2D using UMAP or t-SNE and produces a self-contained interactive HTML file.

**Hover** over a point to see a thumbnail and filename. **Click** a point to open the image in the browser.

### Usage

```bash
python embedding_map.py                                        # image embeddings, UMAP
python embedding_map.py --embedding text                       # caption embeddings, UMAP
python embedding_map.py --method tsne --n-neighbors 30         # t-SNE (better for small sets)
python embedding_map.py --embedding text --method tsne
python embedding_map.py --output my_map.html --point-size 10
```

### Arguments

| Argument | Default | Description |
|---|---|---|
| `--embedding` | `image` | Embedding type: `image` (DINOv2) or `text` (MiniLM captions) |
| `--method` | `umap` | Reduction method: `umap` or `tsne` |
| `--n-neighbors` | 50 | UMAP n_neighbors or t-SNE perplexity |
| `--min-dist` | 0.1 | UMAP min_dist (ignored for t-SNE) |
| `--db` | `../pintme.db` | SQLite database path |
| `--chroma-dir` | `../chromadb` | ChromaDB directory |
| `--output` | `embedding_map.html` | Output HTML file |
| `--thumb-size` | 100 | Thumbnail size in pixels |
| `--point-size` | 8 | Scatter point size in pixels |

### Notes

- Requires the RAG pipeline to have been run first (`rag/run.py`) to populate ChromaDB.
- Text embeddings only exist for images that have a caption — images without captions are skipped.
- t-SNE is recommended for small datasets (< ~1000 images); UMAP scales better to large ones.
