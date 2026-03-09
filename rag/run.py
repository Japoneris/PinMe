#!/usr/bin/env python3
"""CLI entry point for the PintMe RAG embedding pipeline."""
import argparse
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from indexer.db import get_session
from chroma import get_client, get_image_collection, get_text_collection
from embedder import process_image_embeddings, process_text_embeddings

ROOT = Path(__file__).parent.parent


def main():
    parser = argparse.ArgumentParser(description="PintMe RAG embedding pipeline")
    parser.add_argument("--db", default=str(ROOT / "pintme.db"), help="SQLite DB path")
    parser.add_argument("--chroma-dir", default=str(ROOT / "chromadb"), help="ChromaDB persist directory")
    parser.add_argument("--server", default="http://localhost:8100", help="Embedding server base URL")
    parser.add_argument("--skip-image", action="store_true", help="Skip image embedding step")
    parser.add_argument("--skip-text", action="store_true", help="Skip text (caption) embedding step")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-file output")
    args = parser.parse_args()

    session = get_session(args.db)
    chroma = get_client(args.chroma_dir)
    image_col = get_image_collection(chroma)
    text_col = get_text_collection(chroma)

    verbose = not args.quiet

    if not args.skip_image:
        print("\n=== Image embeddings (DINOv2) ===")
        counts = process_image_embeddings(session, image_col, args.server, verbose)
        print(f"Done. Embedded: {counts['done']}  Errors: {counts['errors']}")

    if not args.skip_text:
        print("\n=== Text embeddings (caption → MiniLM) ===")
        counts = process_text_embeddings(session, text_col, args.server, verbose)
        print(f"Done. Embedded: {counts['done']}  Errors: {counts['errors']}")


if __name__ == "__main__":
    main()
