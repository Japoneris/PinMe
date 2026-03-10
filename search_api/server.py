"""PintMe Search API — search images by text or image similarity."""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from indexer.db import get_session
from rag.chroma import get_client, get_image_collection, get_text_collection
from schemas import TextSearchRequest, ImageSearchRequest, SearchResponse
from searcher import search_by_text, search_by_image
from models import Image

ROOT = Path(__file__).parent.parent

EMBED_SERVER = os.environ.get("EMBED_SERVER", "http://localhost:8100")
DB_PATH      = os.environ.get("DB_PATH",      str(ROOT / "pintme.db"))
CHROMA_DIR   = os.environ.get("CHROMA_DIR",   str(ROOT / "chromadb"))


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.session    = get_session(DB_PATH)
    chroma               = get_client(CHROMA_DIR)
    app.state.image_col  = get_image_collection(chroma)
    app.state.text_col   = get_text_collection(chroma)
    print(f"DB:     {DB_PATH}")
    print(f"Chroma: {CHROMA_DIR}")
    print(f"Embed:  {EMBED_SERVER}")
    yield
    app.state.session.close()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="PintMe Search API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


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
    """Search images by a text description."""
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
    """Search images by visual similarity. Input: local path, URL, data URL, or raw base64."""
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
