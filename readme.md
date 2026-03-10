# PinMe

A local Pinterest-like image browser. Index your image folders, search by text description or visual similarity, and browse results in a web GUI — all running locally, no cloud required.

Image search done through 2 mechanisms

- image embedding (using [Dinov2-small](https://huggingface.co/facebook/dinov2-small))
- text embedding (using [MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)) + image captionning (using [LFM2-VL 450M](https://huggingface.co/LiquidAI/LFM2-VL-450M))

Small LLMs, can run in almost any laptop, even if a small GPU is highly recommanded for processing images.

## Architecture

```
config.json          ← whitelist of folders to scan
     │
     ▼
 indexer/            ← scans folders, hashes files, stores metadata
     │
     ▼
 pintme.db           ← SQLite: image metadata + captions
     │
     ▼
 rag/                ← computes embeddings, populates ChromaDB
     │               └── calls embedding_server/ for DINOv2, MiniLM, LFM2-VL
     ▼
 chromadb/           ← vector store (image_embeddings + text_embeddings)
     │
     ▼
 search_api/         ← FastAPI: /search/text  /search/image  /image/{hash}
     │
     ├── gui/        ← FastHTML web UI  (port 8300)
     └── cli/        ← command-line search + DB inspection
```

## Components

| Folder | Role | Port |
|---|---|---|
| `embedding_server/` | Inference: DINOv2, MiniLM, LFM2-VL | 8100 |
| `indexer/` | Scan folders → SQLite | — |
| `rag/` | Compute embeddings → ChromaDB | — |
| `search_api/` | Search endpoints + image serving | 8200 |
| `gui/` | FastHTML web interface | 8300 |
| `cli/` | CLI tools for search and DB inspection | — |

## Quick start

**1. Configure folders to index**

```json
// config.json
{
    "explore": ["/home/user/Images/Projects"]
}
```

**2. Start the embedding server**

```bash
cd embedding_server && python run.py
```

**3. Index your images**

```bash
cd indexer && python run.py
```

**4. Compute embeddings**

```bash
cd rag && python run.py
```

**5. Start the search API**

```bash
cd search_api && python run.py
```

**6. Start the GUI**

```bash
cd gui && python run.py
# open http://localhost:8300
```

## Storage

| File | Contents |
|---|---|
| `pintme.db` | SQLite: image metadata, captions, embedding flags |
| `chromadb/` | ChromaDB: image and text embedding vectors |
| `config.json` | List of folders to scan |

## Tech stack

- **Python 3.11+** throughout
- **FastAPI** — embedding server, search API
- **FastHTML + HTMX** — web GUI
- **SQLAlchemy + SQLite** — metadata storage
- **ChromaDB** — vector search
- **Transformers + PyTorch** — DINOv2-small, MiniLM-v6, LFM2-VL-450M
- **Pillow** — image loading and metadata
