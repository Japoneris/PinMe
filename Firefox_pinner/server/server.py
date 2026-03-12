import base64
import hashlib
import logging
import mimetypes
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

import cairosvg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M",
)
logger = logging.getLogger(__name__)

PORT = 8765
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pintest.db")
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "images")

# mimetypes module returns awkward extensions for common formats; fix them.
EXT_OVERRIDES = {
    ".jpe": ".jpg",
    ".jpeg": ".jpg",
    "": ".bin",
}

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def init_db():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sightings (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                hash      TEXT    NOT NULL,
                ext       TEXT    NOT NULL,
                image_url TEXT    NOT NULL,
                page_url  TEXT,
                mimetype  TEXT,
                size      INTEGER NOT NULL,
                timestamp TEXT    NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON sightings (hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_page ON sightings (page_url)")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="pintest")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

init_db()


class ImagePayload(BaseModel):
    image_data: str   # base64-encoded bytes
    image_url:  str
    page_url:   str
    mimetype:   str


@app.post("/image")
def store_image(payload: ImagePayload):
    mimetype = payload.mimetype.split(";")[0].strip()

    # Reject anything that is not an image
    if not mimetype.startswith("image/"):
        raise HTTPException(status_code=415, detail=f"Unsupported media type: {mimetype}")

    data = base64.b64decode(payload.image_data)

    # Convert SVG to PNG so the RAG pipeline can process it
    if mimetype == "image/svg+xml":
        try:
            data = cairosvg.svg2png(bytestring=data)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"SVG conversion failed: {e}")
        mimetype = "image/png"

    content_hash = hashlib.sha256(data).hexdigest()

    # Derive file extension from (possibly updated) mimetype
    ext = mimetypes.guess_extension(mimetype) or ""
    ext = EXT_OVERRIDES.get(ext, ext)
    filename = f"{content_hash}{ext}"
    filepath = os.path.join(IMAGES_DIR, filename)

    # Write file only if not already on disk (dedup by content)
    if not os.path.exists(filepath):
        with open(filepath, "wb") as f:
            f.write(data)

    # Always insert a sighting row (same image can appear on many pages)
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO sightings
               (hash, ext, image_url, page_url, mimetype, size, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                content_hash,
                ext,
                payload.image_url,
                payload.page_url,
                mimetype,
                len(data),
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    logger.info("POST /image  %d bytes  %s", len(data), payload.image_url)
    return {"status": "ok", "hash": content_hash, "file": filename}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=PORT, reload=False)
