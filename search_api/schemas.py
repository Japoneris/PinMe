"""Pydantic schemas for the search API."""
from typing import Optional
from pydantic import BaseModel


class TextSearchRequest(BaseModel):
    query: str
    n_results: int = 10


class ImageSearchRequest(BaseModel):
    input: str          # local path, URL, data URL, or raw base64
    n_results: int = 10


class SearchResult(BaseModel):
    rank: int
    distance: float     # cosine distance — lower is more similar
    hash: str
    path: str
    mimetype: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size_bytes: Optional[int] = None
    caption: Optional[str] = None


class SearchResponse(BaseModel):
    query_type: str     # "text" or "image"
    query: str          # the original query string / image path
    results: list[SearchResult]
