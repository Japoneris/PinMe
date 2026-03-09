"""Core search logic: embed query, query ChromaDB, enrich with SQL metadata."""
from pathlib import Path

import requests
from sqlalchemy.orm import Session

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import Image
from schemas import SearchResult, SearchResponse


# ---------------------------------------------------------------------------
# Embedding server calls
# ---------------------------------------------------------------------------

def _embed_text(query: str, server: str) -> list[float]:
    r = requests.post(
        f"{server}/v1/text-embeddings",
        json={"model": "minilm-v6", "input": query},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["data"][0]["embedding"]


def _embed_image(input_data: str, server: str) -> list[float]:
    r = requests.post(
        f"{server}/v1/embeddings",
        json={"model": "dinov2-small", "input": input_data},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["data"][0]["embedding"]


# ---------------------------------------------------------------------------
# Result builder
# ---------------------------------------------------------------------------

def _build_results(chroma_result: dict, session: Session) -> list[SearchResult]:
    ids = chroma_result["ids"][0]
    distances = chroma_result["distances"][0]

    results = []
    for rank, (hash_, distance) in enumerate(zip(ids, distances), start=1):
        img = session.query(Image).filter_by(hash=hash_).first()
        if img is None:
            continue
        results.append(SearchResult(
            rank=rank,
            distance=round(distance, 6),
            hash=img.hash,
            path=img.path,
            mimetype=img.mimetype,
            width=img.width,
            height=img.height,
            size_bytes=img.size_bytes,
            caption=img.caption,
        ))
    return results


# ---------------------------------------------------------------------------
# Search functions
# ---------------------------------------------------------------------------

def search_by_text(query: str, n_results: int, session: Session, text_col, server: str) -> SearchResponse:
    embedding = _embed_text(query, server)
    result = text_col.query(query_embeddings=[embedding], n_results=n_results)
    return SearchResponse(
        query_type="text",
        query=query,
        results=_build_results(result, session),
    )


def search_by_image(input_data: str, n_results: int, session: Session, image_col, server: str) -> SearchResponse:
    embedding = _embed_image(input_data, server)
    result = image_col.query(query_embeddings=[embedding], n_results=n_results)
    return SearchResponse(
        query_type="image",
        query=input_data if len(input_data) < 200 else input_data[:80] + "...",
        results=_build_results(result, session),
    )
