"""Embedding pipeline: calls the embedding server and upserts vectors into ChromaDB."""
from datetime import datetime
from pathlib import Path

import requests
from sqlalchemy.orm import Session

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import Image


# ---------------------------------------------------------------------------
# Embedding server calls
# ---------------------------------------------------------------------------

def _post(url: str, payload: dict) -> dict:
    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()


def fetch_image_embedding(path: str, server: str) -> list[float]:
    data = _post(f"{server}/v1/embeddings", {"model": "dinov2-small", "input": path})
    return data["data"][0]["embedding"]


def fetch_caption(path: str, server: str) -> str:
    data = _post(f"{server}/v1/captions", {"model": "lfm2-vl-450m", "input": path})
    return data["data"][0]["text"]


def fetch_text_embedding(text: str, server: str) -> list[float]:
    data = _post(f"{server}/v1/text-embeddings", {"model": "minilm-v6", "input": text})
    return data["data"][0]["embedding"]


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def process_image_embeddings(
    session: Session,
    image_col,
    server: str,
    verbose: bool = True,
) -> dict:
    """Compute DINOv2 embeddings for all images not yet image-embedded."""
    pending = session.query(Image).filter_by(image_embedded=False).all()
    counts = {"done": 0, "errors": 0}

    for img in pending:
        try:
            embedding = fetch_image_embedding(img.path, server)
            image_col.upsert(
                ids=[img.hash],
                embeddings=[embedding],
                metadatas=[{"path": img.path}],
            )
            img.image_embedded = True
            img.updated_at = datetime.utcnow()
            session.commit()
            counts["done"] += 1
            if verbose:
                print(f"  [IMG]  {Path(img.path).name}")
        except Exception as e:
            session.rollback()
            counts["errors"] += 1
            if verbose:
                print(f"  [ERR]  {Path(img.path).name}: {e}")

    return counts


def process_text_embeddings(
    session: Session,
    text_col,
    server: str,
    verbose: bool = True,
) -> dict:
    """Compute caption + MiniLM embeddings for all images not yet text-embedded."""
    pending = session.query(Image).filter_by(text_embedded=False).all()
    counts = {"done": 0, "errors": 0}

    for img in pending:
        try:
            # Generate caption if not already stored in DB
            if not img.caption:
                if verbose:
                    print(f"  [CAP]  {Path(img.path).name} — captioning...")
                img.caption = fetch_caption(img.path, server)
                img.updated_at = datetime.utcnow()
                session.commit()   # persist caption before embedding

            embedding = fetch_text_embedding(img.caption, server)
            text_col.upsert(
                ids=[img.hash],
                embeddings=[embedding],
                metadatas=[{"path": img.path}],
            )
            img.text_embedded = True
            img.updated_at = datetime.utcnow()
            session.commit()
            counts["done"] += 1
            if verbose:
                print(f"  [TXT]  {Path(img.path).name}")
        except Exception as e:
            session.rollback()
            counts["errors"] += 1
            if verbose:
                print(f"  [ERR]  {Path(img.path).name}: {e}")

    return counts
