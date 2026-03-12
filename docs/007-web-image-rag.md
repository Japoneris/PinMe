# 007 — Web Image RAG System

## Overview

A second, parallel RAG pipeline for images passively captured by the Firefox extension. It is completely independent of the local-folder pipeline (`pintme.db` + `image_embeddings`/`text_embeddings`) and must never mix data with it.

---

## Architecture

```
pintest.db + Firefox_pinner/images/
        ↓
  web_rag/run.py          →  ChromaDB: web_image_embeddings
                             ChromaDB: web_text_embeddings
        ↓
  web_search_api/server.py (port 8201)
        ↓
  web_gui/app.py (port 8502)
```

---

## Key Design Decisions

### Separate ChromaDB collections
Two new collections (`web_image_embeddings`, `web_text_embeddings`) live in the same ChromaDB directory as the local collections but use distinct names. The local pipeline is completely unaffected.

### Metadata-only result enrichment
Web results carry `image_url`, `page_url`, `path`, and `caption` entirely within ChromaDB metadata. There is no SQL lookup at query time — `pintest.db` is only read during the embedding pipeline step.

### No schema changes to pintest.db
Captions are generated at embedding time and stored only in ChromaDB metadata. The Firefox extension's database remains read-only from the RAG system's perspective.

### Deduplication by hash
`pintest.db` stores one row per *sighting* (same image on multiple pages). The embedder groups by `hash` and picks the first sighting, so each image is embedded exactly once.

---

## File Map

| File | Role |
|---|---|
| `rag/chroma.py` | Added `get_web_image_collection()` and `get_web_text_collection()` |
| `web_rag/embedder.py` | Reads `pintest.db`, embeds new images into web ChromaDB collections |
| `web_rag/run.py` | CLI entry point for the embedding pipeline |
| `web_search_api/schemas.py` | `WebSearchResult` / `WebSearchResponse` Pydantic models |
| `web_search_api/searcher.py` | Query web collections; build results from ChromaDB metadata |
| `web_search_api/server.py` | FastAPI at port 8201; serves images from `Firefox_pinner/images/` |
| `web_search_api/run.py` | uvicorn launcher |
| `web_gui/app.py` | Streamlit GUI; shows `page_url` links to source websites |
| `web_gui/run.py` | Streamlit launcher on port 8502 |

---

## Startup Workflow

```bash
# 1. Embedding server (shared with local pipeline)
cd embedding_server && python run.py

# 2. Embed new web images (run whenever new images are captured)
cd web_rag && python run.py

# 3. Web search API
cd web_search_api && python run.py

# 4. Web GUI
cd web_gui && python run.py
# or directly: streamlit run web_gui/app.py --server.port 8502
```

### CLI options for web_rag/run.py

| Flag | Default | Description |
|---|---|---|
| `--db` | `Firefox_pinner/pintest.db` | pintest.db path |
| `--images-dir` | `Firefox_pinner/images/` | Directory with captured images |
| `--chroma-dir` | `chromadb/` | ChromaDB persist directory |
| `--server` | `http://localhost:8100` | Embedding server URL |
| `--skip-image` | off | Skip DINOv2 image embedding |
| `--skip-text` | off | Skip caption + MiniLM embedding |
| `--quiet` | off | Suppress per-file output |

### CLI options for web_search_api/run.py

| Flag | Default | Description |
|---|---|---|
| `--port` | 8201 | API port |
| `--embed-server` | `http://localhost:8100` | Embedding server URL |
| `--chroma-dir` | `chromadb/` | ChromaDB persist directory |
| `--firefox-images-dir` | `Firefox_pinner/images/` | Image serving directory |

---

## GUI Differences from local gui/app.py

- Title: `🌐 PinMe Web`
- Default `SEARCH_API`: `http://localhost:8201`
- Result card shows source domain linked to `page_url` (the original webpage)
- Image URL shown as secondary caption line
- No width/height/size metadata (not stored in pintest.db)
