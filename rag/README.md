# RAG Pipeline

Computes and stores embeddings for all indexed images into two ChromaDB collections. Requires the indexer to have run first and the embedding server to be up.

## Architecture

```
Image file
  ├── DINOv2          → vector (dim 384) → ChromaDB: image_embeddings
  └── LFM2-VL caption → text             → SQLite:   images.caption
                            └── MiniLM   → vector (dim 384) → ChromaDB: text_embeddings
```

Captions are stored in SQLite (not in ChromaDB) for portability. If the process is interrupted, captions already generated are not recomputed on the next run.

## ChromaDB collections

| Collection | Embedding source | Distance |
|---|---|---|
| `image_embeddings` | DINOv2-small | cosine |
| `text_embeddings` | MiniLM-v6 on caption | cosine |

Both collections use the image SHA-256 hash as the document ID, linking back to the SQL record.

## Run

```bash
pip install -r requirements.txt

python run.py                        # process all pending images
python run.py --skip-image           # only generate captions + text embeddings
python run.py --skip-text            # only generate image embeddings
python run.py --quiet                # suppress per-file output
python run.py --server http://localhost:8100
python run.py --db /path/to/pintme.db
python run.py --chroma-dir /path/to/chromadb
```

## Dependencies

- Embedding server running on `http://localhost:8100`
- SQLite DB populated by the indexer (`../pintme.db`)
- ChromaDB persisted locally (`../chromadb/`)
