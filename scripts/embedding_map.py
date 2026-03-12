#!/usr/bin/env python3
"""2-D visualisation of image embeddings using UMAP or t-SNE.

Produces a self-contained HTML file. Click any point to open the
corresponding image in the browser.
"""
import argparse
import base64
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image as PilImage
import umap
from sklearn.manifold import TSNE
from bokeh.models import ColumnDataSource, HoverTool, TapTool, OpenURL
from bokeh.plotting import figure, output_file, show

sys.path.insert(0, str(Path(__file__).parent.parent))
from indexer.db import get_session
from rag.chroma import get_client, get_image_collection, get_text_collection
from models import Image

ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def thumb_b64(path: str, size: int = 100) -> str:
    """Return a base64-encoded JPEG thumbnail for inline display in tooltips."""
    try:
        with PilImage.open(path) as img:
            img = img.convert("RGB")
            img.thumbnail((size, size))
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=75)
            return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="2-D visualisation of image embeddings")
    parser.add_argument("--db",         default=str(ROOT / "pintme.db"),  help="SQLite DB path")
    parser.add_argument("--chroma-dir", default=str(ROOT / "chromadb"),   help="ChromaDB directory")
    parser.add_argument("--output",     default="embedding_map.html",     help="Output HTML file")
    parser.add_argument("--method",     choices=["umap", "tsne"], default="umap",
                                                                          help="Dimensionality reduction method (default: umap)")
    parser.add_argument("--embedding",  choices=["image", "text"], default="image",
                                                                          help="Embedding type to visualise (default: image). Text requires captions.")
    parser.add_argument("--thumb-size", type=int, default=100,            help="Thumbnail size in px (default 100)")
    parser.add_argument("--n-neighbors",type=int, default=50,             help="UMAP n_neighbors / t-SNE perplexity (default 50)")
    parser.add_argument("--min-dist",   type=float, default=0.1,          help="UMAP min_dist (default 0.1, ignored for t-SNE)")
    parser.add_argument("--point-size", type=int, default=8,              help="Scatter point size (default 8)")
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load embeddings from ChromaDB
    # ------------------------------------------------------------------
    session = get_session(args.db)
    chroma  = get_client(args.chroma_dir)

    if args.embedding == "image":
        col = get_image_collection(chroma)
    else:
        col = get_text_collection(chroma)

    result     = col.get(include=["embeddings"])
    ids        = result["ids"]
    embeddings = np.array(result["embeddings"], dtype=np.float32)

    if len(ids) == 0:
        label = "image" if args.embedding == "image" else "text (captions)"
        print(f"No {label} embeddings found in ChromaDB. Run the RAG pipeline first.")
        sys.exit(1)

    print(f"Loaded {len(ids)} {args.embedding} embeddings. Running {args.method.upper()}…")

    # ------------------------------------------------------------------
    # Dimensionality reduction
    # ------------------------------------------------------------------
    if args.method == "umap":
        reducer = umap.UMAP(
            n_neighbors=args.n_neighbors,
            min_dist=args.min_dist,
            random_state=42,
            verbose=True,
        )
    else:
        reducer = TSNE(
            n_components=2,
            perplexity=args.n_neighbors,
            random_state=42,
            verbose=1,
        )
    coords = reducer.fit_transform(embeddings)   # (N, 2)

    # ------------------------------------------------------------------
    # Build data source — skip hashes not found in SQLite
    # ------------------------------------------------------------------
    xs, ys, fnames, paths, thumbs, urls = [], [], [], [], [], []

    MISSING_THUMB = "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="  # 1×1 transparent GIF

    print("Building thumbnails…")
    total = len(ids)
    skipped = 0
    for i, hash_ in enumerate(ids, 1):
        print(f"  [{i}/{total}] {hash_[:12]}…", end="\r")
        img = session.query(Image).filter_by(hash=hash_).first()
        if img is None:
            skipped += 1
            continue
        xs.append(float(coords[i - 1, 0]))
        ys.append(float(coords[i - 1, 1]))
        fnames.append(Path(img.path).name)
        caption = img.caption or ""
        paths.append(img.path)
        thumb = thumb_b64(img.path, args.thumb_size)
        thumbs.append(thumb if thumb else MISSING_THUMB)
        urls.append(f"file://{img.path}")

    if skipped:
        print(f"\n  ({skipped} hashes had no matching DB record and were skipped)")

    print(f"\nPlotting {len(xs)} points…")

    source = ColumnDataSource(dict(
        x=xs, y=ys,
        fname=fnames,
        path=paths,
        thumb=thumbs,
        url=urls,
    ))

    # ------------------------------------------------------------------
    # Bokeh figure
    # ------------------------------------------------------------------
    hover = HoverTool(tooltips="""
        <div style="padding:4px; background:#fff; border:1px solid #ccc; border-radius:4px;">
            <img src="@thumb" style="max-height:120px; max-width:120px; display:block; margin-bottom:4px;"/><br>
            <span style="font-size:11px; color:#333;">@fname</span>
        </div>
    """)

    tap = TapTool(callback=OpenURL(url="@url"))

    p = figure(
        title=f"Image Embedding Map — {args.embedding} embeddings / {args.method.upper()}"
              f" (n_neighbors={args.n_neighbors}"
              + (f", min_dist={args.min_dist}" if args.method == "umap" else "") + ")",
        width=1400,
        height=900,
        tools=[hover, tap, "pan", "wheel_zoom", "box_zoom", "reset", "save"],
        active_scroll="wheel_zoom",
    )
    p.circle(
        "x", "y",
        source=source,
        size=args.point_size,
        alpha=0.7,
        color="steelblue",
        hover_color="orange",
        hover_alpha=1.0,
        line_color=None,
    )
    p.title.text_font_size = "14pt"
    p.axis.visible = False
    p.grid.visible = False

    output_file(args.output, title="PintMe — Embedding Map")
    show(p)
    print(f"Saved → {args.output}")


if __name__ == "__main__":
    main()
