# Search API

FastAPI service that exposes image search over the ChromaDB vector store, enriched with metadata from SQLite. This is the central hub consumed by both the GUI and the CLI.

## Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/search/text` | Search by text description |
| `POST` | `/search/image` | Search by visual similarity |
| `GET` | `/image/{hash}` | Serve a local image file by hash |

### Search by text
```bash
POST /search/text
{"query": "a deer in a forest", "n_results": 10}
```

### Search by image
```bash
POST /search/image
{"input": "/path/to/image.jpg", "n_results": 10}
# input accepts: local path, URL, data URL, or raw base64
```

### Response format
```json
{
  "query_type": "text",
  "query": "a deer in a forest",
  "results": [
    {
      "rank": 1,
      "distance": 0.347,
      "hash": "a4fd6487...",
      "path": "/home/user/Images/cerf.jpg",
      "mimetype": "image/jpeg",
      "width": 768, "height": 1365,
      "size_bytes": 252345,
      "caption": "A serene forest scene..."
    }
  ]
}
```

## Run

```bash
pip install -r requirements.txt

python run.py                                      # default: 0.0.0.0:8200
python run.py --port 8200
python run.py --embed-server http://localhost:8100
python run.py --db /path/to/pintme.db
python run.py --chroma-dir /path/to/chromadb
```

Config can also be set via environment variables: `EMBED_SERVER`, `DB_PATH`, `CHROMA_DIR`.

## Dependencies

- Embedding server running on `http://localhost:8100`
- `pintme.db` populated by the indexer and RAG pipeline
- `chromadb/` populated by the RAG pipeline
