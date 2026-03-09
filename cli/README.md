# CLI Tools

Two command-line scripts for interacting with PintMe without the GUI.

---

## `search.py` — query the search API

```bash
# Search by text
python search.py text "a deer in a forest"
python search.py text "anime girl with long hair" --n 10

# Search by image (local path, URL, or base64)
python search.py image /path/to/photo.jpg
python search.py image /path/to/photo.jpg --n 3

# Override server
python search.py --server http://localhost:8200 text "forest"
```

Output shows rank, cosine distance, file path, dimensions, and a caption preview.

---

## `db.py` — inspect the SQLite database

```bash
# List all indexed images (compact table)
python db.py list

# Full metadata for any image whose hash starts with a given prefix
python db.py lookup a4fd
python db.py lookup a4fd6487

# List tracked root folders and their scan timestamps
python db.py folders

# Override DB path
python db.py --db /path/to/pintme.db list
```

---

## Dependencies

- `search.py` — search API running on `http://localhost:8200`
- `db.py` — direct SQLite access, no server needed
