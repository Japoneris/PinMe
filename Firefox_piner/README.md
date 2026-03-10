# pintest

Automatically capture and store every image you see while browsing the web with Firefox.

Each image is saved once to disk (content-addressed by SHA-256 hash) and every occurrence on any page is recorded in a SQLite database.

---

## How it works

```
Firefox (extension)
    │
    │  onCompleted event (type=image)
    │  re-fetch image bytes (from browser cache)
    │  POST { image_data (base64), image_url, page_url, mimetype }
    ▼
Local server (FastAPI, port 8765)
    │
    ├── images/<sha256>.<ext>   ← written once per unique image
    └── pintest.db              ← one sighting row per (image, page) occurrence
```

The browser extension listens for completed image requests. For each one it re-fetches the image (served from the browser cache, so no extra network traffic), then POSTs the binary data along with the image URL and the page URL to the local Python server. The server hashes the content, writes the file to disk if it does not already exist, and inserts a row into the SQLite database.

---

## Project structure

```
pintest/
├── README.md
├── pintest.db              ← created automatically on first server run
├── images/                 ← captured image files (<hash>.<ext>)
├── extension/
│   ├── manifest.json       ← Firefox extension manifest (Manifest V2)
│   └── background.js       ← intercepts image requests, POSTs to server
└── server/
    ├── server.py           ← FastAPI server
    └── requirements.txt
```

---

## Requirements

- Firefox (any recent version)
- Python 3.9+

---

## Setup

### 1. Install Python dependencies

```bash
cd server
pip install -r requirements.txt
```

### 2. Start the server

```bash
python server/server.py
```

The server listens on `http://127.0.0.1:8765`. The `images/` directory and `pintest.db` are created automatically on first run.

### 3. Load the extension in Firefox

1. Open Firefox and navigate to `about:debugging`
2. Click **This Firefox** in the left sidebar
3. Click **Load Temporary Add-on...**
4. Select `extension/manifest.json`

The extension is now active. It will remain loaded until Firefox is closed or it is manually removed. To make it persistent across Firefox restarts, see [Permanent installation](#permanent-installation) below.

---

## Configuration

### Server port

The port is defined at the top of `server/server.py`:

```python
PORT = 8765
```

If you change it, update the matching line in `extension/background.js`:

```javascript
const SERVER_URL = "http://localhost:8765/image";
```

### Storage paths

Also at the top of `server/server.py`:

```python
DB_PATH    = "../pintest.db"   # SQLite database
IMAGES_DIR = "../images"       # image files
```

Change these to any absolute paths you prefer.

---

## Database schema

**Table: `sightings`**

| column      | type    | description                                      |
|-------------|---------|--------------------------------------------------|
| `id`        | INTEGER | auto-increment primary key                       |
| `hash`      | TEXT    | SHA-256 of the image bytes (= filename stem)     |
| `ext`       | TEXT    | file extension (`.jpg`, `.png`, …)               |
| `image_url` | TEXT    | URL of the image resource                        |
| `page_url`  | TEXT    | URL of the page where the image appeared         |
| `mimetype`  | TEXT    | MIME type reported by the server                 |
| `size`      | INTEGER | image size in bytes                              |
| `timestamp` | TEXT    | UTC timestamp in ISO-8601 format                 |

The same image (same hash) can appear in multiple rows if it was seen on different pages. The file on disk is written only once.

Example query — find all pages where a specific image appeared:

```sql
SELECT page_url, timestamp FROM sightings WHERE hash = '<sha256>';
```

Example query — largest images collected:

```sql
SELECT hash, ext, size, image_url FROM sightings
GROUP BY hash
ORDER BY size DESC
LIMIT 20;
```

---

## Permanent installation

Temporary add-ons loaded via `about:debugging` are removed when Firefox closes. To install permanently you have two options:

**Option A — Firefox Developer Edition / Nightly (no signing required)**

1. Open `about:config` and set `xpinstall.signatures.required` to `false`
2. Package the extension: `zip -j extension.xpi extension/*`
3. Open `about:addons` → gear icon → *Install Add-on From File* → select `extension.xpi`

**Option B — Firefox ESR with policies (enterprise)**

Deploy via [enterprise policies](https://mozilla.github.io/policy-templates/) using `ExtensionSettings` to point to a local XPI file.

---

## Notes

- **Authenticated images**: because the extension fetches images from within the browser, session cookies are included automatically. Images behind a login (social media, private galleries, etc.) are captured correctly.
- **Deduplication**: identical image content is stored as a single file regardless of how many URLs or pages serve it. The database records every occurrence.
- **Filtering**: no filtering is applied at capture time. Post-processing can be done with SQL queries on the `sightings` table (filter by `size`, `mimetype`, `page_url`, etc.).
- **Privacy**: everything stays local. The server only listens on `127.0.0.1` and no data is sent anywhere else.
