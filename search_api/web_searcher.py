"""Search logic for web-captured images: query ChromaDB, build results from metadata."""
import requests
from schemas import WebSearchResult, WebSearchResponse


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


def _build_results(chroma_result: dict, include_embeddings: bool = False) -> list[WebSearchResult]:
    ids        = chroma_result["ids"][0]
    distances  = chroma_result["distances"][0]
    metadatas  = chroma_result["metadatas"][0]
    embeddings = chroma_result["embeddings"][0] if include_embeddings else [None] * len(ids)

    results = []
    for rank, (hash_, distance, meta, embedding) in enumerate(
        zip(ids, distances, metadatas, embeddings), start=1
    ):
        results.append(WebSearchResult(
            rank=rank,
            distance=round(distance, 6),
            hash=hash_,
            path=meta.get("path", ""),
            image_url=meta.get("image_url", ""),
            page_url=meta.get("page_url", ""),
            width=meta.get("width") or None,
            height=meta.get("height") or None,
            caption=meta.get("caption"),
            embedding=embedding,
        ))
    return results


def search_by_text(
    query: str,
    n_results: int,
    text_col,
    server: str,
    include_embeddings: bool = False,
) -> WebSearchResponse:
    embedding = _embed_text(query, server)
    include = ["distances", "metadatas", "embeddings"] if include_embeddings else ["distances", "metadatas"]
    result = text_col.query(query_embeddings=[embedding], n_results=n_results, include=include)
    return WebSearchResponse(
        query_type="text",
        query=query,
        results=_build_results(result, include_embeddings),
    )


def search_by_image(
    input_data: str,
    n_results: int,
    image_col,
    server: str,
    include_embeddings: bool = False,
) -> WebSearchResponse:
    embedding = _embed_image(input_data, server)
    include = ["distances", "metadatas", "embeddings"] if include_embeddings else ["distances", "metadatas"]
    result = image_col.query(query_embeddings=[embedding], n_results=n_results, include=include)
    return WebSearchResponse(
        query_type="image",
        query=input_data if len(input_data) < 200 else input_data[:80] + "...",
        results=_build_results(result, include_embeddings),
    )
