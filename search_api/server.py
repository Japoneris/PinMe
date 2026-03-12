"""PintMe Search API — search images by text or image similarity (local + web)."""
import mimetypes
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from indexer.db import get_session
from rag.chroma import get_client, get_image_collection, get_text_collection, get_web_image_collection, get_web_text_collection
from schemas import TextSearchRequest, ImageSearchRequest, SearchResponse, WebSearchResponse
from searcher import search_by_text, search_by_image
from web_searcher import search_by_text as web_search_by_text, search_by_image as web_search_by_image
from models import Image

ROOT = Path(__file__).parent.parent
FIREFOX_DIR = ROOT / "Firefox_pinner"

EMBED_SERVER       = os.environ.get("EMBED_SERVER",         "http://localhost:8100")
DB_PATH            = os.environ.get("DB_PATH",              str(ROOT / "pintme.db"))
CHROMA_DIR         = os.environ.get("CHROMA_DIR",           str(ROOT / "chromadb"))
FIREFOX_IMAGES_DIR = os.environ.get("FIREFOX_IMAGES_DIR",   str(FIREFOX_DIR / "images"))


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.session        = get_session(DB_PATH)
    chroma                   = get_client(CHROMA_DIR)
    app.state.image_col      = get_image_collection(chroma)
    app.state.text_col       = get_text_collection(chroma)
    app.state.web_image_col  = get_web_image_collection(chroma)
    app.state.web_text_col   = get_web_text_collection(chroma)
    print(f"DB:           {DB_PATH}")
    print(f"Chroma:       {CHROMA_DIR}")
    print(f"Embed:        {EMBED_SERVER}")
    print(f"Web images:   {FIREFOX_IMAGES_DIR}")
    yield
    app.state.session.close()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="PintMe Search API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Shared routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Local routes
# ---------------------------------------------------------------------------

@app.get("/image/{hash}")
async def serve_image(hash: str):
    """Serve a local image file by its SHA-256 hash."""
    img = app.state.session.query(Image).filter_by(hash=hash).first()
    if img is None:
        raise HTTPException(404, detail="Image not found")
    path = Path(img.path)
    if not path.exists():
        raise HTTPException(404, detail=f"File not found on disk: {img.path}")
    return FileResponse(path, media_type=img.mimetype or "image/jpeg")


@app.post("/search/text", response_model=SearchResponse)
async def text_search(request: TextSearchRequest):
    """Search local images by a text description."""
    try:
        return search_by_text(
            query=request.query,
            n_results=request.n_results,
            session=app.state.session,
            text_col=app.state.text_col,
            server=EMBED_SERVER,
            include_embeddings=request.include_embeddings,
        )
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/search/image", response_model=SearchResponse)
async def image_search(request: ImageSearchRequest):
    """Search local images by visual similarity."""
    try:
        return search_by_image(
            input_data=request.input,
            n_results=request.n_results,
            session=app.state.session,
            image_col=app.state.image_col,
            server=EMBED_SERVER,
            include_embeddings=request.include_embeddings,
        )
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ---------------------------------------------------------------------------
# Web routes
# ---------------------------------------------------------------------------

@app.get("/web/image/{hash}")
async def serve_web_image(hash: str):
    """Serve a web-captured image by its SHA-256 hash."""
    images_path = Path(FIREFOX_IMAGES_DIR)
    matches = list(images_path.glob(f"{hash}.*"))
    if not matches:
        raise HTTPException(404, detail=f"Web image not found: {hash}")
    path = matches[0]
    mime = mimetypes.guess_type(str(path))[0] or "image/jpeg"
    return FileResponse(path, media_type=mime)


@app.post("/web/search/text", response_model=WebSearchResponse)
async def web_text_search(request: TextSearchRequest):
    """Search web-captured images by a text description."""
    try:
        return web_search_by_text(
            query=request.query,
            n_results=request.n_results,
            text_col=app.state.web_text_col,
            server=EMBED_SERVER,
            include_embeddings=request.include_embeddings,
        )
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/web/search/image", response_model=WebSearchResponse)
async def web_image_search(request: ImageSearchRequest):
    """Search web-captured images by visual similarity."""
    try:
        return web_search_by_image(
            input_data=request.input,
            n_results=request.n_results,
            image_col=app.state.web_image_col,
            server=EMBED_SERVER,
            include_embeddings=request.include_embeddings,
        )
    except Exception as e:
        raise HTTPException(500, detail=str(e))
