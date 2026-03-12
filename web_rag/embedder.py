"""Embedding pipeline for web-captured images (pintest.db + Firefox_pinner/images/)."""
import sqlite3
from pathlib import Path

from PIL import Image as PILImage

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from rag.embedder import fetch_image_embedding, fetch_caption, fetch_text_embedding


def _image_size(path: str) -> tuple[int, int]:
    """Return (width, height) of an image file, or (0, 0) on failure."""
    try:
        with PILImage.open(path) as img:
            return img.size
    except Exception:
        return (0, 0)


def get_unique_hashes(db_path: str) -> list[dict]:
    """Return one row per unique hash (first sighting) from pintest.db."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT hash, ext, image_url, page_url, mimetype
            FROM sightings
            GROUP BY hash
            ORDER BY MIN(id)
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def process_web_image_embeddings(
    records: list[dict],
    images_dir: str,
    image_col,
    server: str,
    verbose: bool = True,
) -> dict:
    """Compute DINOv2 embeddings for web images not yet in ChromaDB."""
    counts = {"done": 0, "skipped": 0, "errors": 0}
    images_path = Path(images_dir)

    for rec in records:
        hash_ = rec["hash"]
        ext = rec["ext"]
        path = str(images_path / f"{hash_}{ext}")

        # Skip if already embedded
        existing = image_col.get(ids=[hash_])
        if existing["ids"]:
            counts["skipped"] += 1
            continue

        if not Path(path).exists():
            if verbose:
                print(f"  [MISS] {hash_}{ext} — file not found, skipping")
            counts["errors"] += 1
            continue

        try:
            width, height = _image_size(path)
            embedding = fetch_image_embedding(path, server)
            image_col.upsert(
                ids=[hash_],
                embeddings=[embedding],
                metadatas=[{
                    "path": path,
                    "image_url": rec["image_url"] or "",
                    "page_url": rec["page_url"] or "",
                    "width": width,
                    "height": height,
                }],
            )
            counts["done"] += 1
            if verbose:
                print(f"  [IMG]  {hash_}{ext}")
        except Exception as e:
            counts["errors"] += 1
            if verbose:
                print(f"  [ERR]  {hash_}{ext}: {e}")

    return counts


def process_web_text_embeddings(
    records: list[dict],
    images_dir: str,
    text_col,
    server: str,
    verbose: bool = True,
) -> dict:
    """Compute caption + MiniLM embeddings for web images not yet in ChromaDB."""
    counts = {"done": 0, "skipped": 0, "errors": 0}
    images_path = Path(images_dir)

    for rec in records:
        hash_ = rec["hash"]
        ext = rec["ext"]
        path = str(images_path / f"{hash_}{ext}")

        # Skip if already embedded
        existing = text_col.get(ids=[hash_])
        if existing["ids"]:
            counts["skipped"] += 1
            continue

        if not Path(path).exists():
            if verbose:
                print(f"  [MISS] {hash_}{ext} — file not found, skipping")
            counts["errors"] += 1
            continue

        try:
            width, height = _image_size(path)
            caption = fetch_caption(path, server)
            embedding = fetch_text_embedding(caption, server)
            text_col.upsert(
                ids=[hash_],
                embeddings=[embedding],
                metadatas=[{
                    "path": path,
                    "image_url": rec["image_url"] or "",
                    "page_url": rec["page_url"] or "",
                    "width": width,
                    "height": height,
                    "caption": caption,
                }],
            )
            counts["done"] += 1
            if verbose:
                print(f"  [TXT]  {hash_}{ext}")
        except Exception as e:
            counts["errors"] += 1
            if verbose:
                print(f"  [ERR]  {hash_}{ext}: {e}")

    return counts
